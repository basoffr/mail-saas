export type ReportFileType = 'pdf' | 'xlsx' | 'png' | 'jpg' | 'jpeg';

export interface ReportItem {
  id: string;
  filename: string;
  type: ReportFileType;
  sizeBytes: number;
  uploadedAt: string;
  boundTo?: {
    kind: 'lead' | 'campaign';
    id: string;
    label?: string;
  } | null;
  storagePath?: string;
  checksum?: string;
  meta?: Record<string, unknown>;
}

export interface ReportsQuery {
  page?: number;
  pageSize?: number;
  types?: ReportFileType[];
  boundFilter?: 'all' | 'bound' | 'unbound';
  boundKind?: 'lead' | 'campaign';
  boundId?: string;
  search?: string;
  dateFrom?: string;
  dateTo?: string;
}

export interface BulkMapRow {
  fileName: string;
  baseKey: string;
  target?: {
    kind: 'lead' | 'image_key' | 'campaign';
    id?: string;
    email?: string;
  };
  status: 'matched' | 'unmatched' | 'ambiguous';
  reason?: string;
}

export interface BulkUploadResult {
  total: number;
  uploaded: number;
  failed: number;
  mappings: Array<{
    fileName: string;
    to?: {
      kind: 'lead' | 'image_key' | 'campaign';
      id?: string;
    };
    status: 'ok' | 'failed';
    error?: string;
  }>;
}

export interface ReportUploadPayload {
  file: File;
  leadId?: string;
  campaignId?: string;
}

export interface ReportBindPayload {
  reportId: string;
  leadId?: string;
  campaignId?: string;
}

export type BulkMode = 'by_image_key' | 'by_email';