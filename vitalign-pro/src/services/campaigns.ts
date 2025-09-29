import { 
  Campaign, 
  CampaignDetail, 
  CampaignCreatePayload, 
  CampaignMessage, 
  DryRunResult 
} from '@/types/campaign';

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

export const campaignsService = {
  async getCampaigns(): Promise<{ items: Campaign[]; total: number }> {
    return await apiCall<{ items: Campaign[]; total: number }>('/campaigns');
  },

  async createCampaign(payload: CampaignCreatePayload): Promise<{ id: string }> {
    return await apiCall<{ id: string }>('/campaigns', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getCampaign(id: string): Promise<CampaignDetail | null> {
    try {
      return await apiCall<CampaignDetail>(`/campaigns/${id}`);
    } catch (error) {
      if (error instanceof Error && error.message.includes('404')) {
        return null;
      }
      throw error;
    }
  },

  async pauseCampaign(id: string): Promise<{ ok: boolean }> {
    return await apiCall<{ ok: boolean }>(`/campaigns/${id}/pause`, {
      method: 'POST',
    });
  },

  async resumeCampaign(id: string): Promise<{ ok: boolean }> {
    return await apiCall<{ ok: boolean }>(`/campaigns/${id}/resume`, {
      method: 'POST',
    });
  },

  async stopCampaign(id: string): Promise<{ ok: boolean }> {
    return await apiCall<{ ok: boolean }>(`/campaigns/${id}/stop`, {
      method: 'POST',
    });
  },

  async duplicateCampaign(id: string): Promise<{ id: string }> {
    return await apiCall<{ id: string }>(`/campaigns/${id}/duplicate`, {
      method: 'POST',
    });
  },

  async dryRunCampaign(id: string): Promise<DryRunResult> {
    return await apiCall<DryRunResult>(`/campaigns/${id}/dry-run`);
  },

  async getCampaignMessages(campaignId: string): Promise<CampaignMessage[]> {
    return await apiCall<CampaignMessage[]>(`/campaigns/${campaignId}/messages`);
  },

  async resendMessage(messageId: string): Promise<{ ok: boolean }> {
    return await apiCall<{ ok: boolean }>(`/messages/${messageId}/resend`, {
      method: 'POST',
    });
  }
};