export type WeakLinkFlag = boolean;

export interface InboxMessageOut {
  id: string;
  accountId: string;
  accountLabel: string;
  folder: 'INBOX';
  uid: number;
  messageId?: string | null;
  inReplyTo?: string | null;
  references?: string[] | null;
  fromEmail: string;
  fromName?: string | null;
  toEmail?: string | null;
  subject: string;
  snippet: string;             // max ~20kB
  rawSize?: number;
  receivedAt: string;          // ISO
  isRead: boolean;             // app-lokaal
  linkedCampaignId?: string | null;
  linkedCampaignName?: string | null;
  linkedLeadId?: string | null;
  linkedLeadEmail?: string | null;
  linkedMessageId?: string | null;
  weakLink?: WeakLinkFlag;     // onzekere koppeling → badge
  encodingIssue?: boolean;     // best-effort decode
}

export interface InboxListResponse { 
  items: InboxMessageOut[]; 
  total: number; 
}

export interface FetchStartResponse { 
  ok: boolean; 
  run_id: string; 
}

export interface MarkReadResponse { 
  ok: boolean; 
}

export interface MailAccountOut {
  id: string;
  label: string;
  imapHost: string;
  imapPort: number;            // default 993
  useSsl: boolean;             // true
  usernameMasked: string;      // nooit plaintext
  active: boolean;
  lastFetchAt?: string | null;
  lastSeenUid?: number | null;
}

export interface InboxRunOut {
  id: string;
  accountId: string;
  startedAt: string;
  finishedAt?: string | null;
  newCount?: number;
  error?: string | null;
}

export interface InboxQuery {
  page?: number;
  pageSize?: number;
  accountId?: string;
  campaignId?: string;
  unread?: boolean;
  q?: string;
  from?: string;
  to?: string;
}
