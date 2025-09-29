import type { 
  ReportItem, 
  ReportsQuery, 
  BulkUploadResult, 
  ReportUploadPayload, 
  ReportBindPayload,
  BulkMode,
  BulkMapRow 
} from '@/types/report';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000');

// API Response Type
interface ApiResponse<T> {
  data: T | null;
  error: string | null;
}

// API Helper Functions
async function apiCall<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

  try {
    // Use Supabase anon key as auth token for production
    const authToken = import.meta.env.VITE_SUPABASE_ANON_KEY || 'mock-jwt-token-for-development';
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Authorization': `Bearer ${authToken}`,
        ...options.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result: ApiResponse<T> = await response.json();
    
    if (result.error) {
      throw new Error(result.error);
    }

    return result.data!;
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new Error(`Request timeout after ${API_TIMEOUT/1000} seconds`);
      }
      if (error.message.includes('Failed to fetch')) {
        throw new Error(`Cannot connect to API at ${API_BASE_URL}. Is the backend running?`);
      }
    }
    
    throw error;
  }
}

function buildQueryString(params: Record<string, any>): string {
  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      if (Array.isArray(value)) {
        value.forEach(v => searchParams.append(key, String(v)));
      } else {
        searchParams.append(key, String(value));
      }
    }
  });
  
  return searchParams.toString();
}

export const reportsService = {
  async getReports(query: ReportsQuery): Promise<{ items: ReportItem[]; total: number }> {
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
    return await apiCall<{ items: ReportItem[]; total: number }>(endpoint);
  },

  async uploadReport(payload: ReportUploadPayload): Promise<ReportItem> {
    const formData = new FormData();
    formData.append('file', payload.file);
    if (payload.leadId) formData.append('lead_id', payload.leadId);
    if (payload.campaignId) formData.append('campaign_id', payload.campaignId);

    const authToken = import.meta.env.VITE_SUPABASE_ANON_KEY || 'mock-jwt-token-for-development';

    const response = await fetch(`${API_BASE_URL}/reports/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result: ApiResponse<ReportItem> = await response.json();
    
    if (result.error) {
      throw new Error(result.error);
    }

    return result.data!;
  },

  async bulkUpload(zipFile: File, mode: BulkMode): Promise<BulkUploadResult> {
    const formData = new FormData();
    formData.append('zip_file', zipFile);
    formData.append('mode', mode);

    const authToken = import.meta.env.VITE_SUPABASE_ANON_KEY || 'mock-jwt-token-for-development';

    const response = await fetch(`${API_BASE_URL}/reports/bulk-upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result: ApiResponse<BulkUploadResult> = await response.json();
    
    if (result.error) {
      throw new Error(result.error);
    }

    return result.data!;
  },

  async generateBulkMapping(zipFile: File, mode: BulkMode): Promise<BulkMapRow[]> {
    const formData = new FormData();
    formData.append('zip_file', zipFile);
    formData.append('mode', mode);

    const authToken = import.meta.env.VITE_SUPABASE_ANON_KEY || 'mock-jwt-token-for-development';

    const response = await fetch(`${API_BASE_URL}/reports/bulk-mapping`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result: ApiResponse<BulkMapRow[]> = await response.json();
    
    if (result.error) {
      throw new Error(result.error);
    }

    return result.data!;
  },

  async bindReport(payload: ReportBindPayload): Promise<{ ok: true }> {
    return await apiCall<{ ok: true }>(`/reports/${payload.reportId}/bind`, {
      method: 'POST',
      body: JSON.stringify({
        lead_id: payload.leadId,
        campaign_id: payload.campaignId,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    });
  },

  async unbindReport(reportId: string): Promise<{ ok: true }> {
    return await apiCall<{ ok: true }>(`/reports/${reportId}/unbind`, {
      method: 'POST',
    });
  },

  async getDownloadUrl(reportId: string): Promise<string> {
    return await apiCall<string>(`/reports/${reportId}/download-url`);
  },

  // Helper methods for binding
  async searchLeads(query: string): Promise<Array<{ id: string; email: string; company?: string }>> {
    const queryString = buildQueryString({ search: query, limit: 10 });
    const endpoint = `/leads${queryString ? `?${queryString}` : ''}`;
    const result = await apiCall<{ items: Array<{ id: string; email: string; company?: string }>; total: number }>(endpoint);
    return result.items;
  },

  async searchCampaigns(query: string): Promise<Array<{ id: string; name: string }>> {
    const queryString = buildQueryString({ search: query, limit: 10 });
    const endpoint = `/campaigns${queryString ? `?${queryString}` : ''}`;
    const result = await apiCall<{ items: Array<{ id: string; name: string }>; total: number }>(endpoint);
    return result.items;
  },
};