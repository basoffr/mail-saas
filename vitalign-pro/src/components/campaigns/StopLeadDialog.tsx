import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { StopCircle, Loader2 } from 'lucide-react';
import { campaignsService } from '@/services/campaigns';
import { useToast } from '@/hooks/use-toast';

interface StopLeadDialogProps {
  campaignId: string;
  leadId: string;
  leadEmail: string;
  onSuccess?: () => void;
  trigger?: React.ReactNode;
}

const STOP_REASONS = [
  { value: 'manual', label: 'Handmatig Stoppen', description: 'Stop deze lead zonder andere leads te beïnvloeden' },
  { value: 'unsubscribe', label: 'Uitgeschreven', description: 'Lead heeft zich uitgeschreven (alle campagnes)' },
  { value: 'bounce', label: 'Bounce/Ongeldig', description: 'Email bounced of is ongeldig (alle campagnes)' },
];

export function StopLeadDialog({ 
  campaignId, 
  leadId, 
  leadEmail,
  onSuccess,
  trigger 
}: StopLeadDialogProps) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState<'unsubscribe' | 'bounce' | 'manual'>('manual');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleStop = async () => {
    setLoading(true);
    try {
      const response = await campaignsService.stopLeadFlow(campaignId, leadId, { reason });
      
      toast({
        title: 'Lead Flow Gestopt',
        description: `${response.canceledCount} toekomstige messages geannuleerd voor ${leadEmail}`,
      });
      
      setOpen(false);
      onSuccess?.();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Kon lead flow niet stoppen',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" size="sm">
            <StopCircle className="w-4 h-4 mr-2" />
            Stop Flow
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Stop Lead Flow</DialogTitle>
          <DialogDescription>
            Stop alle toekomstige emails voor <span className="font-medium">{leadEmail}</span> in deze campaign.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="reason">Reden voor Stoppen</Label>
            <Select value={reason} onValueChange={(v: any) => setReason(v)}>
              <SelectTrigger id="reason">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {STOP_REASONS.map((r) => (
                  <SelectItem key={r.value} value={r.value}>
                    <div className="flex flex-col">
                      <span className="font-medium">{r.label}</span>
                      <span className="text-xs text-muted-foreground">{r.description}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {reason === 'unsubscribe' && (
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
              <p className="text-sm text-yellow-900">
                <strong>Let op:</strong> Deze lead wordt globaal uitgeschreven en ontvangt geen emails meer van <em>alle</em> campagnes.
              </p>
            </div>
          )}

          {reason === 'bounce' && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-900">
                <strong>Let op:</strong> Deze lead wordt gemarkeerd als hard bounce en ontvangt geen emails meer van <em>alle</em> campagnes.
              </p>
            </div>
          )}

          {reason === 'manual' && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
              <p className="text-sm text-blue-900">
                Deze lead wordt alleen gestopt voor <strong>deze campaign</strong>. Andere campagnes worden niet beïnvloed.
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={loading}>
            Annuleren
          </Button>
          <Button 
            onClick={handleStop} 
            disabled={loading}
            variant="destructive"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Stoppen...
              </>
            ) : (
              <>
                <StopCircle className="w-4 h-4 mr-2" />
                Stop Flow
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
