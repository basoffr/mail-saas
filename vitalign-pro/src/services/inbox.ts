import { 
  InboxMessageOut, 
  InboxListResponse, 
  FetchStartResponse, 
  MarkReadResponse,
  MailAccountOut,
  InboxRunOut,
  InboxQuery 
} from '@/types/inbox';

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

class InboxService {
  private lastFetchTime = 0;
  private readonly minFetchInterval = 2 * 60 * 1000; // 2 minutes

  async fetchMessages(): Promise<FetchStartResponse> {
    const now = Date.now();
    if (now - this.lastFetchTime < this.minFetchInterval) {
      throw new Error('Please wait before fetching again. Minimum interval is 2 minutes.');
    }

    this.lastFetchTime = now;
    return await apiCall<FetchStartResponse>('/inbox/fetch', {
      method: 'POST',
    });
  }

  async getMessages(query: InboxQuery = {}): Promise<InboxListResponse> {
    const queryString = buildQueryString({
      account_id: query.accountId,
      campaign_id: query.campaignId,
      unread: query.unread,
      q: query.q,
      from: query.from,
      to: query.to,
      page: query.page || 1,
      page_size: query.pageSize || 25,
    });

    const endpoint = `/inbox/messages${queryString ? `?${queryString}` : ''}`;
    return await apiCall<InboxListResponse>(endpoint);
  }

  async markAsRead(messageId: string): Promise<MarkReadResponse> {
    return await apiCall<MarkReadResponse>(`/inbox/messages/${messageId}/read`, {
      method: 'POST',
    });
  }

  async getAccounts(): Promise<{ items: MailAccountOut[] }> {
    return await apiCall<{ items: MailAccountOut[] }>('/inbox/accounts');
  }

  async testAccount(accountId: string): Promise<{ ok: boolean; message: string }> {
    return await apiCall<{ ok: boolean; message: string }>(`/inbox/accounts/${accountId}/test`, {
      method: 'POST',
    });
  }

  async toggleAccount(accountId: string): Promise<{ ok: boolean }> {
    return await apiCall<{ ok: boolean }>(`/inbox/accounts/${accountId}/toggle`, {
      method: 'POST',
    });
  }

  async getRuns(query: { accountId?: string; page?: number; pageSize?: number } = {}): Promise<{ items: InboxRunOut[]; total: number }> {
    const queryString = buildQueryString({
      account_id: query.accountId,
      page: query.page || 1,
      page_size: query.pageSize || 25,
    });

    const endpoint = `/inbox/runs${queryString ? `?${queryString}` : ''}`;
    return await apiCall<{ items: InboxRunOut[]; total: number }>(endpoint);
  }
}

export const inboxService = new InboxService();
