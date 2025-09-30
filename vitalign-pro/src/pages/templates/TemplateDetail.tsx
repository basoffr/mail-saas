import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';
import { ArrowLeft, Eye, FileText, Send, Image } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { templatesService } from '@/services/templates';
import { leadsService } from '@/services/leads';
import { HtmlViewer } from '@/components/templates/HtmlViewer';
import { VariablesModal } from '@/components/templates/VariablesModal';
import { TestsendModal } from '@/components/templates/TestsendModal';
import { ImageSlotsCard } from '@/components/templates/ImageSlotsCard';

export default function TemplateDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [selectedLeadId, setSelectedLeadId] = useState<string>('');
  const [variablesModal, setVariablesModal] = useState(false);
  const [testsendModal, setTestsendModal] = useState(false);

  const { data: template, isLoading: templateLoading } = useQuery({
    queryKey: ['template', id],
    queryFn: () => templatesService.getTemplate(id!),
    enabled: !!id
  });

  const { data: preview, isLoading: previewLoading } = useQuery({
    queryKey: ['template-preview', id, selectedLeadId],
    queryFn: () => templatesService.getTemplatePreview(id!, selectedLeadId || undefined),
    enabled: !!id
  });

  const { data: leads } = useQuery({
    queryKey: ['leads-for-preview'],
    queryFn: () => leadsService.getLeads({ limit: 10 })
  });

  if (!id) {
    return <div>Template ID niet gevonden</div>;
  }

  if (templateLoading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <div>
            <Skeleton className="h-8 w-48 mb-2" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="rounded-2xl shadow-soft p-6">
            <Skeleton className="h-6 w-32 mb-4" />
            <Skeleton className="h-64 w-full" />
          </Card>
          <Card className="rounded-2xl shadow-soft p-6">
            <Skeleton className="h-6 w-32 mb-4" />
            <Skeleton className="h-64 w-full" />
          </Card>
        </div>
      </div>
    );
  }

  if (!template) {
    return (
      <div className="container mx-auto p-6">
        <Alert>
          <AlertDescription>Template niet gevonden</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/templates')}>
          <ArrowLeft className="h-4 w-4" />
          Terug
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-foreground">{template.name}</h1>
          <p className="text-muted-foreground">
            Laatst gewijzigd: {format(new Date(template.updatedAt), 'dd MMM yyyy HH:mm', { locale: nl })}
          </p>
        </div>
        <div className="ml-auto flex gap-2">
          <Button variant="outline" onClick={() => setVariablesModal(true)}>
            <FileText className="h-4 w-4 mr-2" />
            Variabelen
          </Button>
          <Button variant="outline" onClick={() => setTestsendModal(true)}>
            <Send className="h-4 w-4 mr-2" />
            Test versturen
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Template Content */}
        <Card className="rounded-2xl shadow-soft">
          <div className="p-6">
            <h2 className="text-lg font-semibold mb-4">Template inhoud</h2>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground">Onderwerp</label>
                <div className="mt-1 p-3 bg-muted rounded-lg">
                  <HtmlViewer content={template.subject} />
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-muted-foreground">Bericht</label>
                <div className="mt-1 p-3 bg-muted rounded-lg max-h-96 overflow-y-auto">
                  <HtmlViewer content={template.bodyHtml} />
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Preview Panel */}
        <Card className="rounded-2xl shadow-soft">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Preview</h2>
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-muted-foreground">Test lead:</label>
                <Select value={selectedLeadId} onValueChange={setSelectedLeadId}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="Selecteer lead" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">Geen lead</SelectItem>
                    {leads?.items.map((lead) => (
                      <SelectItem key={lead.id} value={lead.id}>
                        {lead.email}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

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

            <Tabs defaultValue="html" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="html">HTML</TabsTrigger>
                <TabsTrigger value="text">Tekst</TabsTrigger>
              </TabsList>
              
              <TabsContent value="html" className="mt-4">
                {previewLoading ? (
                  <Skeleton className="h-64 w-full" />
                ) : (
                  <div 
                    className="border rounded-lg p-4 bg-white max-h-96 overflow-y-auto"
                    dangerouslySetInnerHTML={{ __html: preview?.html || '' }}
                  />
                )}
              </TabsContent>
              
              <TabsContent value="text" className="mt-4">
                {previewLoading ? (
                  <Skeleton className="h-64 w-full" />
                ) : (
                  <div className="border rounded-lg p-4 bg-muted max-h-96 overflow-y-auto">
                    <pre className="whitespace-pre-wrap text-sm">{preview?.text}</pre>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </div>
        </Card>
      </div>

      {/* Assets */}
      {template.assets && template.assets.length > 0 && (
        <ImageSlotsCard assets={template.assets} />
      )}

      <VariablesModal
        open={variablesModal}
        onOpenChange={setVariablesModal}
        templateId={id}
      />

      <TestsendModal
        open={testsendModal}
        onOpenChange={setTestsendModal}
        templateId={id}
      />
    </div>
  );
}