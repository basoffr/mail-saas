import { 
  Campaign, 
  CampaignDetail, 
  CampaignCreatePayload, 
  CampaignMessage, 
  DryRunResult 
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
  }
};