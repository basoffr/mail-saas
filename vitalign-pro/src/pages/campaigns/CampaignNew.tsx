import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import { Calendar } from '@/components/ui/calendar';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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
  Filter,
  Settings,
  CheckCircle,
  AlertTriangle,
  Play,
  Eye,
  Loader2
} from 'lucide-react';
import { CampaignCreatePayload, DryRunResult } from '@/types/campaign';
import { Template } from '@/types/lead';
import { campaignsService } from '@/services/campaigns';
import { templatesService } from '@/services/templates';
import { leadsService } from '@/services/leads';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';

type WizardStep = 'basic' | 'target' | 'rules' | 'review';

interface WizardData {
  name: string;
  templateId: string;
  startType: 'now' | 'scheduled';
  scheduledStart?: Date;
  followUp: {
    enabled: boolean;
    days: number;
    attachmentRequired: boolean;
  };
  targetType: 'filter' | 'static';
  leadIds: string[];
  filters: any;
  dedupe: {
    suppressBounced: boolean;
    contactedLastDays: number;
    onePerDomain: boolean;
  };
  domains: string[];
  throttle: {
    perHour: number;
    windowStart: string;
    windowEnd: string;
    weekdays: boolean;
  };
  retry: {
    maxAttempts: number;
    backoffHours: number;
  };
}

const defaultData: WizardData = {
  name: '',
  templateId: '',
  startType: 'now',
  followUp: {
    enabled: false,
    days: 3,
    attachmentRequired: false
  },
  targetType: 'filter',
  leadIds: [],
  filters: {},
  dedupe: {
    suppressBounced: true,
    contactedLastDays: 14,
    onePerDomain: false
  },
  domains: ['com', 'org', 'net', 'io'],
  throttle: {
    perHour: 50,
    windowStart: '08:00',
    windowEnd: '17:00',
    weekdays: true
  },
  retry: {
    maxAttempts: 3,
    backoffHours: 24
  }
};

