import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';
import { FileText, Send, Search, ChevronDown } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { templatesService } from '@/services/templates';
import { Template } from '@/types/template';
import { PreviewModal } from '@/components/templates/PreviewModal';
import { VariablesModal } from '@/components/templates/VariablesModal';
import { TestsendModal } from '@/components/templates/TestsendModal';

export default function Templates() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'subject' | 'updatedAt'>('updatedAt');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [previewModal, setPreviewModal] = useState<{ open: boolean; templateId?: string }>({ open: false });
  const [variablesModal, setVariablesModal] = useState<{ open: boolean; templateId?: string }>({ open: false });
  const [testsendModal, setTestsendModal] = useState<{ open: boolean; templateId?: string }>({ open: false });

  const { data, isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: () => templatesService.getTemplates()
  });

  const filteredTemplates = data?.items?.filter((template: Template) => {
    const name = template.name || '';
    const subject = template.subject || '';
    return name.toLowerCase().includes(search.toLowerCase()) ||
      subject.toLowerCase().includes(search.toLowerCase());
  }).sort((a: Template, b: Template) => {
    const aVal = a[sortBy];
    const bVal = b[sortBy];
    const multiplier = sortOrder === 'asc' ? 1 : -1;
    
    if (sortBy === 'updatedAt') {
      const aDate = new Date(aVal || 0).getTime();
      const bDate = new Date(bVal || 0).getTime();
      return multiplier * (aDate - bDate);
    }
    
    return multiplier * String(aVal || '').localeCompare(String(bVal || ''));
  }) || [];

  if (isLoading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <Skeleton className="h-8 w-32 mb-2" />
            <Skeleton className="h-4 w-48" />
          </div>
        </div>
        
        <Card className="rounded-2xl shadow-soft p-6">
          <div className="flex gap-4 mb-6">
            <Skeleton className="h-10 flex-1" />
            <Skeleton className="h-10 w-40" />
          </div>
          
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4 p-4 border rounded-xl">
                <Skeleton className="h-6 flex-1" />
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-6 w-24" />
                <Skeleton className="h-8 w-24" />
              </div>
            ))}
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Templates</h1>
          <p className="text-muted-foreground">Bekijk alle 16 hard-coded email templates (read-only)</p>
        </div>
      </div>

      <Card className="rounded-2xl shadow-soft p-6">
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 mb-6">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">Hard-coded Templates</span>
          </div>
          <p className="text-sm text-blue-700">
            Alle 16 templates (v1-v4 × mail 1-4) zijn hard-coded in de backend. 
            Je kunt ze bekijken, preview en testen, maar niet bewerken.
          </p>
        </div>
        
        <div className="flex gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
            <Input
              placeholder="Zoek templates..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>
          
          <Select value={`${sortBy}-${sortOrder}`} onValueChange={(value) => {
            const [field, order] = value.split('-');
            setSortBy(field as 'name' | 'subject' | 'updatedAt');
            setSortOrder(order as 'asc' | 'desc');
          }}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="updatedAt-desc">Laatst gewijzigd (nieuw)</SelectItem>
              <SelectItem value="updatedAt-asc">Laatst gewijzigd (oud)</SelectItem>
              <SelectItem value="name-asc">Naam (A-Z)</SelectItem>
              <SelectItem value="name-desc">Naam (Z-A)</SelectItem>
              <SelectItem value="subject-asc">Onderwerp (A-Z)</SelectItem>
              <SelectItem value="subject-desc">Onderwerp (Z-A)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="rounded-xl border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Naam</TableHead>
                <TableHead>Onderwerp</TableHead>
                <TableHead>Laatst gewijzigd</TableHead>
                <TableHead>Afbeeldingen</TableHead>
                <TableHead className="text-right">Acties</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTemplates.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                    {search ? 'Geen templates gevonden' : 'Geen templates beschikbaar'}
                  </TableCell>
                </TableRow>
              ) : (
                filteredTemplates.map((template) => {
                  const subject = template.subject || (template as any).subject_template || '';
                  const updatedAt = template.updatedAt || (template as any).updated_at || new Date().toISOString();
                  return (
                  <TableRow key={template.id} className="hover:bg-muted/50">
                    <TableCell className="font-medium">{template.name}</TableCell>
                    <TableCell className="max-w-md truncate">{subject}</TableCell>
                    <TableCell>
                      {format(new Date(updatedAt), 'dd MMM yyyy HH:mm', { locale: nl })}
                    </TableCell>
                    <TableCell>
                      {template.assets?.length ? (
                        <Badge variant="secondary">{template.assets.length} assets</Badge>
                      ) : (
                        <span className="text-muted-foreground">Geen</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setVariablesModal({ open: true, templateId: template.id })}
                        >
                          <FileText className="h-4 w-4" />
                          Variabelen
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setTestsendModal({ open: true, templateId: template.id })}
                        >
                          <Send className="h-4 w-4" />
                          Test
                        </Button>
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => navigate(`/templates/${template.id}`)}
                        >
                          Bekijken
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      </Card>

      <PreviewModal
        open={previewModal.open}
        onOpenChange={(open) => setPreviewModal({ open })}
        templateId={previewModal.templateId}
      />

      <VariablesModal
        open={variablesModal.open}
        onOpenChange={(open) => setVariablesModal({ open })}
        templateId={variablesModal.templateId}
      />

      <TestsendModal
        open={testsendModal.open}
        onOpenChange={(open) => setTestsendModal({ open })}
        templateId={testsendModal.templateId}
      />
    </div>
  );
}