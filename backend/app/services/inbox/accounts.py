from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from loguru import logger
from ..inbox.imap_client import IMAPClient


class MailAccountsStore:
    """In-memory store for IMAP accounts (MVP implementation)"""
    
    def __init__(self):
        self.accounts: Dict[str, Dict[str, Any]] = {}
    
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all accounts"""
        return list(self.accounts.values())
    
    def get_active(self) -> List[Dict[str, Any]]:
        """Get only active accounts"""
        return [acc for acc in self.accounts.values() if acc['active']]
    
    def get_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get account by ID"""
        return self.accounts.get(account_id)
    
    def create(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new account"""
        account_id = str(uuid4())
        now = datetime.utcnow()
        
        account = {
            'id': account_id,
            'label': account_data['label'],
            'imap_host': account_data['imap_host'],
            'imap_port': account_data.get('imap_port', 993),
            'use_ssl': account_data.get('use_ssl', True),
            'username': account_data['username'],
            'secret_ref': account_data['secret_ref'],
            'active': account_data.get('active', True),
            'last_fetch_at': None,
            'last_seen_uid': None,
            'created_at': now,
            'updated_at': now
        }
        
        self.accounts[account_id] = account
        logger.info(f"Created IMAP account: {account['label']}")
        return account
    
    def update(self, account_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing account"""
        if account_id not in self.accounts:
            return None
        
        account = self.accounts[account_id]
        
        # Update allowed fields
        allowed_fields = ['label', 'imap_host', 'imap_port', 'use_ssl', 'username', 'secret_ref', 'active']
        for field in allowed_fields:
            if field in updates:
                account[field] = updates[field]
        
        account['updated_at'] = datetime.utcnow()
        logger.info(f"Updated IMAP account: {account['label']}")
        return account
    
    def toggle_active(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Toggle account active status"""
        if account_id not in self.accounts:
            return None
        
        account = self.accounts[account_id]
        account['active'] = not account['active']
        account['updated_at'] = datetime.utcnow()
        
        status = "activated" if account['active'] else "deactivated"
        logger.info(f"IMAP account {status}: {account['label']}")
        return account
    
    def update_fetch_info(self, account_id: str, last_seen_uid: int):
        """Update last fetch information"""
        if account_id in self.accounts:
            account = self.accounts[account_id]
            account['last_fetch_at'] = datetime.utcnow()
            account['last_seen_uid'] = last_seen_uid
            account['updated_at'] = datetime.utcnow()
    
    def mask_username(self, username: str) -> str:
        """Mask username for security"""
        if '@' in username:
            local, domain = username.split('@', 1)
            if len(local) <= 3:
                masked_local = local[0] + '*' * (len(local) - 1)
            else:
                masked_local = local[:3] + '*' * (len(local) - 3)
            return f"{masked_local}@{domain}"
        else:
            if len(username) <= 3:
                return username[0] + '*' * (len(username) - 1)
            else:
                return username[:3] + '*' * (len(username) - 3)


class MailAccountService:
    """Service for IMAP account management"""
    
    def __init__(self):
        self.store = MailAccountsStore()
    
    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts with masked usernames"""
        accounts = self.store.get_all()
        
        # Mask usernames for security
        for account in accounts:
            account['username_masked'] = self.store.mask_username(account['username'])
        
        return accounts
    
    def get_active_accounts(self) -> List[Dict[str, Any]]:
        """Get active accounts for fetching"""
        return self.store.get_active()
    
    def create_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new IMAP account"""
        return self.store.create(account_data)
    
    def update_account(self, account_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update IMAP account"""
        return self.store.update(account_id, updates)
    
    def toggle_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Toggle account active status"""
        return self.store.toggle_active(account_id)
    
    def test_account(self, account_id: str) -> Dict[str, Any]:
        """Test IMAP account connection"""
        account = self.store.get_by_id(account_id)
        if not account:
            return {'ok': False, 'message': 'Account not found'}
        
        try:
            # Get password from secret store (mock implementation)
            password = self._get_password_from_secret_store(account['secret_ref'])
            if not password:
                return {'ok': False, 'message': 'Failed to retrieve password from secret store'}
            
            # Test IMAP connection
            client = IMAPClient(
                host=account['imap_host'],
                port=account['imap_port'],
                use_ssl=account['use_ssl']
            )
            
            if not client.connect(account['username'], password):
                return {'ok': False, 'message': 'Failed to connect to IMAP server'}
            
            if not client.select_inbox():
                client.close()
                return {'ok': False, 'message': 'Failed to select INBOX folder'}
            
            client.close()
            return {'ok': True, 'message': 'Connection successful'}
            
        except Exception as e:
            logger.error(f"IMAP test failed for account {account_id}: {str(e)}")
            return {'ok': False, 'message': f'Connection failed: {str(e)}'}
    
    def _get_password_from_secret_store(self, secret_ref: str) -> Optional[str]:
        """Get password from secret store"""
        # In production, this would connect to Render Secrets, Supabase Vault, etc.
        # For MVP, passwords should be configured via environment variables
        import os
        return os.getenv(f"IMAP_PASSWORD_{secret_ref}")
