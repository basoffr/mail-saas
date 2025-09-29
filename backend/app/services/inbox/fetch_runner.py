import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import uuid4
from loguru import logger
from .imap_client import IMAPClient
from .linker import MessageLinker
from .accounts import MailAccountService


class MailMessageStore:
    """In-memory store for mail messages (MVP implementation)"""
    
    def __init__(self):
        self.messages: Dict[str, Dict[str, Any]] = {}
        self.runs: Dict[str, Dict[str, Any]] = {}
        self._init_sample_data()
    
    def _init_sample_data(self):
        """Initialize with sample messages"""
        sample_messages = [
            {
                'id': 'msg-001',
                'account_id': 'acc-001',
                'folder': 'INBOX',
                'uid': 1001,
                'message_id': 'reply-001@gmail.com',
                'in_reply_to': 'campaign-msg-001@domain1.com',
                'references': ['campaign-msg-001@domain1.com'],
                'from_email': 'john.doe@gmail.com',
                'from_name': 'John Doe',
                'to_email': 'info@domain1.com',
                'subject': 'Re: Welkom bij onze service!',
                'snippet': 'Bedankt voor jullie bericht. Ik ben geïnteresseerd in meer informatie.',
                'raw_size': 1024,
                'received_at': datetime.utcnow() - timedelta(hours=2),
                'is_read': False,
                'linked_campaign_id': 'campaign-001',
                'linked_lead_id': 'lead-001',
                'linked_message_id': 'msg-out-001',
                'weak_link': False,
                'encoding_issue': False,
                'created_at': datetime.utcnow()
            },
            {
                'id': 'msg-002',
                'account_id': 'acc-001',
                'folder': 'INBOX',
                'uid': 1002,
                'message_id': 'reply-002@outlook.com',
                'in_reply_to': None,
                'references': None,
                'from_email': 'sarah.smith@outlook.com',
                'from_name': 'Sarah Smith',
                'to_email': 'info@domain1.com',
                'subject': 'Vraag over prijzen',
                'snippet': 'Hallo, ik heb jullie website bekeken en ben benieuwd naar de prijzen.',
                'raw_size': 512,
                'received_at': datetime.utcnow() - timedelta(hours=5),
                'is_read': True,
                'linked_campaign_id': None,
                'linked_lead_id': 'lead-002',
                'linked_message_id': None,
                'weak_link': True,
                'encoding_issue': False,
                'created_at': datetime.utcnow()
            }
        ]
        
        for msg in sample_messages:
            self.messages[msg['id']] = msg
    
    def create_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new message with unique constraint check"""
        # Check for duplicate (account_id, folder, uid)
        for existing_msg in self.messages.values():
            if (existing_msg['account_id'] == message_data['account_id'] and
                existing_msg['folder'] == message_data['folder'] and
                existing_msg['uid'] == message_data['uid']):
                logger.debug(f"Duplicate message ignored: UID {message_data['uid']}")
                return existing_msg
        
        message_id = str(uuid4())
        message_data['id'] = message_id
        message_data['created_at'] = datetime.utcnow()
        
        self.messages[message_id] = message_data
        return message_data
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all messages"""
        return list(self.messages.values())
    
    def get_by_query(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get messages by query parameters"""
        messages = list(self.messages.values())
        
        # Apply filters
        if query.get('account_id'):
            messages = [m for m in messages if m['account_id'] == query['account_id']]
        
        if query.get('campaign_id'):
            messages = [m for m in messages if m['linked_campaign_id'] == query['campaign_id']]
        
        if query.get('unread') is not None:
            messages = [m for m in messages if not m['is_read'] == query['unread']]
        
        if query.get('q'):
            search_term = query['q'].lower()
            messages = [m for m in messages if 
                       search_term in m['from_email'].lower() or
                       search_term in (m['from_name'] or '').lower() or
                       search_term in m['subject'].lower()]
        
        # Sort by received_at desc
        messages.sort(key=lambda x: x['received_at'], reverse=True)
        
        return messages
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark message as read"""
        if message_id in self.messages:
            self.messages[message_id]['is_read'] = True
            return True
        return False
    
    def create_run(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create fetch run record"""
        run_id = str(uuid4())
        run_data['id'] = run_id
        self.runs[run_id] = run_data
        return run_data
    
    def update_run(self, run_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update fetch run"""
        if run_id in self.runs:
            self.runs[run_id].update(updates)
            return self.runs[run_id]
        return None
    
    def get_runs(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get fetch runs"""
        runs = list(self.runs.values())
        if account_id:
            runs = [r for r in runs if r['account_id'] == account_id]
        
        runs.sort(key=lambda x: x['started_at'], reverse=True)
        return runs


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
        run_data = {
            'account_id': account_id,
            'started_at': datetime.utcnow(),
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
            max_uid = account.get('last_seen_uid', 0)
            
            for msg_data in new_messages:
                try:
                    # Add account info
                    msg_data['account_id'] = account_id
                    msg_data['folder'] = 'INBOX'
                    
                    # Link to campaigns/leads
                    link_result = self.message_linker.link_message(msg_data)
                    msg_data.update(link_result)
                    
                    # Store message
                    stored_msg = self.messages_store.create_message(msg_data)
                    if stored_msg['id'] == msg_data['id']:  # New message created
                        processed_count += 1
                    
                    # Track max UID
                    if msg_data['uid'] and msg_data['uid'] > max_uid:
                        max_uid = msg_data['uid']
                        
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
            
            # Update account fetch info
            self.accounts_service.store.update_fetch_info(account_id, max_uid)
            self.last_fetch_times[account_id] = datetime.utcnow()
            
            # Update run record
            self.messages_store.update_run(run_record['id'], {
                'finished_at': datetime.utcnow(),
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
                'finished_at': datetime.utcnow(),
                'error': error_msg
            })
            
            return {
                'account_id': account_id,
                'success': False,
                'error': error_msg
            }
