export interface SendingWindow {
  days: string[];
  from: string;
  to: string;
}

export interface ThrottleSettings {
  emailsPer: number;
  minutes: number;
}

export interface EmailInfrastructure {
  current: 'SMTP';
  provider: 'Postmark' | 'SES' | null;
  providerEnabled: boolean;
  dns: {
    spf: boolean;
    dkim: boolean;
    dmarc: boolean;
  };
}

export interface Settings {
  timezone: string;
  window: SendingWindow;
  throttle: ThrottleSettings;
  domains: string[];
  unsubscribeText: string;
  unsubscribeUrl: string;
  trackingPixelEnabled: boolean;
  emailInfra: EmailInfrastructure;
  // Hard-coded policy fields
  gracePeriodTo?: string;
  dailyCapPerDomain?: number;
  timezoneEditable?: boolean;
}

export interface SettingsUpdateRequest {
  unsubscribeText?: string;
  trackingPixelEnabled?: boolean;
}

export interface SettingsResponse {
  ok: boolean;
  message?: string;
}
