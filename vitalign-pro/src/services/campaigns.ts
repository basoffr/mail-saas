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
    return await authService.apiCall<{ id: string }>('/campaigns', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
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

  async getCampaignMessages(campaignId: string): Promise<CampaignMessage[]> {
    const response = await authService.apiCall<{ items: CampaignMessage[]; total: number }>(
      `/campaigns/${campaignId}/messages`
    );
    return response.items || [];
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
    limit?: number;
    domain?: string;
    fromTs?: string;
  }): Promise<ScheduleResponse> {
    const params = new URLSearchParams();
    if (options?.limit) params.append('limit', options.limit.toString());
    if (options?.domain) params.append('domain', options.domain);
    if (options?.fromTs) params.append('from_ts', options.fromTs);
    
    const url = `/campaigns/${campaignId}/schedule${params.toString() ? `?${params.toString()}` : ''}`;
    return await authService.apiCall<ScheduleResponse>(url);
  }
};