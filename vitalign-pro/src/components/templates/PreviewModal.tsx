import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { ExternalLink } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { templatesService } from '@/services/templates';
import { leadsService } from '@/services/leads';

interface PreviewModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  templateId?: string;
}

export function PreviewModal({ open, onOpenChange, templateId }: PreviewModalProps) {
  const navigate = useNavigate();
  const [selectedLeadId, setSelectedLeadId] = useState<string>('');

  const { data: preview, isLoading } = useQuery({
    queryKey: ['template-preview', templateId, selectedLeadId],
    queryFn: () => templatesService.getTemplatePreview(templateId!, selectedLeadId || undefined),
    enabled: !!templateId && open
  });

  const { data: leads } = useQuery({
    queryKey: ['leads-for-preview'],
    queryFn: () => leadsService.getLeads({ limit: 10 }),
    enabled: open
  });

  const handleOpenDetail = () => {
    if (templateId) {
      navigate(`/templates/${templateId}`);
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle>Template Preview</DialogTitle>
            <div className="flex items-center gap-2">
              <Select value={selectedLeadId} onValueChange={setSelectedLeadId}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Selecteer lead" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Geen lead</SelectItem>
                  {leads?.items.map((lead) => (
                    <SelectItem key={lead.id} value={lead.id}>
                      {lead.email}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button variant="outline" size="sm" onClick={handleOpenDetail}>
                <ExternalLink className="h-4 w-4 mr-2" />
                Open in detail
              </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          {preview?.warnings && preview.warnings.length > 0 && (
            <Alert className="mb-4">
              <AlertDescription>
                <strong>Waarschuwingen:</strong>
                <ul className="mt-1 list-disc list-inside">
                  {preview.warnings.map((warning, i) => (
                    <li key={i}>{warning}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}

          <Tabs defaultValue="html" className="h-full flex flex-col">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="html">HTML</TabsTrigger>
              <TabsTrigger value="text">Tekst</TabsTrigger>
            </TabsList>
            
            <TabsContent value="html" className="flex-1 mt-4">
              {isLoading ? (
                <Skeleton className="h-full w-full" />
              ) : (
                <div 
                  className="border rounded-lg p-4 bg-white h-full overflow-y-auto"
                  dangerouslySetInnerHTML={{ __html: preview?.html || '' }}
                />
              )}
            </TabsContent>
            
            <TabsContent value="text" className="flex-1 mt-4">
              {isLoading ? (
                <Skeleton className="h-full w-full" />
              ) : (
                <div className="border rounded-lg p-4 bg-muted h-full overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-sm">{preview?.text}</pre>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  );
}