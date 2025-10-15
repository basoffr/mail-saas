import { 
  Campaign, 
  CampaignDetail, 
  CampaignCreatePayload, 
  CampaignMessage, 
  DryRunResult,
  CampaignControlResponse,
  StopLeadRequest,
  StopLeadResponse,
  ScheduleResponse
} from '@/types/campaign';
import { authService } from './auth';

export const campaignsService = {
  async getCampaigns(): Promise<{ items: Campaign[]; total: number }> {
    return await authService.apiCall<{ items: Campaign[]; total: number }>('/campaigns');
  },

  async createCampaign(payload: CampaignCreatePayload): Promise<{ id: string }> {
    // V2.2: Debug logging
    console.log('Creating campaign with payload:', payload);
    const leadCount = payload.audience?.lead_ids?.length || 0;
    console.log(`Creating campaign with ${leadCount} leads (${leadCount * 4} messages will be scheduled)`);
    
    try {
      // V2.2: Extended timeout for large campaigns (2100 leads × 4 = 8400 messages!)
      // Use custom timeout: 2 minutes for campaigns
      const controller = new AbortController();
      const timeoutMs = 120000; // 120 seconds
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
      
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
      const token = await authService.getToken();
      
      const response = await fetch(`${baseUrl}/campaigns`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      
      const data = await response.json();
      const result = data.data || data;
      
      console.log('Campaign created successfully:', result);
      return result;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error(`Campaign creation timeout after 120 seconds. This may indicate a backend issue with ${leadCount} leads.`);
      }
      console.error('Campaign creation failed in service:', error);
      throw error;
    }
  },

  async getCampaign(id: string): Promise<CampaignDetail | null> {
    try {
      return await authService.apiCall<CampaignDetail>(`/campaigns/${id}`);
    } catch (error) {
      if (error instanceof Error && error.message.includes('404')) {
        return null;
      }
      throw error;
    }
  },

  async pauseCampaign(id: string): Promise<{ ok: boolean }> {
    return await authService.apiCall<{ ok: boolean }>(`/campaigns/${id}/pause`, {
      method: 'POST',
    });
  },

  async resumeCampaign(id: string): Promise<{ ok: boolean }> {
    return await authService.apiCall<{ ok: boolean }>(`/campaigns/${id}/resume`, {
      method: 'POST',
    });
  },

  async stopCampaign(id: string): Promise<{ ok: boolean }> {
    return await authService.apiCall<{ ok: boolean }>(`/campaigns/${id}/stop`, {
      method: 'POST',
    });
  },

  async duplicateCampaign(id: string): Promise<Campaign> {
    return await authService.apiCall<Campaign>(`/campaigns/${id}/duplicate`, {
      method: 'POST',
    });
  },

  async dryRunCampaign(id: string): Promise<DryRunResult> {
    return await authService.apiCall<DryRunResult>(`/campaigns/${id}/dry-run`);
  },

  async getCampaignMessages(
    campaignId: string, 
    page: number = 1, 
    pageSize: number = 100
  ): Promise<{ items: CampaignMessage[]; total: number }> {
    const response = await authService.apiCall<{ items: CampaignMessage[]; total: number }>(
      `/campaigns/${campaignId}/messages?page=${page}&page_size=${pageSize}`
    );
    return response;
  },

  async resendMessage(messageId: string): Promise<{ ok: boolean }> {
    return await authService.apiCall<{ ok: boolean }>(`/messages/${messageId}/resend`, {
      method: 'POST',
    });
  },

  // V2.2: Campaign Controls
  async deleteCampaign(id: string): Promise<CampaignControlResponse> {
    return await authService.apiCall<CampaignControlResponse>(`/campaigns/${id}`, {
      method: 'DELETE',
    });
  },

  async stopLeadFlow(campaignId: string, leadId: string, request: StopLeadRequest): Promise<StopLeadResponse> {
    return await authService.apiCall<StopLeadResponse>(`/campaigns/${campaignId}/leads/${leadId}/stop`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // V2.2: Scheduling View
  async getSchedule(campaignId: string, options?: {
    day?: number;       // V2.3: Day number for per-day pagination
    limit?: number;
    domain?: string;
    fromTs?: string;
  }): Promise<ScheduleResponse> {
    const params = new URLSearchParams();
    if (options?.day) params.append('day', options.day.toString());
    if (options?.limit) params.append('limit', options.limit.toString());
    if (options?.domain) params.append('domain', options.domain);
    if (options?.fromTs) params.append('from_ts', options.fromTs);
    
    const url = `/campaigns/${campaignId}/schedule${params.toString() ? `?${params.toString()}` : ''}`;
    return await authService.apiCall<ScheduleResponse>(url);
  }
};