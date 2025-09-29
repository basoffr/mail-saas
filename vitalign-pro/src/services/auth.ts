// Centralized Authentication Service
// Provides consistent JWT token management across all API calls

export interface AuthConfig {
  token: string;
  baseUrl: string;
  timeout: number;
}

export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
}

class AuthService {
  private token: string;
  private baseUrl: string;
  private timeout: number;

  constructor() {
    // Use Supabase anon key as auth token for production
    this.token = import.meta.env.VITE_SUPABASE_ANON_KEY || 'mock-jwt-token-for-development';
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
    this.timeout = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000');
    
    console.log('Auth Service initialized:', {
      baseUrl: this.baseUrl,
      hasToken: !!this.token,
      timeout: this.timeout
    });
  }

  getAuthHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.token}`,
    };
  }

  getAuthHeadersForFormData(): Record<string, string> {
    return {
      'Authorization': `Bearer ${this.token}`,
    };
  }

  async apiCall<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const url = `${this.baseUrl}${endpoint}`;
      console.log('API Call:', { method: options.method || 'GET', url, hasAuth: !!this.token });

      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          ...this.getAuthHeaders(),
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      console.log('API Response:', { 
        status: response.status, 
        statusText: response.statusText,
        url: response.url 
      });

      if (!response.ok) {
        // Handle different HTTP error statuses
        if (response.status === 401) {
          throw new Error('Authentication failed. Please check your credentials.');
        }
        if (response.status === 403) {
          throw new Error('Access forbidden. You do not have permission to access this resource.');
        }
        if (response.status === 404) {
          throw new Error('Resource not found.');
        }
        if (response.status >= 500) {
          throw new Error('Server error. Please try again later.');
        }
        
        // Try to get error message from response
        try {
          const errorData = await response.json();
          throw new Error(errorData.detail || errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        } catch {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
      }

      const result: ApiResponse<T> = await response.json();
      
      if (result.error) {
        throw new Error(result.error);
      }

      if (result.data === null || result.data === undefined) {
        throw new Error('No data received from server');
      }

      return result.data;
    } catch (error) {
      clearTimeout(timeoutId);
      
      // Better error handling for different error types
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error(`Request timeout after ${this.timeout/1000} seconds`);
        }
        if (error.message.includes('Failed to fetch')) {
          throw new Error(`Cannot connect to API at ${this.baseUrl}. Is the backend running?`);
        }
        if (error.message.includes('NetworkError')) {
          throw new Error('Network error. Please check your internet connection.');
        }
      }
      
      throw error;
    }
  }

  buildQueryString(params: Record<string, any>): string {
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

  // Method to update token if needed
  updateToken(newToken: string): void {
    this.token = newToken;
    console.log('Auth token updated');
  }

  // Method to check if we have a valid token
  hasValidToken(): boolean {
    return !!this.token && this.token !== 'mock-jwt-token-for-development';
  }

  // Get current configuration for debugging
  getConfig(): AuthConfig {
    return {
      token: this.token.substring(0, 20) + '...', // Only show first 20 chars for security
      baseUrl: this.baseUrl,
      timeout: this.timeout
    };
  }
}

// Export singleton instance
export const authService = new AuthService();

// Export helper function for backward compatibility
export const apiCall = <T>(endpoint: string, options: RequestInit = {}): Promise<T> => {
  return authService.apiCall<T>(endpoint, options);
};

export const buildQueryString = (params: Record<string, any>): string => {
  return authService.buildQueryString(params);
};
