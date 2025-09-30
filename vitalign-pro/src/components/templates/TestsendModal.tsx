import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Send } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { templatesService } from '@/services/templates';
import { leadsService } from '@/services/leads';

interface TestsendModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  templateId?: string;
}

export function TestsendModal({ open, onOpenChange, templateId }: TestsendModalProps) {
  const { toast } = useToast();
  const [email, setEmail] = useState('');
  const [selectedLeadId, setSelectedLeadId] = useState<string>('');
  const [errors, setErrors] = useState<{ email?: string }>({});

  const { data: leads } = useQuery({
    queryKey: ['leads-for-test'],
    queryFn: () => leadsService.getLeads({ limit: 10 }),
    enabled: open
  });

  const sendTestMutation = useMutation({
    mutationFn: (payload: { to: string; leadId?: string | null }) =>
      templatesService.sendTest(templateId!, payload),
    onSuccess: () => {
      toast({
        title: 'Test email verzonden',
        description: `Email is verzonden naar ${email}`,
      });
      setEmail('');
      setSelectedLeadId('');
      setErrors({});
      onOpenChange(false);
    },
    onError: (error: Error) => {
      toast({
        title: 'Fout bij verzenden',
        description: error.message,
        variant: 'destructive',
      });
    }
  });

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSend = () => {
    const newErrors: { email?: string } = {};

    if (!email) {
      newErrors.email = 'Email adres is verplicht';
    } else if (!validateEmail(email)) {
      newErrors.email = 'Ongeldig email adres';
    }

    setErrors(newErrors);

    if (Object.keys(newErrors).length === 0) {
      sendTestMutation.mutate({
        to: email,
        leadId: selectedLeadId || null
      });
    }
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      setEmail('');
      setSelectedLeadId('');
      setErrors({});
    }
    onOpenChange(open);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Test email versturen</DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            Verstuur een test versie van deze template
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email adres *</Label>
            <Input
              id="email"
              type="email"
              placeholder="naam@bedrijf.nl"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (errors.email) {
                  setErrors({ ...errors, email: undefined });
                }
              }}
              className={errors.email ? 'border-destructive' : ''}
            />
            {errors.email && (
              <p className="text-sm text-destructive">{errors.email}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="lead">Test lead (optioneel)</Label>
            <Select value={selectedLeadId} onValueChange={setSelectedLeadId}>
              <SelectTrigger>
                <SelectValue placeholder="Selecteer lead voor variabelen" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__none__">Geen lead (toon placeholders)</SelectItem>
                {leads?.items.map((lead) => (
                  <SelectItem key={lead.id} value={lead.id}>
                    {lead.email} {lead.companyName ? `(${lead.companyName})` : ''}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Selecteer een lead om variabelen te vervangen met echte data
            </p>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={() => handleOpenChange(false)}>
              Annuleren
            </Button>
            <Button 
              onClick={handleSend}
              disabled={sendTestMutation.isPending}
            >
              {sendTestMutation.isPending ? (
                'Versturen...'
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Versturen
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}