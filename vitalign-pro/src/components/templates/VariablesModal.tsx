import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { templatesService } from '@/services/templates';
import { TemplateVarItem } from '@/types/template';

interface VariablesModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  templateId?: string;
}

const sourceLabels = {
  lead: 'Lead data',
  vars: 'Custom variabelen',
  campaign: 'Campagne data',
  image: 'Afbeeldingen'
};

const sourceBadgeVariants = {
  lead: 'default',
  vars: 'secondary',
  campaign: 'outline',
  image: 'destructive'
} as const;

export function VariablesModal({ open, onOpenChange, templateId }: VariablesModalProps) {
  const [search, setSearch] = useState('');

  const { data: variables, isLoading } = useQuery({
    queryKey: ['template-variables', templateId],
    queryFn: () => templatesService.getTemplateVariables(templateId!),
    enabled: !!templateId && open
  });

  const filteredVariables = variables?.filter((variable: TemplateVarItem) =>
    variable.key.toLowerCase().includes(search.toLowerCase()) ||
    variable.source.toLowerCase().includes(search.toLowerCase())
  ) || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Template Variabelen</DialogTitle>
          <p className="text-sm text-muted-foreground">
            Overzicht van alle beschikbare variabelen in deze template
          </p>
        </DialogHeader>

        <div className="flex-1 overflow-hidden space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              placeholder="Zoek variabelen..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>

          <div className="border rounded-xl overflow-hidden">
            {isLoading ? (
              <div className="p-6 space-y-4">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-4">
                    <Skeleton className="h-6 flex-1" />
                    <Skeleton className="h-6 w-24" />
                    <Skeleton className="h-6 w-16" />
                    <Skeleton className="h-6 w-32" />
                  </div>
                ))}
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Variabele</TableHead>
                    <TableHead>Bron</TableHead>
                    <TableHead>Verplicht</TableHead>
                    <TableHead>Voorbeeld</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredVariables.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                        {search ? 'Geen variabelen gevonden' : 'Geen variabelen beschikbaar'}
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredVariables.map((variable, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-mono">{`{{${variable.key}}}`}</TableCell>
                        <TableCell>
                          <Badge variant={sourceBadgeVariants[variable.source]}>
                            {sourceLabels[variable.source]}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {variable.required ? (
                            <Badge variant="destructive" className="text-xs">Verplicht</Badge>
                          ) : (
                            <Badge variant="outline" className="text-xs">Optioneel</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {variable.example || '—'}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            )}
          </div>

          <div className="bg-muted/50 rounded-lg p-4">
            <h4 className="font-medium mb-2">Helper functies:</h4>
            <div className="text-sm text-muted-foreground space-y-1">
              <div><code className="bg-background px-2 py-1 rounded">{'{{firstName|upper}}'}</code> - Hoofdletters</div>
              <div><code className="bg-background px-2 py-1 rounded">{'{{firstName|lower}}'}</code> - Kleine letters</div>
              <div><code className="bg-background px-2 py-1 rounded">{'{{firstName|default:"Beste relatie"}}'}</code> - Standaardwaarde</div>
              <div><code className="bg-background px-2 py-1 rounded">{'{{#if companyName}}...{{/if}}'}</code> - Voorwaardelijk tonen</div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}