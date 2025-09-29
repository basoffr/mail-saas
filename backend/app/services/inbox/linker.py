from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger


class MessageLinker:
    """Smart linking of inbox messages to campaigns, leads, and outbound messages"""
    
    def __init__(self, messages_store, leads_store, campaigns_store):
        self.messages_store = messages_store
        self.leads_store = leads_store
        self.campaigns_store = campaigns_store
    
    def link_message(self, inbox_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Link inbox message to campaign/lead/message using 4-tier strategy:
        1. in_reply_to -> match smtp_message_id
        2. references -> contains smtp_message_id
        3. from_email + subject + chronology
        4. from_email only (weak link)
        """
        
        # Initialize linking result
        link_result = {
            'linked_campaign_id': None,
            'linked_lead_id': None,
            'linked_message_id': None,
            'weak_link': False
        }
        
        try:
            # Strategy 1: Direct reply via In-Reply-To
            if inbox_message.get('in_reply_to'):
                result = self._link_by_in_reply_to(inbox_message['in_reply_to'])
                if result:
                    link_result.update(result)
                    logger.info(f"Linked message via In-Reply-To: {inbox_message['id']}")
                    return link_result
            
            # Strategy 2: References chain
            if inbox_message.get('references'):
                result = self._link_by_references(inbox_message['references'])
                if result:
                    link_result.update(result)
                    logger.info(f"Linked message via References: {inbox_message['id']}")
                    return link_result
            
            # Strategy 3: Email + Subject + Chronology
            result = self._link_by_email_subject_chronology(
                inbox_message['from_email'],
                inbox_message['subject'],
                inbox_message['received_at']
            )
            if result:
                link_result.update(result)
                logger.info(f"Linked message via email+subject: {inbox_message['id']}")
                return link_result
            
            # Strategy 4: Email only (weak link)
            result = self._link_by_email_only(inbox_message['from_email'])
            if result:
                link_result.update(result)
                link_result['weak_link'] = True
                logger.info(f"Weak link created for message: {inbox_message['id']}")
                return link_result
            
            logger.info(f"No link found for message: {inbox_message['id']}")
            return link_result
            
        except Exception as e:
            logger.error(f"Error linking message {inbox_message.get('id', 'unknown')}: {str(e)}")
            return link_result
    
    def _link_by_in_reply_to(self, in_reply_to: str) -> Optional[Dict[str, Any]]:
        """Link by matching In-Reply-To with smtp_message_id"""
        try:
            # Find outbound message with matching smtp_message_id
            outbound_messages = self.messages_store.get_all()
            
            for msg in outbound_messages:
                if msg.smtp_message_id == in_reply_to:
                    return {
                        'linked_message_id': msg.id,
                        'linked_campaign_id': msg.campaign_id,
                        'linked_lead_id': msg.lead_id
                    }
            
            return None
        except Exception as e:
            logger.error(f"Error in _link_by_in_reply_to: {str(e)}")
            return None
    
    def _link_by_references(self, references: list) -> Optional[Dict[str, Any]]:
        """Link by checking if any reference matches smtp_message_id"""
        try:
            outbound_messages = self.messages_store.get_all()
            
            for ref in references:
                for msg in outbound_messages:
                    if msg.smtp_message_id == ref:
                        return {
                            'linked_message_id': msg.id,
                            'linked_campaign_id': msg.campaign_id,
                            'linked_lead_id': msg.lead_id
                        }
            
            return None
        except Exception as e:
            logger.error(f"Error in _link_by_references: {str(e)}")
            return None
    
    def _link_by_email_subject_chronology(self, from_email: str, subject: str, 
                                        received_at: datetime) -> Optional[Dict[str, Any]]:
        """Link by email + normalized subject + chronological proximity"""
        try:
            # Find lead by email
            leads = self.leads_store.get_all()
            matching_lead = None
            
            for lead in leads:
                if lead.email.lower() == from_email.lower():
                    matching_lead = lead
                    break
            
            if not matching_lead:
                return None
            
            # Find recent outbound messages to this lead
            outbound_messages = self.messages_store.get_all()
            recent_messages = []
            
            # Look for messages sent in the last 30 days
            cutoff_date = received_at - timedelta(days=30)
            
            for msg in outbound_messages:
                if (msg.lead_id == matching_lead.id and 
                    msg.sent_at and 
                    msg.sent_at >= cutoff_date and 
                    msg.sent_at <= received_at):
                    recent_messages.append(msg)
            
            if not recent_messages:
                return None
            
            # Find the most recent message (closest chronologically)
            recent_messages.sort(key=lambda x: x.sent_at, reverse=True)
            closest_message = recent_messages[0]
            
            # Optional: Check subject similarity (basic implementation)
            # For now, just return the chronologically closest match
            
            return {
                'linked_message_id': closest_message.id,
                'linked_campaign_id': closest_message.campaign_id,
                'linked_lead_id': matching_lead.id
            }
            
        except Exception as e:
            logger.error(f"Error in _link_by_email_subject_chronology: {str(e)}")
            return None
    
    def _link_by_email_only(self, from_email: str) -> Optional[Dict[str, Any]]:
        """Weak link by email only"""
        try:
            # Find lead by email
            leads = self.leads_store.get_all()
            
            for lead in leads:
                if lead.email.lower() == from_email.lower():
                    return {
                        'linked_lead_id': lead.id,
                        'linked_campaign_id': None,  # No campaign link
                        'linked_message_id': None    # No specific message link
                    }
            
            return None
        except Exception as e:
            logger.error(f"Error in _link_by_email_only: {str(e)}")
            return None
    
    def _normalize_subject_for_matching(self, subject: str) -> str:
        """Normalize subject for better matching"""
        if not subject:
            return ""
        
        # Convert to lowercase and remove extra whitespace
        normalized = subject.lower().strip()
        
        # Remove common prefixes that might have been added
        import re
        normalized = re.sub(r'^(re:|fwd?:|fw:)\s*', '', normalized)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
