/**
 * Settings Response Adapter
 * Normalizes API responses to consistent UI types with safe defaults
 */

import { asArray, asBool, asString, pick } from '@/lib/safe';

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

export interface UiDomainAlias {
  email: string;
  name: string;
  active: boolean;
}

export interface UiDomainConfig {
  domain: string;
  displayName: string;
  smtpHost: string;
  smtpPort: number;
  useTls: boolean;
  aliases: UiDomainAlias[];
  dailyLimit: number;
  throttleMinutes: number;
  dnsStatus: {
    spf: string;
    dkim: string;
    dmarc: string;
  };
  reputationScore: string;
  active: boolean;
}

export interface UiSettings {
  timezone: string;
  window: UiSendingWindow;
  throttle: UiThrottleSettings;
  domains: string[];
  domainsConfig?: UiDomainConfig[];
  unsubscribeText: string;
  unsubscribeUrl: string;
  trackingPixelEnabled: boolean;
  emailInfra: UiEmailInfrastructure;
  gracePeriodTo?: string;
  dailyCapPerDomain?: number;
  timezoneEditable?: boolean;
}

/**
 * Convert API response to UI Settings with runtime validation
 */
export function toUiSettings(apiResponse: any): UiSettings {
  const data = apiResponse || {};

  // Window normalization (handles both camel/snake case)
  const windowData = pick(data, ['window', 'sending_window', 'sendingWindow'], {});
  const windowDays = asArray<string>(pick(windowData, ['days', 'Days'], []));
  const windowFrom = asString(pick(windowData, ['from', 'start', 'start_at', 'startAt'], '08:00'));
  const windowTo = asString(pick(windowData, ['to', 'end', 'end_at', 'endAt'], '17:00'));
  
  const window: UiSendingWindow = {
    days: windowDays,
    from: windowFrom,
    to: windowTo,
  };

  // Throttle normalization
  const throttleData = pick(data, ['throttle', 'throttleSettings'], {});
  const throttle: UiThrottleSettings = {
    emailsPer: pick(throttleData, ['emailsPer', 'emails_per', 'perInterval'], 1) as number,
    minutes: pick(throttleData, ['minutes', 'Minutes', 'interval'], 20) as number,
  };

  // Email infra normalization
  const infraData = pick(data, ['emailInfra', 'email_infra', 'emailInfrastructure'], {});
  const dnsData = pick(infraData, ['dns', 'DNS', 'dns_status', 'dnsStatus'], {});
  
  const emailInfra: UiEmailInfrastructure = {
    current: asString(pick(infraData, ['current', 'provider', 'currentProvider'], 'SMTP')),
    provider: pick(infraData, ['provider', 'providerName'], null),
    providerEnabled: asBool(pick(infraData, ['providerEnabled', 'provider_enabled'], false)),
    dns: {
      spf: asBool(pick(dnsData, ['spf', 'SPF'], false)),
      dkim: asBool(pick(dnsData, ['dkim', 'DKIM'], false)),
      dmarc: asBool(pick(dnsData, ['dmarc', 'DMARC'], false)),
    },
  };

  // Domains normalization
  const domains = asArray<string>(pick(data, ['domains', 'Domains', 'domainList'], []));
  
  // Domains config normalization (optional extended configuration)
  const domainsConfigData = pick(data, ['domainsConfig', 'domains_config'], null);
  let domainsConfig: UiDomainConfig[] | undefined = undefined;
  
  if (domainsConfigData && Array.isArray(domainsConfigData)) {
    domainsConfig = domainsConfigData.map((dc: any) => ({
      domain: asString(pick(dc, ['domain'], '')),
      displayName: asString(pick(dc, ['displayName', 'display_name'], '')),
      smtpHost: asString(pick(dc, ['smtpHost', 'smtp_host'], '')),
      smtpPort: pick(dc, ['smtpPort', 'smtp_port'], 587) as number,
      useTls: asBool(pick(dc, ['useTls', 'use_tls'], true)),
      aliases: asArray(pick(dc, ['aliases'], [])).map((alias: any) => ({
        email: asString(pick(alias, ['email'], '')),
        name: asString(pick(alias, ['name'], '')),
        active: asBool(pick(alias, ['active'], false))
      })),
      dailyLimit: pick(dc, ['dailyLimit', 'daily_limit'], 1000) as number,
      throttleMinutes: pick(dc, ['throttleMinutes', 'throttle_minutes'], 20) as number,
      dnsStatus: {
        spf: asString(pick(pick(dc, ['dnsStatus', 'dns_status'], {}), ['spf', 'SPF'], 'unchecked')),
        dkim: asString(pick(pick(dc, ['dnsStatus', 'dns_status'], {}), ['dkim', 'DKIM'], 'unchecked')),
        dmarc: asString(pick(pick(dc, ['dnsStatus', 'dns_status'], {}), ['dmarc', 'DMARC'], 'unchecked'))
      },
      reputationScore: asString(pick(dc, ['reputationScore', 'reputation_score'], 'unknown')),
      active: asBool(pick(dc, ['active'], true))
    }));
  }

  // Text fields
  const unsubscribeText = asString(pick(data, ['unsubscribeText', 'unsubscribe_text'], 'Uitschrijven'));
  const unsubscribeUrl = asString(pick(data, ['unsubscribeUrl', 'unsubscribe_url'], ''));
  
  // Boolean fields
  const trackingPixelEnabled = asBool(pick(data, ['trackingPixelEnabled', 'tracking_pixel_enabled'], true));

  return {
    timezone: asString(pick(data, ['timezone', 'timeZone', 'tz'], 'Europe/Amsterdam')),
    window,
    throttle,
    domains,
    domainsConfig,
    unsubscribeText,
    unsubscribeUrl,
    trackingPixelEnabled,
    emailInfra,
    gracePeriodTo: pick(data, ['gracePeriodTo', 'grace_period_to'], undefined),
    dailyCapPerDomain: pick(data, ['dailyCapPerDomain', 'daily_cap_per_domain'], undefined),
    timezoneEditable: pick(data, ['timezoneEditable', 'timezone_editable'], undefined),
  };
}
