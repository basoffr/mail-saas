import type { 
  ReportItem, 
  ReportsQuery, 
  BulkUploadResult, 
  ReportUploadPayload, 
  ReportBindPayload,
  BulkMode,
  BulkMapRow 
} from '@/types/report';
import { authService, buildQueryString } from './auth';

export const reportsService = {
  async getReports(query: ReportsQuery = {}): Promise<{ items: ReportItem[]; total: number }> {
    const queryString = buildQueryString({
      page: query.page,
      page_size: query.pageSize,
      search: query.search,
      types: query.types,
      bound_filter: query.boundFilter,
      bound_kind: query.boundKind,
      bound_id: query.boundId,
    });

    const endpoint = `/reports${queryString ? `?${queryString}` : ''}`;
    return await authService.apiCall<{ items: ReportItem[]; total: number }>(endpoint);
  },

  async uploadReport(payload: ReportUploadPayload): Promise<ReportItem> {
    const formData = new FormData();
    formData.append('file', payload.file);
    if (payload.leadId) formData.append('lead_id', payload.leadId);
    if (payload.campaignId) formData.append('campaign_id', payload.campaignId);

    const response = await fetch(`${authService.getConfig().baseUrl}/reports/upload`, {
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

  async bulkUpload(file: File, mode: BulkMode): Promise<BulkUploadResult> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${authService.getConfig().baseUrl}/reports/bulk?mode=${mode}`, {
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

  async bindReport(payload: ReportBindPayload): Promise<{ ok: boolean }> {
    return await authService.apiCall<{ ok: boolean }>('/reports/bind', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async unbindReport(reportId: string): Promise<{ ok: boolean }> {
    return await authService.apiCall<{ ok: boolean }>(`/reports/${reportId}/unbind`, {
      method: 'POST',
    });
  },

  async getDownloadUrl(reportId: string): Promise<string> {
    return await authService.apiCall<string>(`/reports/${reportId}/download-url`);
  },

  // Helper methods for binding
  async searchLeads(query: string): Promise<Array<{ id: string; email: string; company?: string }>> {
    const queryString = buildQueryString({ search: query, limit: 10 });
    const endpoint = `/leads${queryString ? `?${queryString}` : ''}`;
    const result = await authService.apiCall<{ items: Array<{ id: string; email: string; company?: string }>; total: number }>(endpoint);
    return result.items;
  },

  async searchCampaigns(query: string): Promise<Array<{ id: string; name: string }>> {
    const queryString = buildQueryString({ search: query, limit: 10 });
    const endpoint = `/campaigns${queryString ? `?${queryString}` : ''}`;
    const result = await authService.apiCall<{ items: Array<{ id: string; name: string }>; total: number }>(endpoint);
    return result.items;
  }
};
