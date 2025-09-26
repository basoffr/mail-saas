export interface Template {
  id: string;
  name: string;
  subject: string;
  bodyHtml: string;
  updatedAt: string;
  assets?: Array<{
    key: string;
    type: 'static' | 'cid';
  }>;
}

export interface TemplateVarItem {
  key: string;
  required: boolean;
  source: 'lead' | 'vars' | 'campaign' | 'image';
  example?: string;
}

export interface TemplatePreviewResponse {
  html: string;
  text: string;
  warnings?: string[];
}

export interface TestsendPayload {
  to: string;
  leadId?: string | null;
}

export interface TemplatesResponse {
  items: Template[];
  total?: number;
}