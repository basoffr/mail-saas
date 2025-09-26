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
  vars: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
}

export enum LeadStatus {
  NEW = 'new',
  QUALIFIED = 'qualified',
  CONTACTED = 'contacted',
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