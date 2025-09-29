import { StatsSummary, StatsQuery, StatsExportQuery, GlobalStats, DomainStats, CampaignStats, TimelinePoint } from '@/types/stats';

// Mock data generator for realistic statistics
const generateTimelineData = (days: number = 30): TimelinePoint[] => {
  const timeline: TimelinePoint[] = [];
  const today = new Date();
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    
    // Skip weekends for more realistic data
    const isWeekend = date.getDay() === 0 || date.getDay() === 6;
    const sent = isWeekend ? 0 : Math.floor(Math.random() * 150) + 50;
    const opens = Math.floor(sent * (0.25 + Math.random() * 0.15)); // 25-40% open rate
    
    timeline.push({
      date: date.toISOString().split('T')[0],
      sent,
      opens
    });
  }
  
  return timeline;
};

const mockDomains: DomainStats[] = [
  {
    domain: 'punthelder.nl',
    sent: 1247,
    openRate: 0.34,
    bounces: 23
  },
  {
    domain: 'vitalign.nl',
    sent: 892,
    openRate: 0.28,
    bounces: 18
  },
  {
    domain: 'innovate-solutions.com',
    sent: 654,
    openRate: 0.31,
    bounces: 12
  },
  {
    domain: 'techpartners.eu',
    sent: 423,
    openRate: 0.26,
    bounces: 8
  }
];

const mockCampaigns: CampaignStats[] = [
  {
    id: 'campaign-001',
    name: 'Welcome Series Q4',
    sent: 1456,
    openRate: 0.32,
    bounces: 28
  },
  {
    id: 'campaign-002', 
    name: 'Product Launch - VitalAlign Pro',
    sent: 892,
    openRate: 0.38,
    bounces: 15
  },
  {
    id: 'campaign-003',
    name: 'Holiday Greetings 2024',
    sent: 2134,
    openRate: 0.29,
    bounces: 41
  },
  {
    id: 'campaign-004',
    name: 'Newsletter - September',
    sent: 734,
    openRate: 0.25,
    bounces: 12
  }
];

const calculateGlobalStats = (timeline: TimelinePoint[]): GlobalStats => {
  const totalSent = timeline.reduce((sum, point) => sum + point.sent, 0);
  const totalOpens = timeline.reduce((sum, point) => sum + point.opens, 0);
  const openRate = totalSent > 0 ? totalOpens / totalSent : 0;
  
  // Calculate bounces from domains (mock calculation)
  const bounces = mockDomains.reduce((sum, domain) => sum + domain.bounces, 0);
  
  return {
    totalSent,
    openRate,
    bounces
  };
};

// Simulate API delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

class StatsService {
  async getSummary(query: StatsQuery = {}): Promise<StatsSummary> {
    await delay(300); // Simulate API call
    
    // Generate timeline data (default last 30 days)
    const timeline = generateTimelineData(30);
    const global = calculateGlobalStats(timeline);
    
    // Filter data based on query (simplified for MVP)
    let domains = [...mockDomains];
    let campaigns = [...mockCampaigns];
    
    if (query.templateId) {
      // Filter campaigns by template (mock logic)
      campaigns = campaigns.filter(c => c.id.includes('001') || c.id.includes('002'));
    }
    
    return {
      global,
      domains,
      campaigns,
      timeline
    };
  }
  
  async exportData(query: StatsExportQuery): Promise<string> {
    await delay(500); // Simulate export processing
    
    const summary = await this.getSummary(query);
    
    switch (query.scope) {
      case 'global':
        return this.generateGlobalCSV(summary.global, summary.timeline);
      case 'domain':
        return this.generateDomainCSV(summary.domains);
      case 'campaign':
        return this.generateCampaignCSV(summary.campaigns);
      default:
        throw new Error('Invalid export scope');
    }
  }
  
  private generateGlobalCSV(global: GlobalStats, timeline: TimelinePoint[]): string {
    let csv = 'Metric,Value\n';
    csv += `Total Sent,${global.totalSent}\n`;
    csv += `Open Rate,${(global.openRate * 100).toFixed(2)}%\n`;
    csv += `Bounces,${global.bounces}\n\n`;
    
    csv += 'Date,Sent,Opens\n';
    timeline.forEach(point => {
      csv += `${point.date},${point.sent},${point.opens}\n`;
    });
    
    return csv;
  }
  
  private generateDomainCSV(domains: DomainStats[]): string {
    let csv = 'Domain,Sent,Open Rate,Bounces\n';
    domains.forEach(domain => {
      csv += `${domain.domain},${domain.sent},${(domain.openRate * 100).toFixed(2)}%,${domain.bounces}\n`;
    });
    return csv;
  }
  
  private generateCampaignCSV(campaigns: CampaignStats[]): string {
    let csv = 'Campaign ID,Campaign Name,Sent,Open Rate,Bounces\n';
    campaigns.forEach(campaign => {
      csv += `${campaign.id},${campaign.name},${campaign.sent},${(campaign.openRate * 100).toFixed(2)}%,${campaign.bounces}\n`;
    });
    return csv;
  }
}

export const statsService = new StatsService();
