from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import csv
import io

from app.models.campaign import Message, Campaign, MessageStatus
from app.schemas.stats import (
    StatsSummary, GlobalStats, DomainStats, CampaignStats, 
    TimelineData, TimelinePoint
)


class StatsService:
    def __init__(self):
        # In-memory stores (MVP)
        self.messages: List[Message] = []
        self.campaigns: List[Campaign] = []
        self._init_sample_data()
    
    def _init_sample_data(self):
        """Initialize with sample data for MVP"""
        from datetime import timedelta
        
        # Sample campaigns
        self.campaigns = [
            Campaign(
                id="campaign-001",
                name="Welcome Campaign",
                template_id="welcome-001",
                status="completed",
                created_at=datetime.utcnow() - timedelta(days=30)
            ),
            Campaign(
                id="campaign-002", 
                name="Follow-up Campaign",
                template_id="followup-001",
                status="running",
                created_at=datetime.utcnow() - timedelta(days=15)
            )
        ]
        
        # Sample messages with realistic distribution
        base_time = datetime.utcnow() - timedelta(days=30)
        domains = ["gmail.com", "outlook.com", "company.com", "business.nl"]
        
        for i in range(150):  # Sample size for testing
            days_offset = i // 5  # Spread over 30 days
            message_time = base_time + timedelta(days=days_offset)
            
            # Determine status (80% sent, 10% bounced, 10% failed)
            if i % 10 == 0:
                status = MessageStatus.bounced
                sent_at = None
                open_at = None
            elif i % 10 == 1:
                status = MessageStatus.failed
                sent_at = None
                open_at = None
            else:
                status = MessageStatus.sent
                sent_at = message_time
                # 40% open rate
                open_at = message_time + timedelta(hours=2) if i % 5 < 2 else None
            
            message = Message(
                id=f"msg-{i:03d}",
                campaign_id="campaign-001" if i < 100 else "campaign-002",
                lead_id=f"lead-{i:03d}",
                domain_used=domains[i % len(domains)],
                scheduled_at=message_time,
                sent_at=sent_at,
                status=status,
                open_at=open_at,
                created_at=message_time
            )
            self.messages.append(message)
    
    def get_stats_summary(
        self, 
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        template_id: Optional[str] = None
    ) -> StatsSummary:
        """Get comprehensive stats summary"""
        
        # Filter messages by date range
        filtered_messages = self._filter_messages_by_date(from_date, to_date)
        
        # Calculate global stats
        global_stats = self._calculate_global_stats(filtered_messages)
        
        # Calculate domain stats
        domain_stats = self._calculate_domain_stats(filtered_messages)
        
        # Calculate campaign stats
        campaign_stats = self._calculate_campaign_stats(filtered_messages)
        
        # Calculate timeline data
        timeline = self._calculate_timeline(filtered_messages)
        
        return StatsSummary(
            global_stats=global_stats,
            domains=domain_stats,
            campaigns=campaign_stats,
            timeline=timeline
        )
    
    def _filter_messages_by_date(
        self, 
        from_date: Optional[date], 
        to_date: Optional[date]
    ) -> List[Message]:
        """Filter messages by date range"""
        if not from_date and not to_date:
            return self.messages
        
        filtered = []
        for msg in self.messages:
            msg_date = msg.sent_at.date() if msg.sent_at else msg.created_at.date()
            
            if from_date and msg_date < from_date:
                continue
            if to_date and msg_date > to_date:
                continue
                
            filtered.append(msg)
        
        return filtered
    
    def _calculate_global_stats(self, messages: List[Message]) -> GlobalStats:
        """Calculate global KPIs"""
        total_sent = sum(1 for msg in messages if msg.status == MessageStatus.sent)
        total_opens = sum(1 for msg in messages if msg.open_at is not None)
        bounces = sum(1 for msg in messages if msg.status == MessageStatus.bounced)
        
        open_rate = (total_opens / total_sent) if total_sent > 0 else 0.0
        
        return GlobalStats(
            total_sent=total_sent,
            total_opens=total_opens,
            open_rate=round(open_rate, 3),
            bounces=bounces
        )
    
    def _calculate_domain_stats(self, messages: List[Message]) -> List[DomainStats]:
        """Calculate per-domain statistics"""
        domain_data = defaultdict(lambda: {
            'sent': 0, 'opens': 0, 'bounces': 0, 'last_activity': None
        })
        
        for msg in messages:
            domain = msg.domain_used
            
            if msg.status == MessageStatus.sent:
                domain_data[domain]['sent'] += 1
                
            if msg.open_at:
                domain_data[domain]['opens'] += 1
                
            if msg.status == MessageStatus.bounced:
                domain_data[domain]['bounces'] += 1
            
            # Track last activity
            activity_time = msg.open_at or msg.sent_at or msg.created_at
            if activity_time:
                current_last = domain_data[domain]['last_activity']
                if not current_last or activity_time > current_last:
                    domain_data[domain]['last_activity'] = activity_time
        
        # Convert to DomainStats objects
        stats = []
        for domain, data in domain_data.items():
            open_rate = (data['opens'] / data['sent']) if data['sent'] > 0 else 0.0
            last_activity = data['last_activity'].isoformat() if data['last_activity'] else None
            
            stats.append(DomainStats(
                domain=domain,
                sent=data['sent'],
                opens=data['opens'],
                open_rate=round(open_rate, 3),
                bounces=data['bounces'],
                last_activity=last_activity
            ))
        
        # Sort by sent count descending
        return sorted(stats, key=lambda x: x.sent, reverse=True)
    
    def _calculate_campaign_stats(self, messages: List[Message]) -> List[CampaignStats]:
        """Calculate per-campaign statistics"""
        campaign_data = defaultdict(lambda: {
            'sent': 0, 'opens': 0, 'bounces': 0
        })
        
        for msg in messages:
            campaign_id = msg.campaign_id
            
            if msg.status == MessageStatus.sent:
                campaign_data[campaign_id]['sent'] += 1
                
            if msg.open_at:
                campaign_data[campaign_id]['opens'] += 1
                
            if msg.status == MessageStatus.bounced:
                campaign_data[campaign_id]['bounces'] += 1
        
        # Convert to CampaignStats objects
        stats = []
        for campaign_id, data in campaign_data.items():
            # Find campaign details
            campaign = next((c for c in self.campaigns if c.id == campaign_id), None)
            campaign_name = campaign.name if campaign else f"Campaign {campaign_id}"
            campaign_status = campaign.status if campaign else "unknown"
            start_date = campaign.created_at.date().isoformat() if campaign else None
            
            open_rate = (data['opens'] / data['sent']) if data['sent'] > 0 else 0.0
            
            stats.append(CampaignStats(
                id=campaign_id,
                name=campaign_name,
                sent=data['sent'],
                opens=data['opens'],
                open_rate=round(open_rate, 3),
                bounces=data['bounces'],
                status=campaign_status,
                start_date=start_date
            ))
        
        # Sort by sent count descending
        return sorted(stats, key=lambda x: x.sent, reverse=True)
    
    def _calculate_timeline(self, messages: List[Message]) -> TimelineData:
        """Calculate daily timeline data"""
        daily_sent = defaultdict(int)
        daily_opens = defaultdict(int)
        
        for msg in messages:
            # Count sent messages by date
            if msg.sent_at:
                sent_date = msg.sent_at.date().isoformat()
                daily_sent[sent_date] += 1
            
            # Count opens by date
            if msg.open_at:
                open_date = msg.open_at.date().isoformat()
                daily_opens[open_date] += 1
        
        # Get all dates and sort
        all_dates = set(daily_sent.keys()) | set(daily_opens.keys())
        sorted_dates = sorted(all_dates)
        
        # Create timeline points
        timeline_points = []
        for date_str in sorted_dates:
            timeline_points.append(TimelinePoint(
                date=date_str,
                sent=daily_sent.get(date_str, 0),
                opens=daily_opens.get(date_str, 0)
            ))
        
        return TimelineData(
            sent_by_day=timeline_points,
            opens_by_day=timeline_points  # Same data, different view
        )
    
    def export_csv(
        self, 
        scope: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        entity_id: Optional[str] = None
    ) -> str:
        """Export statistics as CSV"""
        
        filtered_messages = self._filter_messages_by_date(from_date, to_date)
        
        if scope == "global":
            return self._export_global_csv(filtered_messages)
        elif scope == "domain":
            return self._export_domain_csv(filtered_messages, entity_id)
        elif scope == "campaign":
            return self._export_campaign_csv(filtered_messages, entity_id)
        else:
            raise ValueError(f"Invalid export scope: {scope}")
    
    def _export_global_csv(self, messages: List[Message]) -> str:
        """Export global stats as CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['Date', 'Sent', 'Opens', 'Bounces', 'Open_Rate'])
        
        # Daily data
        timeline = self._calculate_timeline(messages)
        daily_bounces = defaultdict(int)
        
        # Calculate daily bounces
        for msg in messages:
            if msg.status == MessageStatus.bounced:
                bounce_date = (msg.created_at.date() if msg.created_at else date.today()).isoformat()
                daily_bounces[bounce_date] += 1
        
        for point in timeline.sent_by_day:
            bounces = daily_bounces.get(point.date, 0)
            open_rate = (point.opens / point.sent) if point.sent > 0 else 0.0
            
            writer.writerow([
                point.date,
                point.sent,
                point.opens,
                bounces,
                round(open_rate, 3)
            ])
        
        return output.getvalue()
    
    def _export_domain_csv(self, messages: List[Message], domain_filter: Optional[str]) -> str:
        """Export domain stats as CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['Domain', 'Sent', 'Opens', 'Open_Rate', 'Bounces', 'Last_Activity'])
        
        domain_stats = self._calculate_domain_stats(messages)
        
        for stat in domain_stats:
            if domain_filter and stat.domain != domain_filter:
                continue
                
            writer.writerow([
                stat.domain,
                stat.sent,
                stat.opens,
                stat.open_rate,
                stat.bounces,
                stat.last_activity or ""
            ])
        
        return output.getvalue()
    
    def _export_campaign_csv(self, messages: List[Message], campaign_filter: Optional[str]) -> str:
        """Export campaign stats as CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['Campaign_ID', 'Campaign_Name', 'Sent', 'Opens', 'Open_Rate', 'Bounces', 'Status', 'Start_Date'])
        
        campaign_stats = self._calculate_campaign_stats(messages)
        
        for stat in campaign_stats:
            if campaign_filter and stat.id != campaign_filter:
                continue
                
            writer.writerow([
                stat.id,
                stat.name,
                stat.sent,
                stat.opens,
                stat.open_rate,
                stat.bounces,
                stat.status,
                stat.start_date or ""
            ])
        
        return output.getvalue()


# Global instance
stats_service = StatsService()
