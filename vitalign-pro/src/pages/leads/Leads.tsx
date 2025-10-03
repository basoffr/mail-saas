import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { 
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { 
  Search, 
  Filter, 
  Upload, 
  MoreHorizontal, 
  ExternalLink,
  Eye,
  Users,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Trash2
} from 'lucide-react';
import { Lead, LeadsQuery, LeadStatus, Template, TemplatePreview } from '@/types/lead';
import { leadsService, toUiLeadStatus, toneToBadgeClass, BackendLeadStatus } from '@/services/leads';
import { templatesService } from '@/services/templates';
import { ImagePreview } from '@/components/leads/ImagePreview';
import { JsonViewer } from '@/components/leads/JsonViewer';
import { useToast } from '@/hooks/use-toast';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';

const ITEMS_PER_PAGE = 25;

// Helper function to render status badge with backend mapping
const renderStatusBadge = (status: LeadStatus | BackendLeadStatus) => {
  const uiStatus = toUiLeadStatus(status as BackendLeadStatus);
  const badgeClass = toneToBadgeClass(uiStatus.tone);
  return (
    <Badge className={badgeClass}>
      {uiStatus.label}
    </Badge>
  );
};

export default function Leads() {
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLeads, setSelectedLeads] = useState<Set<string>>(new Set());
  const [query, setQuery] = useState<LeadsQuery>({
    page: 1,
    limit: ITEMS_PER_PAGE,
    sortBy: 'createdAt',
    sortOrder: 'desc'
  });
  const [total, setTotal] = useState(0);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [templatePreview, setTemplatePreview] = useState<TemplatePreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const fetchLeads = async () => {
    setLoading(true);
    try {
      const response = await leadsService.getLeads(query);
      setLeads(response.items);
      setTotal(response.total);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load leads',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await templatesService.getTemplates();
      setTemplates(response.items);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const handleTemplatePreview = async () => {
    if (!selectedTemplate || !selectedLead) return;
    
    setPreviewLoading(true);
    try {
      const preview = await templatesService.getTemplatePreview(selectedTemplate, selectedLead.id);
      setTemplatePreview(preview);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to generate template preview',
        variant: 'destructive'
      });
    } finally {
      setPreviewLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, [query]);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const handleSelectAll = () => {
    if (selectedLeads.size === leads.length) {
      setSelectedLeads(new Set());
    } else {
      setSelectedLeads(new Set(leads.map(lead => lead.id)));
    }
  };

  const handleSelectLead = (leadId: string) => {
    const newSelected = new Set(selectedLeads);
    if (newSelected.has(leadId)) {
      newSelected.delete(leadId);
    } else {
      newSelected.add(leadId);
    }
    setSelectedLeads(newSelected);
  };

  const handleAddToCampaign = () => {
    // TODO: Implement add to campaign functionality
    toast({
      title: 'Success',
      description: `${selectedLeads.size} leads ready to add to campaign`,
    });
    setSelectedLeads(new Set());
  };

  const handleBulkDelete = async () => {
    const leadIds = Array.from(selectedLeads);
    try {
      const result = await leadsService.deleteLeads(leadIds);
      toast({
        title: 'Leads verwijderd',
        description: `${result.deleted_count} leads succesvol verwijderd`,
      });
      setSelectedLeads(new Set());
      fetchLeads();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Kon leads niet verwijderen. Probeer het opnieuw.',
        variant: 'destructive'
      });
    }
  };

  const totalPages = Math.ceil(total / ITEMS_PER_PAGE);

  const formatDate = (date: Date | undefined) => {
    if (!date) return '-';
    return format(date, 'dd/MM/yyyy HH:mm', { locale: nl });
  };

  const getTldOptions = useMemo(() => {
    const tlds = new Set<string>();
    leads.forEach(lead => {
      if (lead.domain) {
        const parts = lead.domain.split('.');
        if (parts.length > 1) {
          tlds.add('.' + parts[parts.length - 1]);
        }
      }
    });
    return Array.from(tlds);
  }, [leads]);

  return (
    <div className="min-h-screen bg-gradient-subtle p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Leads</h1>
            <p className="text-muted-foreground">Manage and organize your lead database</p>
          </div>
          <div className="flex gap-3">
            <Button
              onClick={() => navigate('/leads/import')}
              className="bg-gradient-primary hover:shadow-glow"
            >
              <Upload className="w-4 h-4 mr-2" />
              Import Leads
            </Button>
          </div>
        </div>

        {/* Filters & Search */}
        <Card className="p-6 shadow-card rounded-2xl">
          <div className="flex flex-col gap-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by email, company, or domain..."
                    className="pl-10"
                    value={query.search || ''}
                    onChange={(e) => setQuery(prev => ({ ...prev, search: e.target.value, page: 1 }))}
                  />
                </div>
              </div>
              
              <Select
                value={query.status?.join(',') || 'all'}
                onValueChange={(value) => {
                  const statuses = value && value !== 'all' ? value.split(',') as LeadStatus[] : undefined;
                  setQuery(prev => ({ ...prev, status: statuses, page: 1 }));
                }}
              >
                <SelectTrigger className="w-[180px]">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent className="bg-popover border border-border">
                  <SelectItem value="all">All Statuses</SelectItem>
                  {Object.values(LeadStatus).map(status => (
                    <SelectItem key={status} value={status}>
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={query.sortBy || 'createdAt'}
                onValueChange={(value) => setQuery(prev => ({ 
                  ...prev, 
                  sortBy: value as any,
                  page: 1 
                }))}
              >
                <SelectTrigger className="w-[160px]">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent className="bg-popover border border-border">
                  <SelectItem value="email">Email</SelectItem>
                  <SelectItem value="companyName">Company</SelectItem>
                  <SelectItem value="lastMailed">Last Mailed</SelectItem>
                  <SelectItem value="lastOpened">Last Opened</SelectItem>
                  <SelectItem value="createdAt">Created</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {selectedLeads.size > 0 && (
              <div className="flex items-center gap-4 p-4 bg-primary/5 rounded-lg border border-primary/20">
                <span className="text-sm font-medium">
                  {selectedLeads.size} lead{selectedLeads.size > 1 ? 's' : ''} selected
                </span>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={handleAddToCampaign}
                    className="bg-gradient-accent hover:shadow-glow"
                  >
                    <Users className="w-4 h-4 mr-2" />
                    Add to Campaign
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={handleBulkDelete}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete ({selectedLeads.size})
                  </Button>
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Table */}
        <Card className="shadow-card rounded-2xl overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/30">
                <TableHead className="w-12">
                  <Checkbox
                    checked={leads.length > 0 && selectedLeads.size === leads.length}
                    onCheckedChange={handleSelectAll}
                  />
                </TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Company</TableHead>
                <TableHead>Domain</TableHead>
                <TableHead>Tags</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Mailed</TableHead>
                <TableHead>Last Opened</TableHead>
                <TableHead>Image</TableHead>
                <TableHead>Report</TableHead>
                <TableHead>Vars</TableHead>
                <TableHead className="w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-32" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-24" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-20" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-16" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-12" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-24" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-24" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-8" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-8" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-8" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-6" /></TableCell>
                  </TableRow>
                ))
              ) : leads.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={12} className="text-center py-8">
                    <div className="text-muted-foreground">
                      <Users className="w-12 h-12 mx-auto mb-4 opacity-20" />
                      <p className="text-lg font-medium">No leads found</p>
                      <p className="text-sm">Try adjusting your search criteria or import some leads to get started.</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                leads.map((lead) => (
                  <TableRow key={lead.id} className="hover:bg-muted/20">
                    <TableCell>
                      <Checkbox
                        checked={selectedLeads.has(lead.id)}
                        onCheckedChange={() => handleSelectLead(lead.id)}
                      />
                    </TableCell>
                    <TableCell className="font-medium">{lead.email}</TableCell>
                    <TableCell>{lead.companyName || '-'}</TableCell>
                    <TableCell>
                      {lead.domain && (
                        <div className="flex items-center gap-1">
                          {lead.domain}
                          {lead.url && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 w-6 p-0"
                              onClick={() => window.open(lead.url, '_blank')}
                            >
                              <ExternalLink className="w-3 h-3" />
                            </Button>
                          )}
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {lead.tags.map(tag => (
                          <Badge key={tag} variant="secondary" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      {renderStatusBadge(lead.status)}
                    </TableCell>
                    <TableCell>{formatDate(lead.lastMailed)}</TableCell>
                    <TableCell>{formatDate(lead.lastOpened)}</TableCell>
                    <TableCell>
                      <div className="text-center">
                        {lead.hasImage ? '✅' : '❌'}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-center">
                        {lead.hasReport ? '✅' : '❌'}
                      </div>
                    </TableCell>
                    <TableCell>
                      {lead.varsCompleteness ? (
                        <Badge 
                          variant={lead.varsCompleteness.is_complete ? "default" : "secondary"}
                          className="font-mono"
                        >
                          {lead.varsCompleteness.filled}/{lead.varsCompleteness.total}
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="font-mono">
                          {Object.keys(lead.vars || {}).length}
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Sheet>
                        <SheetTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={() => setSelectedLead(lead)}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                        </SheetTrigger>
                        <SheetContent className="w-[400px] sm:w-[540px]">
                          <SheetHeader>
                            <SheetTitle>Lead Details</SheetTitle>
                            <SheetDescription>
                              View and manage lead information
                            </SheetDescription>
                          </SheetHeader>
                          {selectedLead && <LeadDetails lead={selectedLead} />}
                        </SheetContent>
                      </Sheet>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </Card>

        {/* Pagination */}
        {total > ITEMS_PER_PAGE && (
          <Card className="p-4 shadow-card rounded-2xl">
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                Showing {((query.page || 1) - 1) * ITEMS_PER_PAGE + 1} to{' '}
                {Math.min((query.page || 1) * ITEMS_PER_PAGE, total)} of {total} leads
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setQuery(prev => ({ ...prev, page: (prev.page || 1) - 1 }))}
                  disabled={!query.page || query.page <= 1}
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </Button>
                <div className="text-sm">
                  Page {query.page || 1} of {totalPages}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setQuery(prev => ({ ...prev, page: (prev.page || 1) + 1 }))}
                  disabled={!query.page || query.page >= totalPages}
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </Card>
        )}
      </div>
      
      {/* Template Preview Dialog */}
      <Dialog open={!!templatePreview} onOpenChange={() => setTemplatePreview(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Template Preview</DialogTitle>
            <DialogDescription>
              Preview how the template will look for this lead
            </DialogDescription>
          </DialogHeader>
          {templatePreview && (
            <div className="space-y-4">
              {templatePreview.warnings && (
                <div className="bg-warning/10 border border-warning/20 rounded-lg p-3">
                  <h4 className="font-medium text-warning-foreground mb-2">Warnings:</h4>
                  <ul className="list-disc list-inside text-sm text-warning-foreground/80">
                    {templatePreview.warnings.map((warning, i) => (
                      <li key={i}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium mb-2">HTML Preview</h4>
                  <Card className="p-4 max-h-96 overflow-y-auto">
                    <div dangerouslySetInnerHTML={{ __html: templatePreview.html }} />
                  </Card>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Plain Text</h4>
                  <Card className="p-4 max-h-96 overflow-y-auto">
                    <pre className="whitespace-pre-wrap text-sm">{templatePreview.text}</pre>
                  </Card>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Lead Details Component
function LeadDetails({ lead }: { lead: Lead }) {
  const { toast } = useToast();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [templatePreview, setTemplatePreview] = useState<TemplatePreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    templatesService.getTemplates().then(response => {
      setTemplates(response.items);
    });
  }, []);

  const handleTemplatePreview = async () => {
    if (!selectedTemplate) return;
    
    setPreviewLoading(true);
    try {
      const preview = await templatesService.getTemplatePreview(selectedTemplate, lead.id);
      setTemplatePreview(preview);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to generate template preview',
        variant: 'destructive'
      });
    } finally {
      setPreviewLoading(false);
    }
  };

  const formatDate = (date: Date | undefined) => {
    if (!date) return 'Never';
    return format(date, 'dd MMMM yyyy \'at\' HH:mm', { locale: nl });
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await leadsService.deleteLeads([lead.id]);
      toast({
        title: 'Lead verwijderd',
        description: 'De lead is succesvol verwijderd en verplaatst naar de prullenbak',
      });
      // Trigger refresh by closing drawer and reloading
      window.location.reload();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Kon lead niet verwijderen. Probeer het opnieuw.',
        variant: 'destructive'
      });
    } finally {
      setDeleting(false);
      setDeleteDialogOpen(false);
    }
  };

  return (
    <div className="space-y-6 py-6">
      {/* Basic Info */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium text-muted-foreground">Email</label>
          <p className="text-lg font-mono">{lead.email}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-muted-foreground">Status</label>
          <div className="mt-1">
            {renderStatusBadge(lead.status)}
          </div>
        </div>
        <div>
          <label className="text-sm font-medium text-muted-foreground">Company</label>
          <p>{lead.companyName || 'Not specified'}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-muted-foreground">Domain</label>
          <div className="flex items-center gap-2">
            <p>{lead.domain || 'Not specified'}</p>
            {lead.url && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={() => window.open(lead.url, '_blank')}
              >
                <ExternalLink className="w-3 h-3" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Tags */}
      <div>
        <label className="text-sm font-medium text-muted-foreground mb-2 block">Tags</label>
        <div className="flex flex-wrap gap-2">
          {lead.tags.length > 0 ? (
            lead.tags.map(tag => (
              <Badge key={tag} variant="secondary">{tag}</Badge>
            ))
          ) : (
            <p className="text-muted-foreground">No tags</p>
          )}
        </div>
      </div>

      {/* Activity */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-sm font-medium text-muted-foreground">Last Mailed</label>
          <p>{formatDate(lead.lastMailed)}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-muted-foreground">Last Opened</label>
          <p>{formatDate(lead.lastOpened)}</p>
        </div>
      </div>

      {/* Completeness Overview */}
      {lead.varsCompleteness && (
        <div className="bg-muted/30 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium">Lead Completeness</label>
            <Badge variant={lead.isComplete ? "default" : "secondary"}>
              {lead.isComplete ? 'Complete ✅' : 'Incomplete'}
            </Badge>
          </div>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Variables:</span>
              <span className="ml-2 font-mono font-medium">
                {lead.varsCompleteness.filled}/{lead.varsCompleteness.total}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Image:</span>
              <span className="ml-2">{lead.hasImage ? '✅' : '❌'}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Report:</span>
              <span className="ml-2">{lead.hasReport ? '✅' : '❌'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Variables Detail */}
      <div>
        <label className="text-sm font-medium text-muted-foreground mb-2 block">
          Template Variables
          {lead.varsCompleteness && (
            <span className="ml-2 font-mono text-xs">({lead.varsCompleteness.filled}/{lead.varsCompleteness.total})</span>
          )}
        </label>
        {lead.varsCompleteness ? (
          <div className="space-y-2">
            {lead.varsCompleteness.missing.length === 0 && lead.vars && Object.keys(lead.vars).length === 0 ? (
              <p className="text-sm text-muted-foreground">All required variables are filled</p>
            ) : (
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {Object.entries(lead.vars || {}).map(([key, value]) => (
                  <div key={key} className="flex items-start gap-2 text-sm">
                    <span className="text-green-600">✅</span>
                    <span className="font-mono text-muted-foreground">{key}:</span>
                    <span className="flex-1 truncate">{String(value)}</span>
                  </div>
                ))}
                {lead.varsCompleteness.missing.map((varName) => (
                  <div key={varName} className="flex items-start gap-2 text-sm">
                    <span className="text-destructive">❌</span>
                    <span className="font-mono text-muted-foreground">{varName}</span>
                    <span className="text-xs text-muted-foreground italic ml-auto">Missing</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <JsonViewer data={lead.vars} />
        )}
      </div>

      {/* Image Section */}
      <div>
        <label className="text-sm font-medium text-muted-foreground mb-2 block">Image</label>
        {lead.hasImage && lead.imageKey ? (
          <ImagePreview imageKey={lead.imageKey} className="w-32 h-32 rounded-lg" />
        ) : (
          <div className="bg-muted/30 rounded-lg p-4 text-center text-muted-foreground">
            <p className="text-sm">No image attached</p>
          </div>
        )}
      </div>

      {/* Report Section */}
      <div>
        <label className="text-sm font-medium text-muted-foreground mb-2 block">Report</label>
        {lead.hasReport ? (
          <div className="bg-muted/30 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <span className="text-green-600">📄 ✅</span>
              <span className="text-sm font-medium">Report attached</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Download available from reports tab</p>
          </div>
        ) : (
          <div className="bg-muted/30 rounded-lg p-4 text-center text-muted-foreground">
            <p className="text-sm">No report attached</p>
          </div>
        )}
      </div>

      {/* Delete Section */}
      <div className="border-t pt-4">
        <label className="text-sm font-medium text-muted-foreground mb-2 block">Danger Zone</label>
        <Button
          variant="destructive"
          onClick={() => setDeleteDialogOpen(true)}
          className="w-full"
          disabled={lead.isDeleted}
        >
          <Trash2 className="w-4 h-4 mr-2" />
          {lead.isDeleted ? 'Lead is verwijderd' : 'Verwijder Lead'}
        </Button>
        
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Weet je het zeker?</AlertDialogTitle>
              <AlertDialogDescription>
                Deze lead wordt verplaatst naar de prullenbak. Je kunt hem later herstellen via de deleted leads view.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Annuleren</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDelete}
                disabled={deleting}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                {deleting ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Trash2 className="w-4 h-4 mr-2" />}
                Verwijderen
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>

      {/* Template Test */}
      <div className="border-t pt-4">
        <label className="text-sm font-medium text-muted-foreground mb-2 block">Test Template Render</label>
        <div className="flex gap-2 mb-4">
          <Select value={selectedTemplate} onValueChange={setSelectedTemplate}>
            <SelectTrigger className="flex-1">
              <SelectValue placeholder="Select template" />
            </SelectTrigger>
            <SelectContent className="bg-popover border border-border">
              {templates.map(template => (
                <SelectItem key={template.id} value={template.id}>
                  {template.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            onClick={handleTemplatePreview}
            disabled={!selectedTemplate || previewLoading}
          >
            {previewLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            Preview
          </Button>
        </div>
        
        {templatePreview && (
          <div className="space-y-4">
            {templatePreview.warnings && (
              <div className="bg-warning/10 border border-warning/20 rounded-lg p-3">
                <h4 className="font-medium text-warning-foreground mb-1">Warnings:</h4>
                <ul className="list-disc list-inside text-sm text-warning-foreground/80">
                  {templatePreview.warnings.map((warning, i) => (
                    <li key={i}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
            <div>
              <h4 className="font-medium mb-2">HTML Preview</h4>
              <Card className="p-4 max-h-48 overflow-y-auto">
                <div dangerouslySetInnerHTML={{ __html: templatePreview.html }} />
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}