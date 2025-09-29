export interface GlobalStats {
  totalSent: number;
  openRate: number;
  bounces: number;
}

export interface DomainStats {
  domain: string;
  sent: number;
  openRate: number;
  bounces: number;
}

export interface CampaignStats {
  id: string;
  name: string;
  sent: number;
  openRate: number;
  bounces: number;
}

export interface TimelinePoint {
  date: string;
  sent: number;
  opens: number;
}

export interface StatsSummary {
  global: GlobalStats;
  domains: DomainStats[];
  campaigns: CampaignStats[];
  timeline: TimelinePoint[];
}

export interface StatsQuery {
  from?: string; // YYYY-MM-DD format
  to?: string;   // YYYY-MM-DD format
  templateId?: string;
}

export interface StatsExportQuery extends StatsQuery {
  scope: 'global' | 'domain' | 'campaign';
  id?: string; // For domain or campaign specific export
}
