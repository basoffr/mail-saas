import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.main import app
from app.services.inbox.accounts import MailAccountService
from app.services.inbox.fetch_runner import MailMessageStore
from app.services.inbox.linker import MessageLinker

client = TestClient(app)

# Mock JWT token for testing
MOCK_TOKEN = "Bearer mock_jwt_token"
MOCK_USER = {"sub": "test_user_id", "email": "test@example.com"}


@pytest.fixture
def auth_headers():
    return {"Authorization": MOCK_TOKEN}


@pytest.fixture
def mock_auth():
    with patch("app.core.auth.require_auth", return_value=MOCK_USER):
        yield


class TestInboxAPI:
    """Test inbox API endpoints"""
    
    def test_health_check(self):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_fetch_requires_auth(self):
        """Test that fetch endpoint requires authentication"""
        response = client.post("/api/v1/inbox/fetch")
        assert response.status_code == 403  # FastAPI returns 403 for missing auth
    
    def test_list_messages_requires_auth(self):
        """Test that messages endpoint requires authentication"""
        response = client.get("/api/v1/inbox/messages")
        assert response.status_code == 403  # FastAPI returns 403 for missing auth
    
    def test_mark_read_requires_auth(self):
        """Test that mark-read endpoint requires authentication"""
        response = client.post("/api/v1/inbox/messages/test-id/mark-read")
        assert response.status_code == 403  # FastAPI returns 403 for missing auth
    
    @patch("app.core.auth.require_auth", return_value=MOCK_USER)
    def test_start_fetch_ok(self, mock_auth):
        """Test successful fetch start"""
        with patch("app.services.inbox.fetch_runner.FetchRunner.start_fetch_all_accounts") as mock_fetch:
            mock_fetch.return_value = "run-123"
            
            response = client.post("/api/v1/inbox/fetch", headers={"Authorization": MOCK_TOKEN})
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["ok"] is True
            assert "run_id" in data["data"]
    
    @patch("app.core.auth.require_auth", return_value=MOCK_USER)
    def test_list_messages_ok(self, mock_auth):
        """Test successful message listing"""
        response = client.get("/api/v1/inbox/messages", headers={"Authorization": MOCK_TOKEN})
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert isinstance(data["data"]["items"], list)
    
    @patch("app.core.auth.require_auth", return_value=MOCK_USER)
    def test_list_messages_with_filters(self, mock_auth):
        """Test message listing with filters"""
        params = {
            "page": 1,
            "page_size": 10,
            "account_id": "acc-001",
            "unread": True,
            "q": "test"
        }
        
        response = client.get("/api/v1/inbox/messages", params=params, headers={"Authorization": MOCK_TOKEN})
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    @patch("app.core.auth.require_auth", return_value=MOCK_USER)
    def test_mark_message_read(self, mock_auth):
        """Test marking message as read"""
        response = client.post("/api/v1/inbox/messages/msg-001/mark-read", headers={"Authorization": MOCK_TOKEN})
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["ok"] is True
    
    @patch("app.core.auth.require_auth", return_value=MOCK_USER)
    def test_mark_nonexistent_message_read(self, mock_auth):
        """Test marking nonexistent message as read"""
        response = client.post("/api/v1/inbox/messages/nonexistent/mark-read", headers={"Authorization": MOCK_TOKEN})
        
        assert response.status_code == 404
    
    @patch("app.core.auth.require_auth", return_value=MOCK_USER)
    def test_list_runs(self, mock_auth):
        """Test listing fetch runs"""
        response = client.get("/api/v1/inbox/runs", headers={"Authorization": MOCK_TOKEN})
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["data"], list)


