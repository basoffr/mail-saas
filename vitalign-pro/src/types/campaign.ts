export interface Campaign {
  id: string;
  name: string;
  status: CampaignStatus;
  templateId: string;
  templateName: string;
  targetCount: number;
  sentCount: number;
  openCount: number;
  clickCount: number;
  bounceCount: number;
  replyCount: number;
  startDate: Date;
  endDate?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export enum CampaignStatus {
  DRAFT = 'draft',
  SCHEDULED = 'scheduled',
  RUNNING = 'running',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  STOPPED = 'stopped'
}

export enum MessageStatus {
  PENDING = 'pending',
  SENT = 'sent',
  DELIVERED = 'delivered',
  OPENED = 'opened',
  CLICKED = 'clicked',
  BOUNCED = 'bounced',
  FAILED = 'failed',
  REPLIED = 'replied'
}

/**
 * Simplified campaign creation payload.
 * All settings are auto-assigned by backend:
 * - Flow/version (round-robin first available domain)
 * - Domain (1-to-1 with flow)
 * - Templates (4 templates per flow version)
 * - Followup (hard-coded: +3 workdays)
 * - Throttle/window (hard-coded sending policy)
 */
export interface CampaignCreatePayload {
  name: string;
  
  // Audience selection
  audience: {
    mode: 'filter' | 'static';
    lead_ids?: string[];
    filter_criteria?: any;
    
    // Dedupe settings
    exclude_suppressed: boolean;
    exclude_recent_days: number;
    one_per_domain: boolean;
  };
  
  // Schedule
  schedule: {
    start_mode: 'now' | 'scheduled';
    start_at?: string; // ISO datetime
  };
  
  // Legacy fields (ignored by backend, kept for compatibility)
  templateId?: string;
  domains?: string[];
  followUp?: any;
  throttle?: any;
  retry?: any;
}

export interface CampaignDetail extends Campaign {
  // Auto-assigned info
  flowVersion: number; // 1-4
  domain: string; // punthelder-{type}.nl
  templates: string[]; // ["v1m1", "v1m2", "v1m3", "v1m4"]
  estimatedDurationDays: number; // 9 workdays
  
  settings: {
    followUp: {
      enabled: boolean;
      days: number;
      attachmentRequired: boolean;
    };
    dedupe: {
      suppressBounced: boolean;
      contactedLastDays: number;
      onePerDomain: boolean;
    };
    domains: string[];
    throttle: {
      perHour: number;
      windowStart: string;
      windowEnd: string;
      weekdays: boolean;
    };
    retry: {
      maxAttempts: number;
      backoffHours: number;
    };
  };
  stats: {
    totalMessages: number;
    sentToday: number;
    scheduledCount: number;
    followUpCount: number;
    sentByDay: { date: string; sent: number }[];
  };
}

export interface CampaignMessage {
  id: string;
  campaignId: string;
  leadId: string;
  leadEmail: string;
  leadCompany?: string;
  status: MessageStatus;
  sentAt?: Date;
  deliveredAt?: Date;
  openedAt?: Date;
  clickedAt?: Date;
  bouncedAt?: Date;
  failedAt?: Date;
  repliedAt?: Date;
  errorMessage?: string;
  attempts: number;
  nextRetryAt?: Date;
  isFollowUp: boolean;
  templateSnapshot: string;
}

export interface CampaignKPIs {
  totalSent: number;
  deliveryRate: number;
  openRate: number;
  clickRate: number;
  bounceRate: number;
  replyRate: number;
}

export interface DryRunResult {
  totalPlanned: number;
  byDay: { date: string; planned: number }[];
  warnings: string[];
}