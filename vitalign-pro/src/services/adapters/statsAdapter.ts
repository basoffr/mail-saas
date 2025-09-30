/**
 * Stats Response Adapter
 * Normalizes API responses (camelCase/snake_case) to consistent UI types
 * Provides safe defaults for all fields
 */

export interface UiGlobalStats {
  totalSent: number;
  totalOpens: number;
  openRate: number;
  bounces: number;
}

export interface UiTimelinePoint {
  date: string;
  sent: number;
  opens: number;
}

export interface UiDomainStats {
  domain: string;
  sent: number;
  openRate: number;
  bounces: number;
}

export interface UiCampaignStats {
  id: string;
  name: string;
  sent: number;
  openRate: number;
  bounces: number;
}

export interface UiStatsSummary {
  global: UiGlobalStats;
  timeline: UiTimelinePoint[];
  domains: UiDomainStats[];
  campaigns: UiCampaignStats[];
}

/**
 * Coerce value from multiple possible keys, with fallback
 */
function coerce<T>(obj: any, keys: string[], fallback: T): T {
  if (!obj) return fallback;
  for (const key of keys) {
    if (obj[key] !== undefined && obj[key] !== null) {
      return obj[key];
    }
  }
  return fallback;
}

/**
 * Ensure array type
 */
function ensureArray<T>(value: any): T[] {
  return Array.isArray(value) ? value : [];
}

/**
 * Convert API response to UI StatsSummary
 */
export function toUiStatsSummary(apiResponse: any): UiStatsSummary {
  const data = apiResponse || {};
  const globalData = data.global || {};
  const timelineData = data.timeline || [];
  const domainsData = data.domains || [];
  const campaignsData = data.campaigns || [];

  // Normalize global stats
  const global: UiGlobalStats = {
    totalSent: coerce(globalData, ['totalSent', 'total_sent', 'sent'], 0),
    totalOpens: coerce(globalData, ['totalOpens', 'total_opens', 'opens'], 0),
    openRate: coerce(globalData, ['openRate', 'open_rate'], 0),
    bounces: coerce(globalData, ['bounces', 'total_bounces'], 0),
  };

  // Normalize timeline
  const timeline: UiTimelinePoint[] = ensureArray<any>(timelineData).map((point: any) => ({
    date: coerce(point, ['date'], ''),
    sent: coerce(point, ['sent', 'count', 'totalSent', 'total_sent'], 0),
    opens: coerce(point, ['opens', 'totalOpens', 'total_opens'], 0),
  }));

  // Normalize domains
  const domains: UiDomainStats[] = ensureArray<any>(domainsData).map((domain: any) => ({
    domain: coerce(domain, ['domain', 'name'], ''),
    sent: coerce(domain, ['sent', 'totalSent', 'total_sent'], 0),
    openRate: coerce(domain, ['openRate', 'open_rate'], 0),
    bounces: coerce(domain, ['bounces', 'total_bounces'], 0),
  }));

  // Normalize campaigns
  const campaigns: UiCampaignStats[] = ensureArray<any>(campaignsData).map((campaign: any) => ({
    id: coerce(campaign, ['id', 'campaign_id'], ''),
    name: coerce(campaign, ['name', 'campaign_name'], ''),
    sent: coerce(campaign, ['sent', 'totalSent', 'total_sent'], 0),
    openRate: coerce(campaign, ['openRate', 'open_rate'], 0),
    bounces: coerce(campaign, ['bounces', 'total_bounces'], 0),
  }));

  return {
    global,
    timeline,
    domains,
    campaigns,
  };
}
