import { StatsSummary, StatsQuery, StatsExportQuery } from '@/types/stats';

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

class StatsService {
  async getSummary(query: StatsQuery = {}): Promise<StatsSummary> {
    const queryString = buildQueryString({
      from_date: query.from,
      to_date: query.to,
      template_id: query.templateId,
    });

    const endpoint = `/stats/summary${queryString ? `?${queryString}` : ''}`;
    return await apiCall<StatsSummary>(endpoint);
  }
  
  async exportData(query: StatsExportQuery): Promise<string> {
    const queryString = buildQueryString({
      scope: query.scope,
      from_date: query.from,
      to_date: query.to,
      template_id: query.templateId,
      id: query.id,
    });

    const endpoint = `/stats/export${queryString ? `?${queryString}` : ''}`;
    return await apiCall<string>(endpoint);
  }
}

export const statsService = new StatsService();
