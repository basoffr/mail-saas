import { Lead, LeadsQuery, LeadsResponse, LeadStatus, ImportJobStatus, ImportPreview, ImportMapping } from '@/types/lead';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000');

// API Response Type
interface ApiResponse<T> {
  data: T | null;
  error: string | null;
}

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
        'Content-Type': 'application/json',
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
    
    // Better error handling for AbortError
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
    return await apiCall<LeadsResponse>(endpoint);
  },

  async getLead(id: string): Promise<Lead | null> {
    try {
      return await apiCall<Lead>(`/leads/${id}`);
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

    // Use Supabase anon key as auth token for production
    const authToken = import.meta.env.VITE_SUPABASE_ANON_KEY || 'mock-jwt-token-for-development';

    const response = await fetch(`${API_BASE_URL}/import/leads`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result: ApiResponse<ImportJobStatus> = await response.json();
    
    if (result.error) {
      throw new Error(result.error);
    }

    return result.data!;
  },

  async getImportJob(jobId: string): Promise<ImportJobStatus | null> {
    try {
      return await apiCall<ImportJobStatus>(`/import/jobs/${jobId}`);
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

    // Use Supabase anon key as auth token for production
    const authToken = import.meta.env.VITE_SUPABASE_ANON_KEY || 'mock-jwt-token-for-development';

    const response = await fetch(`${API_BASE_URL}/import/preview`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result: ApiResponse<ImportPreview> = await response.json();
    
    if (result.error) {
      throw new Error(result.error);
    }

    return result.data!;
  },

  async getImageUrl(imageKey: string): Promise<string> {
    const queryString = buildQueryString({ key: imageKey });
    return await apiCall<string>(`/assets/image-by-key?${queryString}`);
  }
};