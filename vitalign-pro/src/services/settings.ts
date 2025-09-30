import { Settings, SettingsUpdateRequest } from '@/types/settings';
import { authService } from './auth';
import { toUiSettings } from './adapters/settingsAdapter';

export const settingsService = {
  async getSettings(): Promise<Settings> {
    const response = await authService.apiCall<any>('/settings');
    return toUiSettings(response) as any;
  },

  async updateSettings(updates: SettingsUpdateRequest): Promise<Settings> {
    const response = await authService.apiCall<any>('/settings', {
      method: 'POST',
      body: JSON.stringify(updates),
    });
    return toUiSettings(response) as any;
  }
};
