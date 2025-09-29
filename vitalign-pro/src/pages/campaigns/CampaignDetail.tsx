import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { 
  ArrowLeft, 
  Play, 
  Pause, 
  Square, 
  RefreshCw,
  Mail,
  Eye,
  TrendingUp,
  Users,
  Clock,
  AlertTriangle,
  Loader2,
  RotateCcw
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { 
  type CampaignDetail as CampaignDetailType,
  CampaignMessage, 
  CampaignStatus, 
  MessageStatus 
} from '@/types/campaign';
import { campaignsService } from '@/services/campaigns';
import { useToast } from '@/hooks/use-toast';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';
import { RepliesPanel } from '@/components/inbox/RepliesPanel';

const statusColors = {
  [CampaignStatus.DRAFT]: 'bg-gray-100 text-gray-800',
  [CampaignStatus.SCHEDULED]: 'bg-blue-100 text-blue-800',
  [CampaignStatus.RUNNING]: 'bg-green-100 text-green-800',
  [CampaignStatus.PAUSED]: 'bg-yellow-100 text-yellow-800',
  [CampaignStatus.COMPLETED]: 'bg-emerald-100 text-emerald-800',
  [CampaignStatus.STOPPED]: 'bg-red-100 text-red-800',
};

const messageStatusColors = {
  [MessageStatus.PENDING]: 'bg-gray-100 text-gray-800',
  [MessageStatus.SENT]: 'bg-blue-100 text-blue-800',
  [MessageStatus.DELIVERED]: 'bg-green-100 text-green-800',
  [MessageStatus.OPENED]: 'bg-purple-100 text-purple-800',
  [MessageStatus.CLICKED]: 'bg-indigo-100 text-indigo-800',
  [MessageStatus.BOUNCED]: 'bg-red-100 text-red-800',
  [MessageStatus.FAILED]: 'bg-destructive/10 text-destructive',
  [MessageStatus.REPLIED]: 'bg-emerald-100 text-emerald-800',
};

export default function CampaignDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [campaign, setCampaign] = useState<CampaignDetailType | null>(null);
  const [messages, setMessages] = useState<CampaignMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [selectedMessage, setSelectedMessage] = useState<CampaignMessage | null>(null);

  useEffect(() => {
    if (id) {
      fetchCampaignDetail();
      fetchMessages();
    }
  }, [id]);

  // Polling for live updates
  useEffect(() => {
    if (!campaign || campaign.status !== CampaignStatus.RUNNING) return;

    const interval = setInterval(() => {
      fetchCampaignDetail();
    }, 10000); // Poll every 10 seconds

    return () => clearInterval(interval);
  }, [campaign?.status]);

  const fetchCampaignDetail = async () => {
    if (!id) return;
    
    setLoading(true);
    try {
      const data = await campaignsService.getCampaign(id);
      setCampaign(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load campaign details',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async () => {
    if (!id) return;
    
    try {
      const data = await campaignsService.getCampaignMessages(id);
      setMessages(data);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const handleAction = async (action: 'pause' | 'resume' | 'stop') => {
    if (!id) return;
    
    setActionLoading(action);
    try {
      let response;
      switch (action) {
        case 'pause':
          response = await campaignsService.pauseCampaign(id);
          toast({ title: 'Campaign paused successfully' });
          break;
        case 'resume':
          response = await campaignsService.resumeCampaign(id);
          toast({ title: 'Campaign resumed successfully' });
          break;
        case 'stop':
          response = await campaignsService.stopCampaign(id);
          toast({ title: 'Campaign stopped successfully' });
          break;
      }
      
      if (response?.ok) {
        await fetchCampaignDetail();
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

  const handleResendMessage = async (messageId: string) => {
    try {
      await campaignsService.resendMessage(messageId);
      toast({ title: 'Message queued for resend' });
      await fetchMessages();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to resend message',
        variant: 'destructive'
      });
    }
  };

  const formatDate = (date: Date | undefined) => {
    if (!date) return '-';
    return format(date, 'dd MMM yyyy HH:mm', { locale: nl });
  };

  const calculateRate = (numerator: number, denominator: number) => {
    if (denominator === 0) return '0%';
    return `${Math.round((numerator / denominator) * 100)}%`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-subtle p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin" />
          </div>
        </div>
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="min-h-screen bg-gradient-subtle p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-foreground mb-2">Campaign Not Found</h2>
            <p className="text-muted-foreground mb-4">The requested campaign could not be found.</p>
            <Button onClick={() => navigate('/campaigns')}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Campaigns
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-subtle p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
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
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold text-foreground">{campaign.name}</h1>
                <Badge className={statusColors[campaign.status]}>
                  {campaign.status}
                </Badge>
              </div>
              <p className="text-muted-foreground">Campaign ID: {campaign.id}</p>
            </div>
          </div>

          <div className="flex gap-2">
            {campaign.status === CampaignStatus.RUNNING && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    {actionLoading === 'pause' ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Pause className="w-4 h-4" />
                    )}
                    <span className="ml-1">Pause</span>
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Pause Campaign</AlertDialogTitle>
                    <AlertDialogDescription>
                      Are you sure you want to pause this campaign? You can resume it later.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={() => handleAction('pause')}>
                      Pause Campaign
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}

            {campaign.status === CampaignStatus.PAUSED && (
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => handleAction('resume')}
              >
                {actionLoading === 'resume' ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                <span className="ml-1">Resume</span>
              </Button>
            )}

            {(campaign.status === CampaignStatus.RUNNING || campaign.status === CampaignStatus.PAUSED) && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    {actionLoading === 'stop' ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Square className="w-4 h-4" />
                    )}
                    <span className="ml-1">Stop</span>
                  </Button>
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
                      onClick={() => handleAction('stop')}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                      Stop Campaign
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}

            <Button variant="outline" size="sm" onClick={fetchCampaignDetail}>
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <Card className="p-4 shadow-card rounded-2xl">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">{campaign.targetCount.toLocaleString()}</div>
              <div className="text-sm text-muted-foreground">Target</div>
            </div>
          </Card>

          <Card className="p-4 shadow-card rounded-2xl">
            <div className="text-center">
              <div className="text-2xl font-bold text-accent">{campaign.sentCount.toLocaleString()}</div>
              <div className="text-sm text-muted-foreground">Sent</div>
              <div className="text-xs text-muted-foreground">
                {calculateRate(campaign.sentCount, campaign.targetCount)}
              </div>
            </div>
          </Card>

          <Card className="p-4 shadow-card rounded-2xl">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{campaign.openCount.toLocaleString()}</div>
              <div className="text-sm text-muted-foreground">Opens</div>
              <div className="text-xs text-muted-foreground">
                {calculateRate(campaign.openCount, campaign.sentCount)}
              </div>
            </div>
          </Card>

          <Card className="p-4 shadow-card rounded-2xl">
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{campaign.clickCount.toLocaleString()}</div>
              <div className="text-sm text-muted-foreground">Clicks</div>
              <div className="text-xs text-muted-foreground">
                {calculateRate(campaign.clickCount, campaign.sentCount)}
              </div>
            </div>
          </Card>

          <Card className="p-4 shadow-card rounded-2xl">
            <div className="text-center">
              <div className="text-2xl font-bold text-success">{campaign.replyCount.toLocaleString()}</div>
              <div className="text-sm text-muted-foreground">Replies</div>
              <div className="text-xs text-muted-foreground">
                {calculateRate(campaign.replyCount, campaign.sentCount)}
              </div>
            </div>
          </Card>

          <Card className="p-4 shadow-card rounded-2xl">
            <div className="text-center">
              <div className="text-2xl font-bold text-destructive">{campaign.bounceCount.toLocaleString()}</div>
              <div className="text-sm text-muted-foreground">Bounces</div>
              <div className="text-xs text-muted-foreground">
                {calculateRate(campaign.bounceCount, campaign.sentCount)}
              </div>
            </div>
          </Card>
        </div>

        {/* Chart */}
        <Card className="p-6 shadow-card rounded-2xl">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold">Emails Sent Per Day</h2>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="w-4 h-4" />
              Last 14 days
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={campaign.stats.sentByDay}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(value) => format(new Date(value), 'dd/MM')}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(value) => format(new Date(value), 'dd MMMM yyyy', { locale: nl })}
                  formatter={(value) => [`${value} emails`, 'Sent']}
                />
                <Line 
                  type="monotone" 
                  dataKey="sent" 
                  stroke="hsl(var(--primary))" 
                  strokeWidth={2}
                  dot={{ fill: "hsl(var(--primary))", strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Messages Table */}
          <Card className="lg:col-span-2 shadow-card rounded-2xl overflow-hidden">
            <div className="p-6 border-b">
              <h2 className="text-xl font-bold">Recent Messages</h2>
            </div>
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/30">
                  <TableHead>Recipient</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Sent</TableHead>
                  <TableHead>Last Activity</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {messages.slice(0, 10).map((message) => (
                  <TableRow key={message.id} className="hover:bg-muted/20">
                    <TableCell>
                      <div>
                        <div className="font-medium">{message.leadEmail}</div>
                        {message.leadCompany && (
                          <div className="text-sm text-muted-foreground">{message.leadCompany}</div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={messageStatusColors[message.status]}>
                        {message.status}
                      </Badge>
                      {message.isFollowUp && (
                        <Badge variant="outline" className="ml-1 text-xs">Follow-up</Badge>
                      )}
                    </TableCell>
                    <TableCell>{formatDate(message.sentAt)}</TableCell>
                    <TableCell>
                      {message.repliedAt ? formatDate(message.repliedAt) :
                       message.clickedAt ? formatDate(message.clickedAt) :
                       message.openedAt ? formatDate(message.openedAt) :
                       message.deliveredAt ? formatDate(message.deliveredAt) :
                       '-'}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        {(message.status === MessageStatus.FAILED || message.status === MessageStatus.BOUNCED) && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0"
                            onClick={() => handleResendMessage(message.id)}
                          >
                            <RotateCcw className="w-3 h-3" />
                          </Button>
                        )}
                        
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 w-6 p-0"
                              onClick={() => setSelectedMessage(message)}
                            >
                              <Eye className="w-3 h-3" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                            <DialogHeader>
                              <DialogTitle>Message Details</DialogTitle>
                              <DialogDescription>
                                View email content and delivery information
                              </DialogDescription>
                            </DialogHeader>
                            {selectedMessage && (
                              <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-4 text-sm">
                                  <div>
                                    <span className="font-medium">To:</span> {selectedMessage.leadEmail}
                                  </div>
                                  <div>
                                    <span className="font-medium">Status:</span> {selectedMessage.status}
                                  </div>
                                  <div>
                                    <span className="font-medium">Sent:</span> {formatDate(selectedMessage.sentAt)}
                                  </div>
                                  <div>
                                    <span className="font-medium">Attempts:</span> {selectedMessage.attempts}
                                  </div>
                                </div>
                                <div>
                                  <h4 className="font-medium mb-2">Email Content</h4>
                                  <Card className="p-4 bg-muted/30 max-h-64 overflow-y-auto">
                                    <pre className="whitespace-pre-wrap text-sm">{selectedMessage.templateSnapshot}</pre>
                                  </Card>
                                </div>
                                {selectedMessage.errorMessage && (
                                  <div>
                                    <h4 className="font-medium mb-2 text-destructive">Error Details</h4>
                                    <Card className="p-4 bg-destructive/5 border-destructive/20">
                                      <p className="text-sm text-destructive">{selectedMessage.errorMessage}</p>
                                    </Card>
                                  </div>
                                )}
                              </div>
                            )}
                          </DialogContent>
                        </Dialog>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>

          {/* Follow-up Panel */}
          <Card className="p-6 shadow-card rounded-2xl">
            <h2 className="text-xl font-bold mb-4">Follow-up Status</h2>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
                <div>
                  <div className="font-medium">Follow-ups Enabled</div>
                  <div className="text-sm text-muted-foreground">
                    {campaign.settings.followUp.enabled ? 'Yes' : 'No'}
                  </div>
                </div>
                <div className={`w-3 h-3 rounded-full ${campaign.settings.followUp.enabled ? 'bg-accent' : 'bg-muted'}`} />
              </div>

              {campaign.settings.followUp.enabled && (
                <>
                  <div className="text-sm space-y-2">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Delay:</span>
                      <span className="font-medium">{campaign.settings.followUp.days} days</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Scheduled:</span>
                      <span className="font-medium">{campaign.stats.followUpCount}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Attachment required:</span>
                      <span className="font-medium">{campaign.settings.followUp.attachmentRequired ? 'Yes' : 'No'}</span>
                    </div>
                  </div>

                  <div className="pt-4 border-t">
                    <h3 className="font-medium mb-2">Today's Activity</h3>
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-primary" />
                      <span className="text-sm">{campaign.stats.sentToday} emails sent today</span>
                    </div>
                  </div>
                </>
              )}
            </div>
          </Card>
        </div>

        {/* Replies Panel - Full Width */}
        <RepliesPanel campaignId={campaign.id} campaignName={campaign.name} />
      </div>
    </div>
  );
}