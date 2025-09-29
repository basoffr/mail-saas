import { Settings, SettingsUpdateRequest, SettingsResponse } from '@/types/settings';

// Mock settings data
const mockSettings: Settings = {
  timezone: 'Europe/Amsterdam',
  window: {
    days: ['ma', 'di', 'wo', 'do', 'vr'],
    from: '08:00',
    to: '17:00'
  },
  throttle: {
    emailsPer: 1,
    minutes: 20
  },
  domains: [
    'punthelder.nl',
    'vitalign.nl',
    'innovate-solutions.com',
    'techpartners.eu'
  ],
  unsubscribeText: 'Uitschrijven',
  unsubscribeUrl: 'https://mail.punthelder.nl/unsubscribe?token=abc123def456',
  trackingPixelEnabled: true,
  emailInfra: {
    current: 'SMTP',
    provider: null,
    providerEnabled: false,
    dns: {
      spf: true,
      dkim: true,
      dmarc: false
    }
  }
};

// Simulate API delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

class SettingsService {
  private settings: Settings = { ...mockSettings };

  async getSettings(): Promise<Settings> {
    await delay(200); // Simulate API call
    return { ...this.settings };
  }

  async updateSettings(updates: SettingsUpdateRequest): Promise<SettingsResponse> {
    await delay(300); // Simulate API call
    
    try {
      // Validate updates
      if (updates.unsubscribeText !== undefined) {
        if (updates.unsubscribeText.length < 1 || updates.unsubscribeText.length > 50) {
          return {
            ok: false,
            message: 'Unsubscribe tekst moet tussen 1 en 50 karakters zijn'
          };
        }
        this.settings.unsubscribeText = updates.unsubscribeText;
      }

      if (updates.trackingPixelEnabled !== undefined) {
        this.settings.trackingPixelEnabled = updates.trackingPixelEnabled;
      }

      return {
        ok: true,
        message: 'Instellingen succesvol opgeslagen'
      };
    } catch (error) {
      return {
        ok: false,
        message: 'Er is een fout opgetreden bij het opslaan van de instellingen'
      };
    }
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
  getProviderStatus(): { label: string; variant: 'default' | 'secondary' } {
    return {
      label: this.settings.emailInfra.current,
      variant: 'default'
    };
  }

  // Format sending window for display
  formatSendingWindow(): string {
    const { days, from, to } = this.settings.window;
    return `${days.join('–')}, ${from}–${to}`;
  }

  // Format throttle for display
  formatThrottle(): string {
    const { emailsPer, minutes } = this.settings.throttle;
    return `${emailsPer} email / ${minutes} min / per domein`;
  }
}

export const settingsService = new SettingsService();
