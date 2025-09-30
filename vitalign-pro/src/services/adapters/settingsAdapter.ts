/**
 * Settings Response Adapter
 * Normalizes API responses to consistent UI types with safe defaults
 */

export interface UiSendingWindow {
  days: string[];
  from: string;
  to: string;
}

export interface UiThrottleSettings {
  emailsPer: number;
  minutes: number;
}

export interface UiEmailInfrastructure {
  current: string;
  provider: string | null;
  providerEnabled: boolean;
  dns: {
    spf: boolean;
    dkim: boolean;
    dmarc: boolean;
  };
}

export interface UiSettings {
  timezone: string;
  window: UiSendingWindow;
  throttle: UiThrottleSettings;
  domains: string[];
  unsubscribeText: string;
  unsubscribeUrl: string;
  trackingPixelEnabled: boolean;
  emailInfra: UiEmailInfrastructure;
  gracePeriodTo?: string;
  dailyCapPerDomain?: number;
  timezoneEditable?: boolean;
}

/**
 * Ensure array type
 */
function ensureArray<T>(value: any): T[] {
  return Array.isArray(value) ? value : [];
}

/**
 * Convert API response to UI Settings
 */
export function toUiSettings(apiResponse: any): UiSettings {
  const data = apiResponse || {};

  // Safe window extraction
  const windowData = data.window || {};
  const window: UiSendingWindow = {
    days: ensureArray<string>(windowData.days),
    from: windowData.from || '08:00',
    to: windowData.to || '17:00',
  };

  // Safe throttle extraction
  const throttleData = data.throttle || {};
  const throttle: UiThrottleSettings = {
    emailsPer: throttleData.emailsPer ?? throttleData.emails_per ?? 1,
    minutes: throttleData.minutes ?? 20,
  };

  // Safe email infra extraction
  const infraData = data.emailInfra || data.email_infra || {};
  const dnsData = infraData.dns || {};
  const emailInfra: UiEmailInfrastructure = {
    current: infraData.current || 'SMTP',
    provider: infraData.provider || null,
    providerEnabled: infraData.providerEnabled ?? infraData.provider_enabled ?? false,
    dns: {
      spf: dnsData.spf ?? false,
      dkim: dnsData.dkim ?? false,
      dmarc: dnsData.dmarc ?? false,
    },
  };

  return {
    timezone: data.timezone || 'Europe/Amsterdam',
    window,
    throttle,
    domains: ensureArray<string>(data.domains),
    unsubscribeText: data.unsubscribeText ?? data.unsubscribe_text ?? 'Uitschrijven',
    unsubscribeUrl: data.unsubscribeUrl ?? data.unsubscribe_url ?? '',
    trackingPixelEnabled: data.trackingPixelEnabled ?? data.tracking_pixel_enabled ?? true,
    emailInfra,
    gracePeriodTo: data.gracePeriodTo ?? data.grace_period_to ?? undefined,
    dailyCapPerDomain: data.dailyCapPerDomain ?? data.daily_cap_per_domain ?? undefined,
    timezoneEditable: data.timezoneEditable ?? data.timezone_editable ?? undefined,
  };
}
