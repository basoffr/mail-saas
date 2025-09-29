import { Settings, SettingsUpdateRequest, SettingsResponse } from '@/types/settings';

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

class SettingsService {
  async getSettings(): Promise<Settings> {
    return await apiCall<Settings>('/settings');
  }

  async updateSettings(updates: SettingsUpdateRequest): Promise<SettingsResponse> {
    return await apiCall<SettingsResponse>('/settings', {
      method: 'POST',
      body: JSON.stringify(updates),
    });
  }

  // Helper method to copy URL to clipboard
  async copyToClipboard(text: string): Promise<boolean> {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (error) {
      // Fallback for older browsers
      try {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        const result = document.execCommand('copy');
        document.body.removeChild(textArea);
        return result;
      } catch (err) {
        return false;
      }
    }
  }

  // Get DNS status labels
  getDnsStatusLabel(status: boolean): { label: string; variant: 'success' | 'destructive' | 'secondary' } {
    return status 
      ? { label: 'OK', variant: 'success' }
      : { label: 'NOK', variant: 'destructive' };
  }

  // Get provider status
  getProviderStatus(settings: Settings): { label: string; variant: 'default' | 'secondary' } {
    return {
      label: settings.emailInfra.current,
      variant: 'default'
    };
  }

  // Format sending window for display
  formatSendingWindow(settings: Settings): string {
    const { days, from, to } = settings.window;
    return `${days.join('–')}, ${from}–${to}`;
  }

  // Format throttle for display
  formatThrottle(settings: Settings): string {
    const { emailsPer, minutes } = settings.throttle;
    return `${emailsPer} email / ${minutes} min / per domein`;
  }
}

export const settingsService = new SettingsService();
