import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import uuid4
from loguru import logger
from supabase import create_client, Client
from .imap_client import IMAPClient
from .linker import MessageLinker
from .accounts import MailAccountService


class MailMessageStore:
    """Supabase-backed store for mail messages (production implementation)"""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self._init_supabase()
    
    def _init_supabase(self):
        """Initialize Supabase client"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            logger.warning("Supabase credentials not found, inbox will not be persistent")
            return
        
        try:
            self.supabase = create_client(url, key)
            logger.info("✅ Supabase-backed MailMessageStore initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase for inbox: {e}")
    
    
    def create_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new message with unique constraint check"""
        if not self.supabase:
            logger.error("Supabase not initialized, cannot store message")
            return message_data
        
        try:
            # Convert datetime to ISO string for JSON serialization
            received_at = message_data['received_at']
            if isinstance(received_at, datetime):
                received_at = received_at.isoformat()
            
            # Prepare data for Supabase (snake_case)
            db_data = {
                'account_id': message_data['account_id'],
                'folder': message_data.get('folder', 'INBOX'),
                'uid': message_data.get('uid'),
                'message_id': message_data.get('message_id'),
                'in_reply_to': message_data.get('in_reply_to'),
                'message_references': message_data.get('references', []),
                'from_email': message_data['from_email'],
                'from_name': message_data.get('from_name'),
                'to_email': message_data.get('to_email'),
                'subject': message_data['subject'],
                'snippet': message_data.get('snippet'),
                'received_at': received_at,  # ISO string now
                'linked_campaign_id': message_data.get('linked_campaign_id'),
                'linked_lead_id': message_data.get('linked_lead_id'),
                'linked_message_id': message_data.get('linked_message_id'),
                'weak_link': message_data.get('weak_link', False),
                'is_read': False
            }
            
            # Insert into Supabase (upsert to handle duplicates)
            result = self.supabase.table('inbox_messages').upsert(
                db_data,
                on_conflict='account_id,folder,uid'
            ).execute()
            
            if result.data and len(result.data) > 0:
                stored = result.data[0]
                message_data['id'] = stored.get('id', str(uuid4()))
                logger.debug(f"Message stored/updated in Supabase: UID {message_data.get('uid')}")
                return message_data
            else:
                # Duplicate found by unique constraint, generate temp ID
                logger.debug(f"Duplicate message ignored: UID {message_data.get('uid')}")
                message_data['id'] = str(uuid4())  # Ensure 'id' always exists
                return message_data
                
        except Exception as e:
            logger.error(f"Failed to store message in Supabase: {e}")
            # Ensure 'id' exists even on error
            if 'id' not in message_data:
                message_data['id'] = str(uuid4())
            return message_data
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all messages"""
        if not self.supabase:
            return []
        
        try:
            result = self.supabase.table('inbox_messages').select('*').execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Failed to get all messages: {e}")
            return []
    
    def get_by_query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get messages by query parameters"""
        if not self.supabase:
            return []
        
        try:
            # Start building query
            db_query = self.supabase.table('inbox_messages').select('*')
            
            # Apply filters
            if query.get('account_id'):
                db_query = db_query.eq('account_id', query['account_id'])
            
            if query.get('campaign_id'):
                db_query = db_query.eq('linked_campaign_id', query['campaign_id'])
            
            if query.get('unread') is not None:
                db_query = db_query.eq('is_read', not query['unread'])
            
            if query.get('q'):
                search_term = query['q']
                # Use ilike for case-insensitive search
                db_query = db_query.or_(f'from_email.ilike.%{search_term}%,from_name.ilike.%{search_term}%,subject.ilike.%{search_term}%')
            
            # Sort by received_at desc
            db_query = db_query.order('received_at', desc=True)
            
            result = db_query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to query messages: {e}")
            return []
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark message as read"""
        if not self.supabase:
            return False
        
        try:
            result = self.supabase.table('inbox_messages').update(
                {'is_read': True}
            ).eq('id', message_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to mark message as read: {e}")
            return False
    
    def create_run(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create fetch run record"""
        if not self.supabase:
            run_data['id'] = str(uuid4())
            return run_data
        
        try:
            result = self.supabase.table('inbox_fetch_runs').insert(run_data).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
            return run_data
        except Exception as e:
            logger.error(f"Failed to create run: {e}")
            return run_data
    
    def update_run(self, run_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update fetch run"""
        if not self.supabase:
            return None
        
        try:
            result = self.supabase.table('inbox_fetch_runs').update(updates).eq('id', run_id).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to update run: {e}")
            return None
    
    def get_runs(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get fetch runs"""
        if not self.supabase:
            return []
        
        try:
            db_query = self.supabase.table('inbox_fetch_runs').select('*')
            
            if account_id:
                db_query = db_query.eq('account_id', account_id)
            
            db_query = db_query.order('started_at', desc=True)
            result = db_query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get runs: {e}")
            return []


class FetchRunner:
    """Manages IMAP fetch operations with rate limiting and job tracking"""
    
    MIN_FETCH_INTERVAL = timedelta(minutes=2)  # Configurable minimum interval
    
    def __init__(self, accounts_service: MailAccountService, 
                 messages_store: MailMessageStore,
                 message_linker: MessageLinker):
        self.accounts_service = accounts_service
        self.messages_store = messages_store
        self.message_linker = message_linker
        self.last_fetch_times: Dict[str, datetime] = {}
    
    async def start_fetch_all_accounts(self) -> str:
        """Start fetch job for all active accounts"""
        run_id = str(uuid4())
        
        # Get active accounts
        active_accounts = self.accounts_service.get_active_accounts()
        
        if not active_accounts:
            logger.warning("No active IMAP accounts found")
            return run_id
        
        # Start async fetch for each account
        tasks = []
        for account in active_accounts:
            if self._can_fetch_account(account['id']):
                task = asyncio.create_task(self._fetch_account(account, run_id))
                tasks.append(task)
            else:
                logger.info(f"Skipping account {account['label']} - rate limit")
        
        if tasks:
            # Run all fetch tasks concurrently
            asyncio.create_task(self._run_fetch_tasks(tasks))
        
        return run_id
    
    def _can_fetch_account(self, account_id: str) -> bool:
        """Check if account can be fetched (rate limit guard)"""
        last_fetch = self.last_fetch_times.get(account_id)
        if not last_fetch:
            return True
        
        return datetime.utcnow() - last_fetch >= self.MIN_FETCH_INTERVAL
    
    async def _run_fetch_tasks(self, tasks: List[asyncio.Task]):
        """Run fetch tasks and handle results"""
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error in fetch tasks: {str(e)}")
    
    async def _fetch_account(self, account: Dict[str, Any], run_id: str) -> Dict[str, Any]:
        """Fetch messages for a single account"""
        account_id = account['id']
        
        # Create run record
        run_id = str(uuid4())
        run_data = {
            'id': run_id,
            'account_id': account_id,
            'started_at': datetime.utcnow().isoformat(),  # ISO string for JSON serialization
            'finished_at': None,
            'new_count': 0,
            'error': None
        }
        
        run_record = self.messages_store.create_run(run_data)
        
        try:
            logger.info(f"Starting fetch for account: {account['label']}")
            
            # Get password from secret store
            password = self.accounts_service._get_password_from_secret_store(account['secret_ref'])
            if not password:
                raise Exception("Failed to retrieve password from secret store")
            
            # Connect to IMAP
            client = IMAPClient(
                host=account['imap_host'],
                port=account['imap_port'],
                use_ssl=account['use_ssl']
            )
            
            if not client.connect(account['username'], password):
                raise Exception("Failed to connect to IMAP server")
            
            if not client.select_inbox():
                raise Exception("Failed to select INBOX folder")
            
            # Fetch new messages
            new_messages = client.fetch_new_messages(
                last_seen_uid=account.get('last_seen_uid'),
                last_fetch_date=account.get('last_fetch_at')
            )
            
            client.close()
            
            # Process and link messages
            processed_count = 0
            max_uid = account.get('last_seen_uid') or 0  # Ensure integer, never None
            
            for msg_data in new_messages:
                try:
                    # Add account info
                    msg_data['account_id'] = account_id
                    msg_data['folder'] = 'INBOX'
                    
                    # Link to campaigns/leads (before storing, so no 'id' yet)
                    link_result = self.message_linker.link_message(msg_data)
                    msg_data.update(link_result)
                    
                    # Store message (this assigns 'id' to msg_data)
                    stored_msg = self.messages_store.create_message(msg_data)
                    if stored_msg.get('id') and stored_msg.get('id') == msg_data.get('id'):
                        processed_count += 1
                    
                    # Track max UID (ensure both are integers)
                    msg_uid = msg_data.get('uid')
                    if msg_uid and isinstance(msg_uid, int) and msg_uid > max_uid:
                        max_uid = msg_uid
                        
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
            
            # Update account fetch info
            self.accounts_service.store.update_fetch_info(account_id, max_uid)
            self.last_fetch_times[account_id] = datetime.utcnow()
            
            # Update run record
            self.messages_store.update_run(run_record['id'], {
                'finished_at': datetime.utcnow().isoformat(),
                'new_count': processed_count
            })
            
            logger.info(f"Fetch completed for {account['label']}: {processed_count} new messages")
            
            return {
                'account_id': account_id,
                'success': True,
                'new_count': processed_count
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Fetch failed for account {account['label']}: {error_msg}")
            
            # Update run record with error
            self.messages_store.update_run(run_record['id'], {
                'finished_at': datetime.utcnow().isoformat(),
                'error': error_msg
            })
            
            return {
                'account_id': account_id,
                'success': False,
                'error': error_msg
            }
