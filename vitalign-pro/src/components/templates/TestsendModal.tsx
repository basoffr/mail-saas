import { useState, useMemo } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Send, Search, Check, ChevronsUpDown } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { cn } from '@/lib/utils';
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
  const [leadSearchOpen, setLeadSearchOpen] = useState(false);
  const [errors, setErrors] = useState<{ email?: string }>({});

  // Fetch ALL leads for search (no limit)
  const { data: leads } = useQuery({
    queryKey: ['leads-for-test'],
    queryFn: () => leadsService.getLeads({ limit: 1000 }), // Get many leads for search
    enabled: open
  });

  // Find selected lead for display
  const selectedLead = useMemo(() => {
    return leads?.items.find(lead => lead.id === selectedLeadId);
  }, [leads, selectedLeadId]);

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
            <Popover open={leadSearchOpen} onOpenChange={setLeadSearchOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  role="combobox"
                  aria-expanded={leadSearchOpen}
                  className="w-full justify-between"
                >
                  {selectedLead ? (
                    <span className="truncate">
                      {selectedLead.email} {selectedLead.companyName ? `(${selectedLead.companyName})` : ''}
                    </span>
                  ) : (
                    "Zoek lead..."
                  )}
                  <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-[400px] p-0">
                <Command>
                  <CommandInput placeholder="Zoek op email of bedrijf..." />
                  <CommandList>
                    <CommandEmpty>Geen leads gevonden</CommandEmpty>
                    <CommandGroup>
                      <CommandItem
                        value="__none__"
                        onSelect={() => {
                          setSelectedLeadId('');
                          setLeadSearchOpen(false);
                        }}
                      >
                        <Check
                          className={cn(
                            "mr-2 h-4 w-4",
                            selectedLeadId === '' ? "opacity-100" : "opacity-0"
                          )}
                        />
                        Geen lead (toon placeholders)
                      </CommandItem>
                      {leads?.items.map((lead) => (
                        <CommandItem
                          key={lead.id}
                          value={`${lead.email} ${lead.companyName || ''}`}
                          onSelect={() => {
                            setSelectedLeadId(lead.id);
                            setLeadSearchOpen(false);
                          }}
                        >
                          <Check
                            className={cn(
                              "mr-2 h-4 w-4",
                              selectedLeadId === lead.id ? "opacity-100" : "opacity-0"
                            )}
                          />
                          <div className="flex flex-col">
                            <span className="font-medium">{lead.email}</span>
                            {lead.companyName && (
                              <span className="text-xs text-muted-foreground">{lead.companyName}</span>
                            )}
                          </div>
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
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