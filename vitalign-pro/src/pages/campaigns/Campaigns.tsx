import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
  Plus, 
  MoreHorizontal, 
  Play, 
  Pause, 
  Square, 
  Copy, 
  Eye,
  Users,
  TrendingUp,
  Loader2
} from 'lucide-react';
import { Campaign, CampaignStatus } from '@/types/campaign';
import { campaignsService } from '@/services/campaigns';
import { useToast } from '@/hooks/use-toast';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';

const statusColors = {
  [CampaignStatus.DRAFT]: 'bg-gray-100 text-gray-800',
  [CampaignStatus.SCHEDULED]: 'bg-blue-100 text-blue-800',
  [CampaignStatus.RUNNING]: 'bg-green-100 text-green-800',
  [CampaignStatus.PAUSED]: 'bg-yellow-100 text-yellow-800',
  [CampaignStatus.COMPLETED]: 'bg-emerald-100 text-emerald-800',
  [CampaignStatus.STOPPED]: 'bg-red-100 text-red-800',
};

const statusLabels = {
  [CampaignStatus.DRAFT]: 'Draft',
  [CampaignStatus.SCHEDULED]: 'Scheduled',
  [CampaignStatus.RUNNING]: 'Running',
  [CampaignStatus.PAUSED]: 'Paused',
  [CampaignStatus.COMPLETED]: 'Completed',
  [CampaignStatus.STOPPED]: 'Stopped',
};

