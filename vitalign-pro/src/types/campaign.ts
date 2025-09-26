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

export interface CampaignCreatePayload {
  name: string;
  templateId: string;
  startType: 'now' | 'scheduled';
  scheduledStart?: Date;
  followUp: {
    enabled: boolean;
    days: number;
    attachmentRequired: boolean;
  };
  targetType: 'filter' | 'static';
  leadIds?: string[];
  filters?: any; // LeadsQuery type from leads
  dedupe: {
    suppressBounced: boolean;
    contactedLastDays: number;
    onePerDomain: boolean;
  };
  domains: string[];
  throttle: {
    perHour: number;
    windowStart: string; // "08:00"
    windowEnd: string; // "17:00"
    weekdays: boolean;
  };
  retry: {
    maxAttempts: number;
    backoffHours: number;
  };
}

export interface CampaignDetail extends Campaign {
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