export default function CampaignNew() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  
  const [step, setStep] = useState<WizardStep>('basic');
  const [data, setData] = useState<WizardData>(defaultData);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(false);
  const [targetCount, setTargetCount] = useState(0);
  const [dryRunResult, setDryRunResult] = useState<DryRunResult | null>(null);

  // Handle incoming leads from URL params
  const source = searchParams.get('source');
  const leadIdsParam = searchParams.get('ids');

  useEffect(() => {
    fetchTemplates();
  }, []);

  useEffect(() => {
    if (source === 'leads' && leadIdsParam) {
      const ids = leadIdsParam.split(',');
      setData(prev => ({
        ...prev,
        targetType: 'static',
        leadIds: ids
      }));
      setTargetCount(ids.length);
      
      toast({
        title: 'Leads imported',
        description: `${ids.length} leads imported from selection`,
      });
    }
  }, [source, leadIdsParam, toast]);

  const fetchTemplates = async () => {
    try {
      const response = await templatesService.getTemplates();
      setTemplates(response.items);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load templates',
        variant: 'destructive'
      });
    }
  };

  const updateData = (updates: Partial<WizardData>) => {
    setData(prev => ({ ...prev, ...updates }));
  };

  const validateStep = (stepName: WizardStep): boolean => {
    switch (stepName) {
      case 'basic':
        return !!(data.name && data.templateId);
      case 'target':
        return data.targetType === 'static' ? data.leadIds.length > 0 : true;
      case 'rules':
        return data.domains.length > 0;
      case 'review':
        return true;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (!validateStep(step)) return;
    
    const steps: WizardStep[] = ['basic', 'target', 'rules', 'review'];
    const currentIndex = steps.indexOf(step);
    if (currentIndex < steps.length - 1) {
      setStep(steps[currentIndex + 1]);
    }
  };

  const handlePrevious = () => {
    const steps: WizardStep[] = ['basic', 'target', 'rules', 'review'];
    const currentIndex = steps.indexOf(step);
    if (currentIndex > 0) {
      setStep(steps[currentIndex - 1]);
    }
  };

  const handleDryRun = async () => {
    setLoading(true);
    try {
      // Create a temporary campaign for dry run
      const tempPayload: CampaignCreatePayload = {
        name: data.name,
        templateId: data.templateId,
        startType: data.startType,
        scheduledStart: data.scheduledStart,
        followUp: data.followUp,
        targetType: data.targetType,
        leadIds: data.leadIds,
        filters: data.filters,
        dedupe: data.dedupe,
        domains: data.domains,
        throttle: data.throttle,
        retry: data.retry
      };
      
      // Mock dry run - in reality this would be a different endpoint
      const result: DryRunResult = {
        totalPlanned: targetCount,
        byDay: [
          { date: '2024-01-22', planned: Math.floor(targetCount * 0.2) },
          { date: '2024-01-23', planned: Math.floor(targetCount * 0.25) },
          { date: '2024-01-24', planned: Math.floor(targetCount * 0.25) },
          { date: '2024-01-25', planned: Math.floor(targetCount * 0.2) },
          { date: '2024-01-26', planned: Math.floor(targetCount * 0.1) }
        ],
        warnings: [
          'Some leads may be missing required template variables',
          '3 leads have bounced emails in the last 30 days'
        ]
      };
      
      setDryRunResult(result);
      
      toast({
        title: 'Dry run completed',
        description: `${result.totalPlanned} emails planned for sending`
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to run dry run analysis',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!validateStep('review')) return;
    
    setLoading(true);
    try {
      const payload: CampaignCreatePayload = {
        name: data.name,
        templateId: data.templateId,
        startType: data.startType,
        scheduledStart: data.scheduledStart,
        followUp: data.followUp,
        targetType: data.targetType,
        leadIds: data.leadIds,
        filters: data.filters,
        dedupe: data.dedupe,
        domains: data.domains,
        throttle: data.throttle,
        retry: data.retry
      };
      
      const result = await campaignsService.createCampaign(payload);
      
      toast({
        title: 'Campaign created successfully',
        description: 'Your campaign has been created and will start soon'
      });
      
      navigate(`/campaigns/${result.id}`);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create campaign',
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
          { key: 'basic', label: 'Basic Info', icon: Settings },
          { key: 'target', label: 'Target Group', icon: Users },
          { key: 'rules', label: 'Send Rules', icon: Filter },
          { key: 'review', label: 'Review & Start', icon: CheckCircle }
        ].map((stepItem, index) => {
          const StepIcon = stepItem.icon;
          const isActive = step === stepItem.key;
          const isCompleted = ['basic', 'target', 'rules', 'review'].indexOf(stepItem.key) < 
                              ['basic', 'target', 'rules', 'review'].indexOf(step);
          
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
              {index < 3 && (
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
          <h2 className="text-2xl font-bold mb-2">Basic Campaign Info</h2>
          <p className="text-muted-foreground">Set up the basic details for your campaign</p>
        </div>

        <div className="space-y-4">
          <div>
            <Label htmlFor="name">Campaign Name *</Label>
            <Input
              id="name"
              value={data.name}
              onChange={(e) => updateData({ name: e.target.value })}
              placeholder="Enter campaign name..."
            />
          </div>

          <div>
            <Label htmlFor="template">Email Template *</Label>
            <Select
              value={data.templateId}
              onValueChange={(value) => updateData({ templateId: value })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select template..." />
              </SelectTrigger>
              <SelectContent className="bg-popover border border-border">
                {templates.map(template => (
                  <SelectItem key={template.id} value={template.id}>
                    {template.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Start Time</Label>
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <input
                  type="radio"
                  id="start-now"
                  name="startType"
                  checked={data.startType === 'now'}
                  onChange={() => updateData({ startType: 'now' })}
                />
                <Label htmlFor="start-now">Start immediately</Label>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="radio"
                  id="start-scheduled"
                  name="startType"
                  checked={data.startType === 'scheduled'}
                  onChange={() => updateData({ startType: 'scheduled' })}
                />
                <Label htmlFor="start-scheduled">Schedule for later</Label>
              </div>
              
              {data.startType === 'scheduled' && (
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
                      {data.scheduledStart ? format(data.scheduledStart, "PPP") : <span>Pick a date</span>}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={data.scheduledStart}
                      onSelect={(date) => updateData({ scheduledStart: date })}
                      initialFocus
                      className="p-3 pointer-events-auto"
                    />
                  </PopoverContent>
                </Popover>
              )}
            </div>
          </div>

          <div>
            <div className="flex items-center space-x-2 mb-3">
              <Switch
                checked={data.followUp.enabled}
                onCheckedChange={(checked) => updateData({
                  followUp: { ...data.followUp, enabled: checked }
                })}
              />
              <Label>Enable follow-up sequence</Label>
            </div>
            
            {data.followUp.enabled && (
              <div className="ml-6 space-y-3">
                <div>
                  <Label htmlFor="followup-days">Days after initial email</Label>
                  <Input
                    id="followup-days"
                    type="number"
                    value={data.followUp.days}
                    onChange={(e) => updateData({
                      followUp: { ...data.followUp, days: parseInt(e.target.value) || 0 }
                    })}
                    className="w-32"
                  />
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    checked={data.followUp.attachmentRequired}
                    onCheckedChange={(checked) => updateData({
                      followUp: { ...data.followUp, attachmentRequired: !!checked }
                    })}
                  />
                  <Label>Only send if attachment is available</Label>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );

  const renderTargetStep = () => (
    <Card className="p-6 shadow-card rounded-2xl">
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold mb-2">Target Audience</h2>
          <p className="text-muted-foreground">Choose your target audience for this campaign</p>
        </div>

        <div className="space-y-4">
          <div>
            <Label>Target Type</Label>
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <input
                  type="radio"
                  id="target-filter"
                  name="targetType"
                  checked={data.targetType === 'filter'}
                  onChange={() => updateData({ targetType: 'filter' })}
                />
                <Label htmlFor="target-filter">Use filters (like Leads page)</Label>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="radio"
                  id="target-static"
                  name="targetType"
                  checked={data.targetType === 'static'}
                  onChange={() => updateData({ targetType: 'static' })}
                />
                <Label htmlFor="target-static">Static selection</Label>
              </div>
            </div>
          </div>

          {data.targetType === 'static' && (
            <div className="space-y-4">
              <div>
                <Label>Selected Leads</Label>
                <div className="mt-2 p-4 border border-border rounded-lg bg-muted/30">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{data.leadIds.length} leads selected</span>
                    <Button size="sm" variant="outline">
                      <Users className="w-4 h-4 mr-2" />
                      Manage Selection
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {data.targetType === 'filter' && (
            <div className="p-4 border border-border rounded-lg bg-muted/30">
              <p className="text-muted-foreground mb-3">Filter configuration would go here</p>
              <div className="flex items-center justify-between">
                <span>Estimated: ~1,234 leads</span>
                <Button size="sm" variant="outline">
                  <Filter className="w-4 h-4 mr-2" />
                  Configure Filters
                </Button>
              </div>
            </div>
          )}

          <div>
            <h3 className="font-semibold mb-3">Deduplication Settings</h3>
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  checked={data.dedupe.suppressBounced}
                  onCheckedChange={(checked) => updateData({
                    dedupe: { ...data.dedupe, suppressBounced: !!checked }
                  })}
                />
                <Label>Suppress bounced emails</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  checked={data.dedupe.onePerDomain}
                  onCheckedChange={(checked) => updateData({
                    dedupe: { ...data.dedupe, onePerDomain: !!checked }
                  })}
                />
                <Label>One email per domain</Label>
              </div>
              <div className="flex items-center space-x-2 gap-2">
                <Label>Skip leads contacted in last</Label>
                <Input
                  type="number"
                  value={data.dedupe.contactedLastDays}
                  onChange={(e) => updateData({
                    dedupe: { ...data.dedupe, contactedLastDays: parseInt(e.target.value) || 0 }
                  })}
                  className="w-20"
                />
                <Label>days</Label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
  const renderRulesStep = () => (
    <Card className="p-6 shadow-card rounded-2xl">
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold mb-2">Verzendregels</h2>
          <p className="text-muted-foreground">Overzicht van hard-coded verzendregels (read-only)</p>
        </div>

        <div className="space-y-6">
          <div>
            <Label className="text-base font-semibold">Target Domains</Label>
            <p className="text-sm text-muted-foreground mb-3">Select which domains to include</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {['com', 'org', 'net', 'io', 'co.uk', 'de', 'fr', 'nl'].map(domain => (
                <div key={domain} className="flex items-center space-x-2">
                  <Checkbox
                    checked={data.domains.includes(domain)}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        updateData({ domains: [...data.domains, domain] });
                      } else {
                        updateData({ domains: data.domains.filter(d => d !== domain) });
                      }
                    }}
                  />
                  <Label>.{domain}</Label>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <Label className="text-base font-semibold">Throttle & Window</Label>
              <div className="space-y-3 mt-3">
                <Badge variant="outline">
                  {data.throttle.perHour} emails per hour
                </Badge>
                <Badge variant="outline">
                  {data.throttle.weekdays ? 'Weekdays only' : '7 days/week'} • {data.throttle.windowStart}–{data.throttle.windowEnd}
                </Badge>
              </div>
            </div>

            <div>
              <Label className="text-base font-semibold">Retry Policy</Label>
              <div className="space-y-3 mt-3">
                <Badge variant="outline">
                  Max {data.retry.maxAttempts} attempts
                </Badge>
                <Badge variant="outline">
                  {data.retry.backoffHours}h backoff
                </Badge>
              </div>
            </div>
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
            <h2 className="text-2xl font-bold mb-2">Review & Launch</h2>
            <p className="text-muted-foreground">Review your campaign settings before launching</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-3">Campaign Details</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Name:</span>
                  <span className="font-medium">{data.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Template:</span>
                  <span className="font-medium">{templates.find(t => t.id === data.templateId)?.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Start:</span>
                  <span className="font-medium">
                    {data.startType === 'now' ? 'Immediately' : format(data.scheduledStart!, 'PPP', { locale: nl })}
                  </span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-3">Target Audience</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Type:</span>
                  <span className="font-medium">{data.targetType === 'static' ? 'Static Selection' : 'Filter-based'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Count:</span>
                  <span className="font-medium">{data.targetType === 'static' ? data.leadIds.length : '~1,234'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Domains:</span>
                  <span className="font-medium">{data.domains.length} selected</span>
                </div>
              </div>
            </div>
          </div>

          {dryRunResult && (
            <div className="border border-border rounded-lg p-4 bg-muted/30">
              <h4 className="font-semibold mb-2">Dry Run Results</h4>
              <div className="text-sm space-y-1">
                <p><strong>{dryRunResult.totalPlanned}</strong> emails planned for sending</p>
                <p>Scheduled over <strong>{dryRunResult.byDay.length}</strong> days</p>
                
                {dryRunResult.warnings.length > 0 && (
                  <div className="mt-3 p-3 bg-warning/10 border border-warning/20 rounded">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="w-4 h-4 text-warning" />
                      <span className="font-medium">Warnings</span>
                    </div>
                    <ul className="list-disc list-inside text-xs space-y-1">
                      {dryRunResult.warnings.map((warning, i) => (
                        <li key={i}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </Card>

      <div className="flex gap-3">
        <Button
          variant="outline"
          onClick={handleDryRun}
          disabled={loading}
          className="flex-1"
        >
          {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
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
              Start Campaign
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Start Campaign</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to start this campaign? Emails will begin sending according to your configured schedule.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleSubmit}
                className="bg-gradient-accent hover:shadow-glow"
              >
                Start Campaign
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
            Back to Campaigns
          </Button>
          <div>
            <h1 className="text-3xl font-bold text-foreground">New Campaign</h1>
            <p className="text-muted-foreground">Create and configure your email campaign</p>
          </div>
        </div>

        {renderStepIndicator()}

        {/* Step Content */}
        {step === 'basic' && renderBasicStep()}
        {step === 'target' && renderTargetStep()}
        {step === 'rules' && renderRulesStep()}
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
              Previous
            </Button>
            <Button
              onClick={handleNext}
              disabled={!validateStep(step)}
              className="bg-gradient-primary hover:shadow-glow"
            >
              Next
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}