class TestSettingsIMAPEndpoints:
    """Test IMAP account management in settings"""
    
    @patch("app.core.auth.require_auth", return_value=MOCK_USER)
    def test_get_imap_accounts(self, mock_auth):
        """Test getting IMAP accounts"""
        response = client.get("/api/v1/settings/inbox/accounts", headers={"Authorization": MOCK_TOKEN})
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
        
        # Check that usernames are masked
        if data["data"]:
            account = data["data"][0]
            assert "username_masked" in account
            assert "*" in account["username_masked"]
    
    @patch("app.core.auth.require_auth", return_value=MOCK_USER)
    def test_create_imap_account(self, mock_auth):
        """Test creating IMAP account"""
        account_data = {
            "label": "test@example.com",
            "imap_host": "imap.example.com",
            "imap_port": 993,
            "use_ssl": True,
            "username": "test@example.com",
            "secret_ref": "secret_ref_test"
        }
        
        response = client.post("/api/v1/settings/inbox/accounts", 
                             json=account_data, 
                             headers={"Authorization": MOCK_TOKEN})
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["label"] == account_data["label"]
        assert "username_masked" in data["data"]
    
    @patch("app.core.auth.require_auth", return_value=MOCK_USER)
    def test_test_imap_account(self, mock_auth):
        """Test IMAP account connection test"""
        response = client.post("/api/v1/settings/inbox/accounts/acc-001/test", 
                             headers={"Authorization": MOCK_TOKEN})
        
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data["data"]
        assert "message" in data["data"]
    
    @patch("app.core.auth.require_auth", return_value=MOCK_USER)
    def test_toggle_imap_account(self, mock_auth):
        """Test toggling IMAP account"""
        response = client.post("/api/v1/settings/inbox/accounts/acc-001/toggle", 
                             headers={"Authorization": MOCK_TOKEN})
        
        assert response.status_code == 200
        data = response.json()
        assert "active" in data["data"]
    
    @patch("app.core.auth.require_auth", return_value=MOCK_USER)
    def test_toggle_nonexistent_account(self, mock_auth):
        """Test toggling nonexistent account"""
        response = client.post("/api/v1/settings/inbox/accounts/nonexistent/toggle", 
                             headers={"Authorization": MOCK_TOKEN})
        
        assert response.status_code == 404


class TestMessageLinker:
    """Test message linking logic"""
    
    def setup_method(self):
        """Setup test data"""
        self.mock_messages_store = MagicMock()
        self.mock_leads_store = MagicMock()
        self.mock_campaigns_store = MagicMock()
        
        self.linker = MessageLinker(
            self.mock_messages_store,
            self.mock_leads_store,
            self.mock_campaigns_store
        )
    
    def test_link_by_in_reply_to(self):
        """Test linking via In-Reply-To header"""
        # Mock outbound message
        mock_message = MagicMock()
        mock_message.id = "msg-out-001"
        mock_message.campaign_id = "campaign-001"
        mock_message.lead_id = "lead-001"
        mock_message.smtp_message_id = "test-message-id@domain.com"
        
        self.mock_messages_store.get_all.return_value = [mock_message]
        
        inbox_message = {
            'id': 'inbox-001',
            'in_reply_to': 'test-message-id@domain.com',
            'from_email': 'test@example.com',
            'subject': 'Re: Test',
            'received_at': datetime.utcnow()
        }
        
        result = self.linker.link_message(inbox_message)
        
        assert result['linked_message_id'] == 'msg-out-001'
        assert result['linked_campaign_id'] == 'campaign-001'
        assert result['linked_lead_id'] == 'lead-001'
        assert result['weak_link'] is False
    
    def test_link_by_references(self):
        """Test linking via References header"""
        mock_message = MagicMock()
        mock_message.id = "msg-out-001"
        mock_message.campaign_id = "campaign-001"
        mock_message.lead_id = "lead-001"
        mock_message.smtp_message_id = "ref-message-id@domain.com"
        
        self.mock_messages_store.get_all.return_value = [mock_message]
        
        inbox_message = {
            'id': 'inbox-001',
            'in_reply_to': None,
            'references': ['ref-message-id@domain.com', 'other-id@domain.com'],
            'from_email': 'test@example.com',
            'subject': 'Re: Test',
            'received_at': datetime.utcnow()
        }
        
        result = self.linker.link_message(inbox_message)
        
        assert result['linked_message_id'] == 'msg-out-001'
        assert result['weak_link'] is False
    
    def test_weak_link_by_email_only(self):
        """Test weak linking by email only"""
        # No matching outbound messages
        self.mock_messages_store.get_all.return_value = []
        
        # Mock lead
        mock_lead = MagicMock()
        mock_lead.id = "lead-001"
        mock_lead.email = "test@example.com"
        
        self.mock_leads_store.get_all.return_value = [mock_lead]
        
        inbox_message = {
            'id': 'inbox-001',
            'in_reply_to': None,
            'references': None,
            'from_email': 'test@example.com',
            'subject': 'New inquiry',
            'received_at': datetime.utcnow()
        }
        
        result = self.linker.link_message(inbox_message)
        
        assert result['linked_lead_id'] == 'lead-001'
        assert result['linked_campaign_id'] is None
        assert result['linked_message_id'] is None
        assert result['weak_link'] is True
    
    def test_no_link_found(self):
        """Test when no link can be established"""
        self.mock_messages_store.get_all.return_value = []
        self.mock_leads_store.get_all.return_value = []
        
        inbox_message = {
            'id': 'inbox-001',
            'in_reply_to': None,
            'references': None,
            'from_email': 'unknown@example.com',
            'subject': 'Unknown sender',
            'received_at': datetime.utcnow()
        }
        
        result = self.linker.link_message(inbox_message)
        
        assert result['linked_lead_id'] is None
        assert result['linked_campaign_id'] is None
        assert result['linked_message_id'] is None
        assert result['weak_link'] is False