export default function Campaigns() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();
  
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const source = searchParams.get('source');
  const leadIds = searchParams.get('ids');

  useEffect(() => {
    fetchCampaigns();
  }, []);

  useEffect(() => {
    if (source === 'leads' && leadIds) {
      toast({
        title: 'Leads ready for campaign',
        description: `${leadIds.split(',').length} leads selected for new campaign`,
      });
    }
  }, [source, leadIds, toast]);

  const fetchCampaigns = async () => {
    setLoading(true);
    try {
      const response = await campaignsService.getCampaigns();
      setCampaigns(response.items);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load campaigns',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (action: 'pause' | 'resume' | 'stop' | 'duplicate', campaignId: string) => {
    setActionLoading(campaignId);
    try {
      let response;
      switch (action) {
        case 'pause':
          response = await campaignsService.pauseCampaign(campaignId);
          toast({ title: 'Campaign paused successfully' });
          break;
        case 'resume':
          response = await campaignsService.resumeCampaign(campaignId);
          toast({ title: 'Campaign resumed successfully' });
          break;
        case 'stop':
          response = await campaignsService.stopCampaign(campaignId);
          toast({ title: 'Campaign stopped successfully' });
          break;
        case 'duplicate':
          response = await campaignsService.duplicateCampaign(campaignId);
          toast({ title: 'Campaign duplicated successfully' });
          break;
      }
      
      if (response?.ok || response?.id) {
        await fetchCampaigns();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: `Failed to ${action} campaign`,
        variant: 'destructive'
      });
    } finally {
      setActionLoading(null);
    }
  };

  const formatDate = (date: Date) => {
    return format(date, 'dd MMM yyyy HH:mm', { locale: nl });
  };

  const calculateRate = (numerator: number, denominator: number) => {
    if (denominator === 0) return '0%';
    return `${Math.round((numerator / denominator) * 100)}%`;
  };

  const getTotalStats = () => {
    const totals = campaigns.reduce((acc, campaign) => ({
      campaigns: acc.campaigns + 1,
      sent: acc.sent + campaign.sentCount,
      opens: acc.opens + campaign.openCount,
      replies: acc.replies + campaign.replyCount
    }), { campaigns: 0, sent: 0, opens: 0, replies: 0 });

    return totals;
  };

  const stats = getTotalStats();

  return (
    <div className="min-h-screen bg-gradient-subtle p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Campaigns</h1>
            <p className="text-muted-foreground">Create and manage your email campaigns</p>
          </div>
          <div className="flex gap-3">
            <Button
              onClick={() => {
                const params = source && leadIds ? `?source=${source}&ids=${leadIds}` : '';
                navigate(`/campaigns/new${params}`);
              }}
              className="bg-gradient-primary hover:shadow-glow"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Campaign
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="p-6 shadow-card rounded-2xl">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Campaigns</p>
                <p className="text-2xl font-bold">{stats.campaigns}</p>
              </div>
              <div className="h-12 w-12 bg-primary/10 rounded-2xl flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-primary" />
              </div>
            </div>
          </Card>

          <Card className="p-6 shadow-card rounded-2xl">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Emails Sent</p>
                <p className="text-2xl font-bold">{stats.sent.toLocaleString()}</p>
              </div>
              <div className="h-12 w-12 bg-accent/10 rounded-2xl flex items-center justify-center">
                <Users className="h-6 w-6 text-accent" />
              </div>
            </div>
          </Card>

          <Card className="p-6 shadow-card rounded-2xl">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Opens</p>
                <p className="text-2xl font-bold">{stats.opens.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">
                  {calculateRate(stats.opens, stats.sent)} open rate
                </p>
              </div>
              <div className="h-12 w-12 bg-warning/10 rounded-2xl flex items-center justify-center">
                <Eye className="h-6 w-6 text-warning" />
              </div>
            </div>
          </Card>

          <Card className="p-6 shadow-card rounded-2xl">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Replies</p>
                <p className="text-2xl font-bold">{stats.replies.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">
                  {calculateRate(stats.replies, stats.sent)} reply rate
                </p>
              </div>
              <div className="h-12 w-12 bg-success/10 rounded-2xl flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-success" />
              </div>
            </div>
          </Card>
        </div>

        {/* Campaigns Table */}
        <Card className="shadow-card rounded-2xl overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/30">
                <TableHead>Campaign Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Template</TableHead>
                <TableHead>Target</TableHead>
                <TableHead>Sent</TableHead>
                <TableHead>Opens</TableHead>
                <TableHead>Replies</TableHead>
                <TableHead>Start Date</TableHead>
                <TableHead className="w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-48" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-20" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-32" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-16" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-16" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-16" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-16" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-24" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-8" /></TableCell>
                  </TableRow>
                ))
              ) : campaigns.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8">
                    <div className="text-muted-foreground">
                      <TrendingUp className="w-12 h-12 mx-auto mb-4 opacity-20" />
                      <p className="text-lg font-medium">No campaigns yet</p>
                      <p className="text-sm">Create your first email campaign to get started.</p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                campaigns.map((campaign) => (
                  <TableRow key={campaign.id} className="hover:bg-muted/20">
                    <TableCell className="font-medium">
                      <div>
                        <p className="font-semibold">{campaign.name}</p>
                        <p className="text-sm text-muted-foreground">ID: {campaign.id}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={statusColors[campaign.status]}>
                        {statusLabels[campaign.status]}
                      </Badge>
                    </TableCell>
                    <TableCell>{campaign.templateName}</TableCell>
                    <TableCell>{campaign.targetCount.toLocaleString()}</TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{campaign.sentCount.toLocaleString()}</p>
                        {campaign.targetCount > 0 && (
                          <p className="text-xs text-muted-foreground">
                            {calculateRate(campaign.sentCount, campaign.targetCount)}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{campaign.openCount.toLocaleString()}</p>
                        {campaign.sentCount > 0 && (
                          <p className="text-xs text-muted-foreground">
                            {calculateRate(campaign.openCount, campaign.sentCount)}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{campaign.replyCount.toLocaleString()}</p>
                        {campaign.sentCount > 0 && (
                          <p className="text-xs text-muted-foreground">
                            {calculateRate(campaign.replyCount, campaign.sentCount)}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{formatDate(campaign.startDate)}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            {actionLoading === campaign.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <MoreHorizontal className="w-4 h-4" />
                            )}
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="bg-popover border border-border">
                          <DropdownMenuItem
                            onClick={() => navigate(`/campaigns/${campaign.id}`)}
                          >
                            <Eye className="w-4 h-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          
                          {campaign.status === CampaignStatus.RUNNING && (
                            <DropdownMenuItem
                              onClick={() => handleAction('pause', campaign.id)}
                            >
                              <Pause className="w-4 h-4 mr-2" />
                              Pause
                            </DropdownMenuItem>
                          )}
                          
                          {campaign.status === CampaignStatus.PAUSED && (
                            <DropdownMenuItem
                              onClick={() => handleAction('resume', campaign.id)}
                            >
                              <Play className="w-4 h-4 mr-2" />
                              Resume
                            </DropdownMenuItem>
                          )}
                          
                          {(campaign.status === CampaignStatus.RUNNING || campaign.status === CampaignStatus.PAUSED) && (
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
                                  <Square className="w-4 h-4 mr-2" />
                                  Stop
                                </DropdownMenuItem>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>Stop Campaign</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    Are you sure you want to stop this campaign? This action cannot be undone.
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                                  <AlertDialogAction
                                    onClick={() => handleAction('stop', campaign.id)}
                                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                  >
                                    Stop Campaign
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          )}
                          
                          <DropdownMenuSeparator />
                          
                          <DropdownMenuItem
                            onClick={() => handleAction('duplicate', campaign.id)}
                          >
                            <Copy className="w-4 h-4 mr-2" />
                            Duplicate
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </Card>
      </div>
    </div>
  );
}