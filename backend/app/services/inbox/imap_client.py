import imaplib
import email
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from email.header import decode_header
from loguru import logger


class IMAPClient:
    def __init__(self, host: str, port: int = 993, use_ssl: bool = True):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.connection: Optional[imaplib.IMAP4_SSL] = None
    
    def connect(self, username: str, password: str) -> bool:
        """Connect to IMAP server and authenticate"""
        try:
            if self.use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                self.connection = imaplib.IMAP4(self.host, self.port)
            
            self.connection.login(username, password)
            return True
        except Exception as e:
            logger.error(f"IMAP connection failed: {str(e)}")
            return False
    
    def select_inbox(self) -> bool:
        """Select INBOX folder"""
        try:
            if not self.connection:
                return False
            
            status, _ = self.connection.select('INBOX')
            return status == 'OK'
        except Exception as e:
            logger.error(f"Failed to select INBOX: {str(e)}")
            return False
    
    def fetch_new_messages(self, last_seen_uid: Optional[int] = None, 
                          last_fetch_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch new messages using UID strategy"""
        try:
            if not self.connection:
                return []
            
            # Strategy 1: UID > last_seen_uid (preferred)
            if last_seen_uid:
                search_criteria = f"UID {last_seen_uid + 1}:*"
            # Strategy 2: SINCE date (fallback)
            elif last_fetch_date:
                date_str = last_fetch_date.strftime("%d-%b-%Y")
                search_criteria = f"SINCE {date_str}"
            else:
                # First time fetch - get recent messages
                search_criteria = "ALL"
            
            # Search for messages
            status, message_ids = self.connection.uid('search', None, search_criteria)
            if status != 'OK':
                return []
            
            uid_list = message_ids[0].split()
            if not uid_list:
                return []
            
            # Fetch in batches of 50
            messages = []
            batch_size = 50
            
            for i in range(0, len(uid_list), batch_size):
                batch_uids = uid_list[i:i + batch_size]
                uid_range = b','.join(batch_uids).decode()
                
                # Fetch envelope + headers + text preview
                status, msg_data = self.connection.uid('fetch', uid_range, 
                    '(ENVELOPE BODY.PEEK[HEADER.FIELDS (MESSAGE-ID IN-REPLY-TO REFERENCES FROM TO SUBJECT DATE)] BODY.PEEK[TEXT]<0.20480>)')
                
                if status == 'OK':
                    messages.extend(self._parse_messages(msg_data, batch_uids))
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to fetch messages: {str(e)}")
            return []
    
    def _parse_messages(self, msg_data: List, uids: List[bytes]) -> List[Dict[str, Any]]:
        """Parse IMAP message data into structured format"""
        messages = []
        
        for i, response_part in enumerate(msg_data):
            if isinstance(response_part, tuple):
                try:
                    uid = int(uids[i // 2]) if i // 2 < len(uids) else None
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Extract headers
                    message_id = self._decode_header(msg.get('Message-ID', ''))
                    in_reply_to = self._decode_header(msg.get('In-Reply-To', ''))
                    references = self._parse_references(msg.get('References', ''))
                    from_header = self._parse_from_header(msg.get('From', ''))
                    to_email = self._decode_header(msg.get('To', ''))
                    subject = self._decode_header(msg.get('Subject', ''))
                    date_header = msg.get('Date', '')
                    
                    # Get text content (first 20KB)
                    snippet = self._extract_text_content(msg)
                    
                    # Parse date
                    received_at = self._parse_date(date_header)
                    
                    message_data = {
                        'uid': uid,
                        'message_id': message_id.strip('<>') if message_id else None,
                        'in_reply_to': in_reply_to.strip('<>') if in_reply_to else None,
                        'references': references,
                        'from_email': from_header['email'],
                        'from_name': from_header['name'],
                        'to_email': to_email,
                        'subject': self._normalize_subject(subject),
                        'snippet': snippet,
                        'raw_size': len(response_part[1]),
                        'received_at': received_at,
                        'encoding_issue': False  # Will be set if decode fails
                    }
                    
                    messages.append(message_data)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse message: {str(e)}")
                    # Create minimal message with encoding issue flag
                    messages.append({
                        'uid': uid,
                        'message_id': None,
                        'from_email': 'unknown@unknown.com',
                        'subject': 'Encoding Error',
                        'snippet': 'Message could not be decoded',
                        'received_at': datetime.utcnow(),
                        'encoding_issue': True
                    })
        
        return messages
    
    def _decode_header(self, header: str) -> str:
        """Decode email header with charset handling"""
        if not header:
            return ""
        
        try:
            decoded_parts = decode_header(header)
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding, errors='replace')
                    else:
                        decoded_string += part.decode('utf-8', errors='replace')
                else:
                    decoded_string += part
            
            return decoded_string.strip()
        except Exception:
            return header  # Return as-is if decode fails
    
    def _parse_references(self, references: str) -> List[str]:
        """Parse References header into list of message IDs"""
        if not references:
            return []
        
        # Extract message IDs from references
        message_ids = re.findall(r'<[^>]+>', references)
        return [mid.strip('<>') for mid in message_ids]
    
    def _parse_from_header(self, from_header: str) -> Dict[str, Optional[str]]:
        """Parse From header into name and email"""
        if not from_header:
            return {'name': None, 'email': 'unknown@unknown.com'}
        
        try:
            # Try to parse "Name <email@domain.com>" format
            match = re.match(r'^(.+?)\s*<(.+?)>$', from_header.strip())
            if match:
                name = self._decode_header(match.group(1).strip('"'))
                email_addr = match.group(2).strip().lower()
                return {'name': name, 'email': email_addr}
            
            # Just email address
            email_addr = from_header.strip().lower()
            return {'name': None, 'email': email_addr}
            
        except Exception:
            return {'name': None, 'email': 'unknown@unknown.com'}
    
    def _extract_text_content(self, msg: email.message.Message) -> str:
        """Extract text content from email message (max 20KB)"""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            text = payload.decode(charset, errors='replace')
                            return text[:20480]  # Max 20KB
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    text = payload.decode(charset, errors='replace')
                    return text[:20480]  # Max 20KB
            
            return ""
        except Exception:
            return "Content could not be decoded"
    
    def _normalize_subject(self, subject: str) -> str:
        """Normalize subject by removing Re:, Fwd: prefixes"""
        if not subject:
            return ""
        
        # Remove common prefixes
        normalized = re.sub(r'^(Re:|RE:|Fwd:|FWD:|Fw:)\s*', '', subject, flags=re.IGNORECASE)
        return normalized.strip()
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date header"""
        if not date_str:
            return datetime.utcnow()
        
        try:
            # Try to parse standard email date format
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            return datetime.utcnow()
    
    def close(self):
        """Close IMAP connection"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except Exception:
                pass
            finally:
                self.connection = None
