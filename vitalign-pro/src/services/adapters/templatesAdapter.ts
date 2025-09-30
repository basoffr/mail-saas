/**
 * Templates Response Adapter
 * Transforms API responses (snake_case) to UI types (camelCase)
 */

import { asArray, asString, pick } from '@/lib/safe';

export interface UiTemplate {
  id: string;
  name: string;
  subject: string;
  bodyHtml?: string;
  updatedAt: string;
  requiredVars?: string[];
  assets?: Array<{
    key: string;
    type: 'static' | 'cid';
  }>;
  variables?: Array<{
    key: string;
    required: boolean;
    source: 'lead' | 'vars' | 'campaign' | 'image';
    example?: string;
  }>;
}

export interface UiTemplatePreview {
  html: string;
  text: string;
  warnings?: string[];
}

/**
 * Transform API template response to UI format
 */
export function toUiTemplate(apiResponse: any): UiTemplate {
  const data = apiResponse || {};

  return {
    id: asString(pick(data, ['id'], '')),
    name: asString(pick(data, ['name'], '')),
    // Handle both snake_case (from API) and camelCase (fallback)
    subject: asString(pick(data, ['subject', 'subject_template', 'subjectTemplate'], '')),
    bodyHtml: pick(data, ['bodyHtml', 'body_html', 'body_template', 'bodyTemplate'], undefined),
    // Ensure updatedAt is always a valid string
    updatedAt: asString(pick(data, ['updatedAt', 'updated_at'], new Date().toISOString())),
    requiredVars: pick(data, ['requiredVars', 'required_vars'], undefined),
    assets: pick(data, ['assets'], undefined),
    variables: pick(data, ['variables'], undefined),
  };
}

/**
 * Transform API templates list response
 */
export function toUiTemplatesList(apiResponse: any): { items: UiTemplate[]; total: number } {
  const items = asArray(pick(apiResponse, ['items'], []));
  const total = pick(apiResponse, ['total'], items.length) as number;

  return {
    items: items.map(toUiTemplate),
    total,
  };
}

/**
 * Transform API template preview response
 */
export function toUiTemplatePreview(apiResponse: any): UiTemplatePreview {
  const data = apiResponse || {};

  return {
    html: asString(pick(data, ['html'], '')),
    text: asString(pick(data, ['text'], '')),
    warnings: pick(data, ['warnings'], undefined),
  };
}

/**
 * Transform API template variables response
 */
export function toUiTemplateVariables(apiResponse: any): Array<{
  key: string;
  required: boolean;
  source: 'lead' | 'vars' | 'campaign' | 'image';
  example?: string;
}> {
  const items = asArray(apiResponse);

  return items.map((item: any) => ({
    key: asString(pick(item, ['key'], '')),
    required: pick(item, ['required'], false) as boolean,
    source: pick(item, ['source'], 'lead') as 'lead' | 'vars' | 'campaign' | 'image',
    example: pick(item, ['example'], undefined),
  }));
}
