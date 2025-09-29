import { Settings, SettingsUpdateRequest } from '@/types/settings';
import { authService } from './auth';

export const settingsService = {
  async getSettings(): Promise<Settings> {
    return await authService.apiCall<Settings>('/settings');
  },

  async updateSettings(updates: SettingsUpdateRequest): Promise<Settings> {
    return await authService.apiCall<Settings>('/settings', {
      method: 'POST',
      body: JSON.stringify(updates),
    });
  }
};
