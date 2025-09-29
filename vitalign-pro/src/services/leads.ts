import { Lead, LeadsQuery, LeadsResponse, LeadStatus, ImportJobStatus, ImportPreview, ImportMapping } from '@/types/lead';
import { authService, buildQueryString } from './auth';

// Backend -> UI status mapping (centralized)
export type BackendLeadStatus = 'active' | 'suppressed' | 'bounced';

export const toUiLeadStatus = (s: BackendLeadStatus | string) => {
  switch (s) {
    case 'active':
      return { label: 'Actief', tone: 'success' as const };
    case 'suppressed':
      return { label: 'Onderdrukt', tone: 'warning' as const };
    case 'bounced':
      return { label: 'Bounced', tone: 'destructive' as const };
    default:
      return { label: String(s), tone: 'default' as const };
  }
};

export const toneToBadgeClass = (tone: 'success' | 'warning' | 'destructive' | 'default') => {
  switch (tone) {
    case 'success':
      return 'bg-success/15 text-success-foreground border border-success/20';
    case 'warning':
      return 'bg-warning/15 text-warning-foreground border border-warning/20';
    case 'destructive':
      return 'bg-destructive/15 text-destructive-foreground border border-destructive/20';
    default:
      return 'bg-muted text-muted-foreground';
  }
};

export const leadsService = {
  async getLeads(query: LeadsQuery = {}): Promise<LeadsResponse> {
    const queryString = buildQueryString({
      page: query.page || 1,
      page_size: query.limit || 25,
      search: query.search,
      status: query.status,
      tags: query.tags,
      has_image: query.hasImage,
      has_vars: query.hasVars,
      tld: query.tld,
      sort_by: query.sortBy,
      sort_order: query.sortOrder,
    });

    const endpoint = `/leads${queryString ? `?${queryString}` : ''}`;
    return await authService.apiCall<LeadsResponse>(endpoint);
  },

  async getLead(id: string): Promise<Lead | null> {
    try {
      return await authService.apiCall<Lead>(`/leads/${id}`);
    } catch (error) {
      if (error instanceof Error && error.message.includes('404')) {
        return null;
      }
      throw error;
    }
  },

  async importLeads(file: File, mapping: ImportMapping): Promise<ImportJobStatus> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mapping', JSON.stringify(mapping));

    const response = await fetch(`${authService.getConfig().baseUrl}/import/leads`, {
      method: 'POST',
      headers: authService.getAuthHeadersForFormData(),
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    
    if (result.error) {
      throw new Error(result.error);
    }

    return result.data!;
  },

  async getImportJob(jobId: string): Promise<ImportJobStatus | null> {
    try {
      return await authService.apiCall<ImportJobStatus>(`/import/jobs/${jobId}`);
    } catch (error) {
      if (error instanceof Error && error.message.includes('404')) {
        return null;
      }
      throw error;
    }
  },

  async previewImport(file: File): Promise<ImportPreview> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${authService.getConfig().baseUrl}/import/preview`, {
      method: 'POST',
      headers: authService.getAuthHeadersForFormData(),
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    
    if (result.error) {
      throw new Error(result.error);
    }

    return result.data!;
  },

  async getImageUrl(imageKey: string): Promise<string> {
    const queryString = buildQueryString({ key: imageKey });
    return await authService.apiCall<string>(`/assets/image-by-key?${queryString}`);
  }
};