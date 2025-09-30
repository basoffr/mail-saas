import { 
  InboxMessageOut, 
  InboxQuery, 
  MailAccountOut, 
  FetchStartResponse,
  MarkReadResponse 
} from '@/types/inbox';
import { authService, buildQueryString } from './auth';

export const inboxService = {
  async startFetch(): Promise<FetchStartResponse> {
    return await authService.apiCall<FetchStartResponse>('/inbox/fetch', {
      method: 'POST',
    });
  },

  async getMessages(query: InboxQuery = {}): Promise<{ items: InboxMessageOut[]; total: number }> {
    const queryString = buildQueryString({
      account_id: query.accountId,
      campaign_id: query.campaignId,
      unread: query.unread,
      q: query.q,
      from: query.from,
      to: query.to,
      page: query.page,
      page_size: query.pageSize,
    });

    const endpoint = `/inbox/messages${queryString ? `?${queryString}` : ''}`;
    return await authService.apiCall<{ items: InboxMessageOut[]; total: number }>(endpoint);
  },

  async markAsRead(messageId: string): Promise<MarkReadResponse> {
    return await authService.apiCall<MarkReadResponse>(`/inbox/messages/${messageId}/mark-read`, {
      method: 'POST',
    });
  },

  async getAccounts(): Promise<MailAccountOut[]> {
    return await authService.apiCall<MailAccountOut[]>('/settings/inbox/accounts');
  },

  async testAccount(accountId: string): Promise<{ ok: boolean; message: string }> {
    return await authService.apiCall<{ ok: boolean; message: string }>(`/settings/inbox/accounts/${accountId}/test`, {
      method: 'POST',
    });
  },

  async toggleAccount(accountId: string): Promise<{ ok: boolean }> {
    return await authService.apiCall<{ ok: boolean }>(`/settings/inbox/accounts/${accountId}/toggle`, {
      method: 'POST',
    });
  }
};