class TestMailMessageStore:
    """Test mail message store functionality"""
    
    def setup_method(self):
        """Setup test store"""
        self.store = MailMessageStore()
    
    def test_create_message(self):
        """Test creating new message"""
        message_data = {
            'account_id': 'acc-test',
            'folder': 'INBOX',
            'uid': 9999,
            'from_email': 'test@example.com',
            'subject': 'Test message',
            'snippet': 'Test content',
            'received_at': datetime.utcnow()
        }
        
        result = self.store.create_message(message_data)
        
        assert result['id'] is not None
        assert result['account_id'] == 'acc-test'
        assert result['uid'] == 9999
    
    def test_duplicate_message_ignored(self):
        """Test that duplicate messages are ignored"""
        message_data = {
            'account_id': 'acc-001',
            'folder': 'INBOX',
            'uid': 1001,  # Existing UID in sample data
            'from_email': 'test@example.com',
            'subject': 'Test message',
            'snippet': 'Test content',
            'received_at': datetime.utcnow()
        }
        
        result = self.store.create_message(message_data)
        
        # Should return existing message, not create new one
        assert result['uid'] == 1001
        assert result['from_email'] != 'test@example.com'  # Should be original data
    
    def test_mark_as_read(self):
        """Test marking message as read"""
        # Use existing message from sample data
        success = self.store.mark_as_read('msg-001')
        assert success is True
        
        # Check that message is now read
        messages = self.store.get_all()
        msg = next((m for m in messages if m['id'] == 'msg-001'), None)
        assert msg is not None
        assert msg['is_read'] is True
    
    def test_mark_nonexistent_as_read(self):
        """Test marking nonexistent message as read"""
        success = self.store.mark_as_read('nonexistent')
        assert success is False
    
    def test_query_filtering(self):
        """Test message querying with filters"""
        query = {
            'account_id': 'acc-001',
            'unread': True
        }
        
        messages = self.store.get_by_query(query)
        
        # Should only return unread messages from acc-001
        for msg in messages:
            assert msg['account_id'] == 'acc-001'
            assert msg['is_read'] is False
    
    def test_search_query(self):
        """Test search functionality"""
        query = {
            'q': 'john'
        }
        
        messages = self.store.get_by_query(query)
        
        # Should find messages containing 'john' in from_email, from_name, or subject
        assert len(messages) > 0
        for msg in messages:
            search_text = f"{msg['from_email']} {msg.get('from_name', '')} {msg['subject']}".lower()
            assert 'john' in search_text
