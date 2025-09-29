import { StatsSummary, StatsQuery, StatsExportQuery } from '@/types/stats';
import { authService, buildQueryString } from './auth';

export const statsService = {
  async getStatsSummary(query: StatsQuery = {}): Promise<StatsSummary> {
    const queryString = buildQueryString({
      from: query.from,
      to: query.to,
    });

    const endpoint = `/stats/summary${queryString ? `?${queryString}` : ''}`;
    return await authService.apiCall<StatsSummary>(endpoint);
  },

  async exportStats(query: StatsExportQuery): Promise<Blob> {
    const queryString = buildQueryString({
      scope: query.scope,
      from: query.from,
      to: query.to,
      id: query.id,
    });

    const response = await fetch(`${authService.getConfig().baseUrl}/stats/export${queryString ? `?${queryString}` : ''}`, {
      method: 'GET',
      headers: authService.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.blob();
  }
};
