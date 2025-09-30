import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Calendar } from '@/components/ui/calendar';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { 
  ArrowLeft, 
  ArrowRight, 
  Calendar as CalendarIcon,
  Users,
  Settings,
  CheckCircle,
  Play,
  Eye,
  Loader2,
  Info
} from 'lucide-react';
import { CampaignCreatePayload, DryRunResult } from '@/types/campaign';
import { campaignsService } from '@/services/campaigns';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';

type WizardStep = 'basic' | 'audience' | 'review';

interface WizardData {
  name: string;
  startMode: 'now' | 'scheduled';
  scheduledStart?: Date;
  leadIds: string[];
  onePerDomain: boolean;
}

const defaultData: WizardData = {
  name: '',
  startMode: 'now',
  leadIds: [],
  onePerDomain: false
};

export default function CampaignNewSimplified() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  
  const [step, setStep] = useState<WizardStep>('basic');
  const [data, setData] = useState<WizardData>(defaultData);
  const [loading, setLoading] = useState(false);
  const [dryRunResult, setDryRunResult] = useState<DryRunResult | null>(null);

  // Handle incoming leads from URL params
  const source = searchParams.get('source');
  const leadIdsParam = searchParams.get('ids');

  useEffect(() => {
    if (source === 'leads' && leadIdsParam) {
      const ids = leadIdsParam.split(',');
      setData(prev => ({
        ...prev,
        leadIds: ids
      }));
      
      toast({
        title: 'Leads geïmporteerd',
        description: `${ids.length} leads geïmporteerd uit selectie`,
      });
    }
  }, [source, leadIdsParam, toast]);

  const updateData = (updates: Partial<WizardData>) => {
    setData(prev => ({ ...prev, ...updates }));
  };

  const validateStep = (stepName: WizardStep): boolean => {
    switch (stepName) {
      case 'basic':
        return !!data.name;
      case 'audience':
        return data.leadIds.length > 0;
      case 'review':
        return true;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (!validateStep(step)) return;
    
    const steps: WizardStep[] = ['basic', 'audience', 'review'];
    const currentIndex = steps.indexOf(step);
    if (currentIndex < steps.length - 1) {
      setStep(steps[currentIndex + 1]);
    }
  };

  const handlePrevious = () => {
    const steps: WizardStep[] = ['basic', 'audience', 'review'];
    const currentIndex = steps.indexOf(step);
    if (currentIndex > 0) {
      setStep(steps[currentIndex - 1]);
    }
  };

  const handleSubmit = async () => {
    if (!validateStep('review')) return;
    
    setLoading(true);
    try {
      const payload: CampaignCreatePayload = {
        name: data.name,
        audience: {
          mode: 'static',
          lead_ids: data.leadIds,
          exclude_suppressed: true,
          exclude_recent_days: 14,
          one_per_domain: data.onePerDomain
        },
        schedule: {
          start_mode: data.startMode,
          start_at: data.scheduledStart?.toISOString()
        }
      };
      
      const result = await campaignsService.createCampaign(payload);
      
      toast({
        title: 'Campagne aangemaakt',
        description: 'Je campagne is aangemaakt en wordt binnenkort gestart'
      });
      
      navigate(`/campaigns/${result.id}`);
    } catch (error) {
      toast({
        title: 'Fout',
        description: 'Campagne aanmaken mislukt',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const renderStepIndicator = () => (
    <Card className="p-4 shadow-card rounded-2xl mb-6">
      <div className="flex items-center justify-between">
        {[
          { key: 'basic', label: 'Basis', icon: Settings },
          { key: 'audience', label: 'Doelgroep', icon: Users },
          { key: 'review', label: 'Review & Start', icon: CheckCircle }
        ].map((stepItem, index) => {
          const StepIcon = stepItem.icon;
          const isActive = step === stepItem.key;
          const isCompleted = ['basic', 'audience', 'review'].indexOf(stepItem.key) < 
                              ['basic', 'audience', 'review'].indexOf(step);
          
          return (
            <div key={stepItem.key} className="flex items-center">
              <div className={`flex items-center gap-2 ${isActive ? 'text-primary' : isCompleted ? 'text-accent' : 'text-muted-foreground'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${
                  isActive ? 'border-primary bg-primary/10' : 
                  isCompleted ? 'border-accent bg-accent/10' : 
                  'border-muted'
                }`}>
                  <StepIcon className="w-4 h-4" />
                </div>
                <span className="font-medium hidden sm:block">{stepItem.label}</span>
              </div>
              {index < 2 && (
                <div className={`w-8 h-0.5 mx-2 ${isCompleted ? 'bg-accent' : 'bg-muted'}`} />
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );

  const renderBasicStep = () => (
    <Card className="p-6 shadow-card rounded-2xl">
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold mb-2">Campagne Basis</h2>
          <p className="text-muted-foreground">Geef je campagne een naam en kies wanneer deze start</p>
        </div>

        <div className="space-y-4">
          <div>
            <Label htmlFor="name">Campagne Naam *</Label>
            <Input
              id="name"
              value={data.name}
              onChange={(e) => updateData({ name: e.target.value })}
              placeholder="Bijv: Q1 2025 Outreach"
            />
          </div>

          <div>
            <Label>Start Timing</Label>
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <input
                  type="radio"
                  id="start-now"
                  name="startMode"
                  checked={data.startMode === 'now'}
                  onChange={() => updateData({ startMode: 'now' })}
                />
                <Label htmlFor="start-now">Nu starten (eerstvolgende slot)</Label>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="radio"
                  id="start-scheduled"
                  name="startMode"
                  checked={data.startMode === 'scheduled'}
                  onChange={() => updateData({ startMode: 'scheduled' })}
                />
                <Label htmlFor="start-scheduled">Gepland starten op:</Label>
              </div>
              
              {data.startMode === 'scheduled' && (
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        "w-[280px] justify-start text-left font-normal ml-6",
                        !data.scheduledStart && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {data.scheduledStart ? format(data.scheduledStart, "PPP", { locale: nl }) : <span>Kies een datum</span>}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={data.scheduledStart}
                      onSelect={(date) => updateData({ scheduledStart: date })}
                      initialFocus
                      className="p-3"
                    />
                  </PopoverContent>
                </Popover>
              )}
            </div>
          </div>

          {/* Info box about auto-assignment */}
          <Card className="p-4 bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
            <div className="flex gap-3">
              <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <div className="space-y-1 text-sm">
                <p className="font-semibold text-blue-900 dark:text-blue-100">Automatisch toegewezen:</p>
                <ul className="text-blue-800 dark:text-blue-200 space-y-0.5">
                  <li>• Flow/domein (eerste beschikbare)</li>
                  <li>• Templates (4 mails per lead)</li>
                  <li>• Timing (+3 werkdagen tussen mails)</li>
                  <li>• Verzendvenster (ma-vr 08:00-17:00)</li>
                </ul>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </Card>
  );

  const renderAudienceStep = () => (
    <Card className="p-6 shadow-card rounded-2xl">
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold mb-2">Doelgroep</h2>
          <p className="text-muted-foreground">Selecteer de leads voor deze campagne</p>
        </div>

        <div className="space-y-4">
          <div>
            <Label>Geselecteerde Leads</Label>
            <div className="mt-2 p-4 border border-border rounded-lg bg-muted/30">
              <div className="flex items-center justify-between">
                <span className="font-medium">{data.leadIds.length} leads geselecteerd</span>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => navigate('/leads')}
                >
                  <Users className="w-4 h-4 mr-2" />
                  Leads Beheren
                </Button>
              </div>
            </div>
          </div>

          <div>
            <Label className="text-base font-semibold mb-3 block">Auto-Filters (altijd actief)</Label>
            <Card className="p-4 bg-muted/30">
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>Suppressed leads uitgesloten</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>Bounced emails uitgesloten</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>Recent gecontacteerd (&lt; 14 dagen) uitgesloten</span>
                </div>
              </div>
            </Card>
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="one-per-domain"
              checked={data.onePerDomain}
              onCheckedChange={(checked) => updateData({ onePerDomain: !!checked })}
            />
            <Label htmlFor="one-per-domain">Maximaal één lead per domein</Label>
          </div>
        </div>
      </div>
    </Card>
  );

  const renderReviewStep = () => (
    <div className="space-y-6">
      <Card className="p-6 shadow-card rounded-2xl">
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold mb-2">Review & Start</h2>
            <p className="text-muted-foreground">Controleer je campagne instellingen</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-3">Campagne Details</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Naam:</span>
                  <span className="font-medium">{data.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Start:</span>
                  <span className="font-medium">
                    {data.startMode === 'now' ? 'Direct' : format(data.scheduledStart!, 'PPP', { locale: nl })}
                  </span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-3">Doelgroep</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Leads:</span>
                  <span className="font-medium">{data.leadIds.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">One per domain:</span>
                  <span className="font-medium">{data.onePerDomain ? 'Ja' : 'Nee'}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Auto-assigned configuration display */}
          <Card className="border-primary/20 bg-primary/5 p-4">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Auto-toegewezen Configuratie
            </h3>
            <div className="space-y-2 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-muted-foreground">Flow:</span>
                  <p className="font-medium">Eerste beschikbare domein (v1-v4)</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Planning:</span>
                  <p className="font-medium">4 mails per lead</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Timing:</span>
                  <p className="font-medium">dag 0, +3, +6, +9 (werkdagen)</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Verzendvenster:</span>
                  <p className="font-medium">ma-vr 08:00-17:00</p>
                </div>
              </div>
              <div className="pt-2 border-t border-primary/10">
                <p className="text-xs text-muted-foreground">
                  <strong>Totale mails:</strong> {data.leadIds.length * 4} over 9 werkdagen
                </p>
                <p className="text-xs text-muted-foreground">
                  <strong>Throttle:</strong> 1 mail per 20 min per domein (12 mails/uur totaal)
                </p>
              </div>
            </div>
          </Card>

          {dryRunResult && (
            <Card className="p-4 bg-muted/30">
              <h4 className="font-semibold mb-2">Dry Run Planning</h4>
              <div className="text-sm space-y-1">
                <p><strong>{dryRunResult.totalPlanned}</strong> mails gepland</p>
                <p>Verspreid over <strong>{dryRunResult.byDay.length}</strong> dagen</p>
              </div>
            </Card>
          )}
        </div>
      </Card>

      <div className="flex gap-3">
        <Button
          variant="outline"
          onClick={() => {/* TODO: Dry-run */}}
          disabled={loading}
          className="flex-1"
        >
          <Eye className="w-4 h-4 mr-2" />
          Dry Run
        </Button>
        
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              className="flex-1 bg-gradient-accent hover:shadow-glow"
              disabled={!validateStep('review')}
            >
              <Play className="w-4 h-4 mr-2" />
              Start Campagne
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Campagne Starten</AlertDialogTitle>
              <AlertDialogDescription>
                Weet je zeker dat je deze campagne wilt starten? Emails worden verzonden volgens het automatisch gegenereerde schema.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Annuleer</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleSubmit}
                className="bg-gradient-accent hover:shadow-glow"
              >
                Start Campagne
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-subtle p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/campaigns')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Terug naar Campagnes
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-foreground">Nieuwe Campagne</h1>
            <p className="text-muted-foreground">Simpel & snel - meeste instellingen zijn hard-coded</p>
          </div>
        </div>

        {renderStepIndicator()}

        {/* Step Content */}
        {step === 'basic' && renderBasicStep()}
        {step === 'audience' && renderAudienceStep()}
        {step === 'review' && renderReviewStep()}

        {/* Navigation */}
        {step !== 'review' && (
          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={step === 'basic'}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Vorige
            </Button>
            <Button
              onClick={handleNext}
              disabled={!validateStep(step)}
              className="bg-gradient-primary hover:shadow-glow"
            >
              Volgende
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
