import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { 
  Settings as SettingsIcon, 
  Clock, 
  Mail, 
  Shield, 
  Server,
  Save,
  Loader2
} from 'lucide-react';
import { SettingsCard } from '@/components/settings/SettingsCard';
import { CopyField } from '@/components/settings/CopyField';
import { DnsChecklist } from '@/components/settings/DnsChecklist';
import { ImapAccountsSection } from '@/components/settings/ImapAccountsSection';
import { settingsService } from '@/services/settings';
import { Settings as SettingsType, SettingsUpdateRequest } from '@/types/settings';
import { useToast } from '@/hooks/use-toast';

const Settings = () => {
  const { toast } = useToast();
  const [settings, setSettings] = useState<SettingsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  
  // Form state for editable fields
  const [unsubscribeText, setUnsubscribeText] = useState('');
  const [trackingPixelEnabled, setTrackingPixelEnabled] = useState(true);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const data = await settingsService.getSettings();
      setSettings(data);
      setUnsubscribeText(data?.unsubscribeText || 'Uitschrijven');
      setTrackingPixelEnabled(data?.trackingPixelEnabled ?? true);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load settings',
        variant: 'destructive'
      });
      setSettings(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings) return;
    
    setSaving(true);
    try {
      const updates: SettingsUpdateRequest = {};
      
      if (unsubscribeText !== settings.unsubscribeText) {
        updates.unsubscribeText = unsubscribeText;
      }
      
      if (trackingPixelEnabled !== settings.trackingPixelEnabled) {
        updates.trackingPixelEnabled = trackingPixelEnabled;
      }
      
      const response = await settingsService.updateSettings(updates);
      
      // Update local settings with response
      setSettings(response);
      setUnsubscribeText(response.unsubscribeText);
      setTrackingPixelEnabled(response.trackingPixelEnabled);
      setHasChanges(false);
      
      toast({
        title: 'Opgeslagen!',
        description: 'Instellingen zijn succesvol opgeslagen',
      });
    } catch (error) {
      toast({
        title: 'Fout bij opslaan',
        description: 'Er is een onverwachte fout opgetreden',
        variant: 'destructive'
      });
    } finally {
      setSaving(false);
    }
  };

  const handleCopy = async (value: string): Promise<boolean> => {
    try {
      await navigator.clipboard.writeText(value);
      return true;
    } catch (error) {
      return false;
    }
  };

  // Check for changes
  useEffect(() => {
    if (!settings) return;
    
    const hasTextChange = unsubscribeText !== settings.unsubscribeText;
    const hasPixelChange = trackingPixelEnabled !== settings.trackingPixelEnabled;
    
    setHasChanges(hasTextChange || hasPixelChange);
  }, [settings, unsubscribeText, trackingPixelEnabled]);

  useEffect(() => {
    fetchSettings();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-subtle p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <div className="flex items-center gap-3">
              <SettingsIcon className="h-6 w-6 text-primary" />
              <h1 className="text-3xl font-bold text-foreground">Instellingen</h1>
            </div>
            <p className="text-muted-foreground">Beheer je email configuratie en systeem instellingen</p>
          </div>
          
          {hasChanges && (
            <Button
              onClick={handleSave}
              disabled={saving}
              className="bg-gradient-primary hover:shadow-glow gap-2"
            >
              {saving ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              Opslaan
            </Button>
          )}
        </div>

        {/* Verzendregels (Hard-coded) */}
        <SettingsCard
          title="Verzendregels"
          description="Hard-coded verzendregels - Deze waarden zijn vastgelegd in de backend"
          loading={loading}
        >
          {settings && (
            <>
              <div className="bg-muted/50 p-4 rounded-lg border-l-4 border-orange-500 mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="h-4 w-4 text-orange-500" />
                  <span className="text-sm font-medium text-orange-700">Hard-coded Policy</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  Deze waarden zijn hard-coded in de backend en kunnen niet worden gewijzigd via de UI.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      Tijdzone
                    </Label>
                    <Badge variant="secondary" className="font-mono">
                      {settings.timezone}
                    </Badge>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Werkdagen</Label>
                    {settings?.window?.days && Array.isArray(settings.window.days) ? (
                      <div className="flex flex-wrap gap-1">
                        {settings.window.days.map((day) => (
                          <Badge key={day} variant="outline" className="text-xs">
                            {day}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">Geen werkdagen geconfigureerd</p>
                    )}
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Verzendvenster</Label>
                    <Badge variant="secondary" className="font-mono">
                      {settings.window?.from} - {settings.window?.to}
                    </Badge>
                    <p className="text-xs text-muted-foreground">
                      Laatste slot: 16:40 (17:00 exclusief)
                    </p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Grace Period</Label>
                    <Badge variant="secondary" className="font-mono">
                      Tot {settings.gracePeriodTo || '18:00'}
                    </Badge>
                    <p className="text-xs text-muted-foreground">
                      Uitloop toegestaan tot 18:00
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Throttle</Label>
                    <Badge variant="secondary" className="font-mono">
                      {settings.throttle?.emailsPer || 1} email / {settings.throttle?.minutes || 20} min
                    </Badge>
                    <p className="text-xs text-muted-foreground">
                      Per domein throttling
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Dagcap per Domein</Label>
                    <Badge variant="secondary" className="font-mono">
                      {settings.dailyCapPerDomain || 27} emails/dag
                    </Badge>
                    <p className="text-xs text-muted-foreground">
                      27 slots van 20 minuten (08:00-16:40)
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="space-y-2 mt-6">
                <Label>Domeinen & Flows</Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(settings?.domains || []).map((domain, index) => (
                    <div key={domain} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant="outline" className="font-mono text-xs">
                          {domain}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          v{index + 1}
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        M1+M2: Christian • M3+M4: Victor • +3 werkdagen interval
                      </div>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-muted-foreground">
                  Domeinbeheer wordt later beschikbaar (read-only in MVP)
                </p>
              </div>
            </>
          )}
        </SettingsCard>

        {/* Unsubscribe & Tracking */}
        <SettingsCard
          title="Unsubscribe & Tracking"
          description="Configureer unsubscribe opties en tracking instellingen"
          loading={loading}
        >
          {settings && (
            <>
              <div className="space-y-2">
                <Label htmlFor="unsubscribe-text">Unsubscribe Tekst</Label>
                <Input
                  id="unsubscribe-text"
                  value={unsubscribeText}
                  onChange={(e) => setUnsubscribeText(e.target.value)}
                  placeholder="Uitschrijven"
                  maxLength={50}
                />
                <p className="text-sm text-muted-foreground">
                  Deze tekst wordt getoond als unsubscribe link in emails (max. 50 karakters)
                </p>
              </div>
              
              <CopyField
                label="Unsubscribe URL"
                value={settings.unsubscribeUrl}
                onCopy={handleCopy}
              />
              
              <div className="flex items-center justify-between p-4 rounded-lg border bg-card">
                <div className="space-y-1">
                  <Label htmlFor="tracking-pixel">Tracking Pixel</Label>
                  <p className="text-sm text-muted-foreground">
                    Voegt een 1×1 pixel toe om email opens te meten
                  </p>
                </div>
                <Switch
                  id="tracking-pixel"
                  checked={trackingPixelEnabled}
                  onCheckedChange={setTrackingPixelEnabled}
                />
              </div>
            </>
          )}
        </SettingsCard>

        {/* E-mail Infrastructuur */}
        <SettingsCard
          title="E-mail Infrastructuur"
          description="Huidige email provider en DNS configuratie"
          loading={loading}
        >
          {settings && (
            <>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <Server className="h-4 w-4" />
                    Huidig Kanaal
                  </Label>
                  <div className="flex items-center gap-2">
                    <Badge variant="default" className="font-medium">
                      SMTP (Vimexx)
                    </Badge>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label>Toekomstige Providers</Label>
                  <div className="flex gap-2">
                    <Badge variant="secondary" className="opacity-50">
                      Postmark (disabled in MVP)
                    </Badge>
                    <Badge variant="secondary" className="opacity-50">
                      AWS SES (disabled in MVP)
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Provider switching wordt later beschikbaar
                  </p>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  DNS Configuratie
                </Label>
                <DnsChecklist status={settings?.emailInfra?.dns ?? { spf: false, dkim: false, dmarc: false }} />
              </div>
            </>
          )}
        </SettingsCard>

        {/* IMAP Accounts */}
        <SettingsCard
          title="Inbox (IMAP)"
          description="Configureer IMAP accounts voor het ophalen van inkomende berichten"
          loading={loading}
        >
          <ImapAccountsSection />
        </SettingsCard>
      </div>
    </div>
  );
};

export default Settings;
