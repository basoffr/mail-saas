export interface Lead {
  id: string;
  email: string;
  companyName?: string;
  domain?: string;
  url?: string;
  tags: string[];
  status: LeadStatus;
  lastMailed?: Date;
  lastOpened?: Date;
  imageKey?: string;
  listName?: string;
  vars: Record<string, any>;
  stopped: boolean;
  deletedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
  
  // Enriched fields (computed by backend)
  hasReport: boolean;
  hasImage: boolean;
  varsCompleteness?: {
    filled: number;
    total: number;
    missing: string[];
    percentage: number;
    is_complete: boolean;
  };
  isComplete: boolean;
  isDeleted: boolean;
}

export enum LeadStatus {
  NEW = 'new',
  QUALIFIED = 'qualified',
  RESPONDED = 'responded',
  CONVERTED = 'converted',
  UNQUALIFIED = 'unqualified',
  BOUNCED = 'bounced'
}

export interface LeadsQuery {
  search?: string;
  tld?: string[];
  status?: LeadStatus[];
  tags?: string[];
  hasImage?: boolean;
  hasVars?: boolean;
  listName?: string;
  isComplete?: boolean;
  sortBy?: 'email' | 'companyName' | 'lastMailed' | 'lastOpened' | 'createdAt';
  sortOrder?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export interface LeadsResponse {
  items: Lead[];
  total: number;
}

export interface ImportJobStatus {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  inserted: number;
  updated: number;
  skipped: number;
  errors: ImportError[];
  createdAt: Date;
  completedAt?: Date;
}

export interface ImportError {
  row: number;
  field?: string;
  message: string;
  value?: any;
}

export interface ImportPreview {
  headers: string[];
  rows: any[][];
  duplicates: number[];
}

export interface ImportMapping {
  [csvColumn: string]: string | null;
}

export interface Template {
  id: string;
  name: string;
}

export interface TemplatePreview {
  html: string;
  text: string;
  warnings?: string[];
}

export interface LeadDeleteRequest {
  lead_ids: string[];
  reason?: string;
}

export interface LeadDeleteResponse {
  deleted_count: number;
  deleted_ids: string[];
  failed_ids: string[];
}

export interface LeadRestoreResponse {
  restored_count: number;
  restored_ids: string[];
  failed_ids: string[];
}