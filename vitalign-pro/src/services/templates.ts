import { Template, TemplatePreviewResponse, TestsendPayload, TemplatesResponse, TemplateVarItem } from '@/types/template';

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
    // For development, use a mock auth token
    const authToken = 'mock-jwt-token-for-development';
    
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

export const templatesService = {
  async getTemplates(): Promise<TemplatesResponse> {
    try {
      console.log('Calling templates API:', `${API_BASE_URL}/templates`);
      return await apiCall<TemplatesResponse>('/templates');
    } catch (error) {
      console.warn('Templates API call failed, using fallback:', error);
      console.log('API Base URL:', API_BASE_URL);
      
      // Fallback voor development als backend niet draait
      return {
        items: [],
        total: 0
      };
    }
  },

  async getTemplate(id: string): Promise<Template> {
    return await apiCall<Template>(`/templates/${id}`);
  },

  async getTemplatePreview(templateId: string, leadId?: string): Promise<TemplatePreviewResponse> {
    const queryString = buildQueryString({ lead_id: leadId });
    const endpoint = `/templates/${templateId}/preview${queryString ? `?${queryString}` : ''}`;
    return await apiCall<TemplatePreviewResponse>(endpoint);
  },

  async getTemplateVariables(templateId: string): Promise<TemplateVarItem[]> {
    return await apiCall<TemplateVarItem[]>(`/templates/${templateId}/variables`);
  },

  async sendTest(templateId: string, payload: TestsendPayload): Promise<{ ok: boolean }> {
    return await apiCall<{ ok: boolean }>(`/templates/${templateId}/testsend`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }
};