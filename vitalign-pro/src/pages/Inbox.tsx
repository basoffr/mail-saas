import React, { useState, useEffect } from 'react';
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
} from '@/components/ui/sheet';
import { 
  Search, 
  Filter, 
  RefreshCw, 
  CheckCheck, 
  Mail,
  AlertTriangle,
  Eye,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Settings as SettingsIcon
} from 'lucide-react';
import { InboxMessageOut, InboxQuery, MailAccountOut } from '@/types/inbox';
import { inboxService } from '@/services/inbox';
import { useToast } from '@/hooks/use-toast';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';

const ITEMS_PER_PAGE = 25;

export default function Inbox() {
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [messages, setMessages] = useState<InboxMessageOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchLoading, setFetchLoading] = useState(false);
  const [selectedMessages, setSelectedMessages] = useState<Set<string>>(new Set());
  const [query, setQuery] = useState<InboxQuery>({
    page: 1,
    pageSize: ITEMS_PER_PAGE
  });
  const [total, setTotal] = useState(0);
  const [selectedMessage, setSelectedMessage] = useState<InboxMessageOut | null>(null);
  const [accounts, setAccounts] = useState<MailAccountOut[]>([]);

  const fetchMessages = async () => {
    setLoading(true);
    try {
      const response = await inboxService.getMessages(query);
      setMessages(response?.items || []);
      setTotal(response?.total || 0);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load messages',
        variant: 'destructive'
      });
      setMessages([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const fetchAccounts = async () => {
    try {
      const response = await inboxService.getAccounts();
      // Response is array directly after our fix, not {items: []}
      setAccounts(Array.isArray(response) ? response : []);
    } catch (error) {
      console.error('Failed to load accounts:', error);
      setAccounts([]);
    }
  };

  const handleFetch = async () => {
    setFetchLoading(true);
    try {
      await inboxService.startFetch();
      await fetchMessages();
      toast({
        title: 'Success',
        description: 'Messages fetched successfully',
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to fetch messages',
        variant: 'destructive'
      });
    } finally {
      setFetchLoading(false);
    }
  };

  const handleSelectAll = () => {
    if (selectedMessages.size === messages.length) {
      setSelectedMessages(new Set());
    } else {
      setSelectedMessages(new Set(messages.map(msg => msg.id)));
    }
  };

  const handleSelectMessage = (messageId: string) => {
    const newSelected = new Set(selectedMessages);
    if (newSelected.has(messageId)) {
      newSelected.delete(messageId);
    } else {
      newSelected.add(messageId);
    }
    setSelectedMessages(newSelected);
  };

  const handleMarkAsRead = async (messageIds: string[]) => {
    try {
      await Promise.all(messageIds.map(id => inboxService.markAsRead(id)));
      await fetchMessages();
      setSelectedMessages(new Set());
      toast({
        title: 'Success',
        description: `${messageIds.length} message${messageIds.length > 1 ? 's' : ''} marked as read`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to mark messages as read',
        variant: 'destructive'
      });
    }
  };

  useEffect(() => {
    fetchMessages();
  }, [query]);

  useEffect(() => {
    fetchAccounts();
  }, []);

  const totalPages = Math.ceil(total / ITEMS_PER_PAGE);

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'dd/MM/yyyy HH:mm', { locale: nl });
  };

  const getStatusBadge = (message: InboxMessageOut) => {
    if (!message.isRead) {
      return <Badge className="bg-blue-100 text-blue-800">Nieuw</Badge>;
    }
    return <Badge variant="outline">Gelezen</Badge>;
  };

  const activeAccounts = accounts.filter(acc => acc.active);

  return (
    <div className="min-h-screen bg-gradient-subtle p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Inbox</h1>
            <p className="text-muted-foreground">Manage incoming email replies</p>
          </div>
          <div className="flex gap-3">
            <Button
              onClick={handleFetch}
              disabled={fetchLoading}
              className="bg-gradient-primary hover:shadow-glow"
            >
              {fetchLoading ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4 mr-2" />
              )}
              Ophalen
            </Button>
          </div>
        </div>

        {/* No accounts warning */}
        {activeAccounts.length === 0 && (
          <Card className="p-6 shadow-card rounded-2xl border-orange-200 bg-orange-50">
            <div className="flex items-center gap-4">
              <AlertTriangle className="w-8 h-8 text-orange-600" />
              <div className="flex-1">
                <h3 className="font-medium text-orange-900">Geen actieve IMAP accounts</h3>
                <p className="text-sm text-orange-700">
                  Configureer eerst IMAP accounts om berichten op te kunnen halen.
                </p>
              </div>
              <Button
                variant="outline"
                onClick={() => navigate('/settings')}
                className="border-orange-300 text-orange-700 hover:bg-orange-100"
              >
                <SettingsIcon className="w-4 h-4 mr-2" />
                Configureer Accounts
              </Button>
            </div>
          </Card>
        )}

        {/* Filters & Search */}
        <Card className="p-6 shadow-card rounded-2xl">
          <div className="flex flex-col gap-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search by sender or subject..."
                    className="pl-10"
                    value={query.q || ''}
                    onChange={(e) => setQuery(prev => ({ ...prev, q: e.target.value, page: 1 }))}
                  />
                </div>
              </div>
              
              <Select
                value={query.unread === undefined ? 'all' : query.unread ? 'unread' : 'read'}
                onValueChange={(value) => {
                  const unread = value === 'all' ? undefined : value === 'unread';
                  setQuery(prev => ({ ...prev, unread, page: 1 }));
                }}
              >
                <SelectTrigger className="w-[140px]">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent className="bg-popover border border-border">
                  <SelectItem value="all">Alle</SelectItem>
                  <SelectItem value="unread">Ongelezen</SelectItem>
                  <SelectItem value="read">Gelezen</SelectItem>
                </SelectContent>
              </Select>

              <Select
                value={query.accountId || 'all'}
                onValueChange={(value) => {
                  const accountId = value === 'all' ? undefined : value;
                  setQuery(prev => ({ ...prev, accountId, page: 1 }));
                }}
              >
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Account" />
                </SelectTrigger>
                <SelectContent className="bg-popover border border-border">
                  <SelectItem value="all">Alle Accounts</SelectItem>
                  {accounts.map(account => (
                    <SelectItem key={account.id} value={account.id}>
                      {account.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedMessages.size > 0 && (
              <div className="flex items-center gap-4 p-4 bg-primary/5 rounded-lg border border-primary/20">
                <span className="text-sm font-medium">
                  {selectedMessages.size} bericht{selectedMessages.size > 1 ? 'en' : ''} geselecteerd
                </span>
                <Button
                  size="sm"
                  onClick={() => handleMarkAsRead(Array.from(selectedMessages))}
                  className="bg-gradient-accent hover:shadow-glow"
                >
                  <CheckCheck className="w-4 h-4 mr-2" />
                  Markeer als gelezen
                </Button>
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
                    checked={messages.length > 0 && selectedMessages.size === messages.length}
                    onCheckedChange={handleSelectAll}
                  />
                </TableHead>
                <TableHead>Datum</TableHead>
                <TableHead>Van</TableHead>
                <TableHead>Onderwerp</TableHead>
                <TableHead>Campagne</TableHead>
                <TableHead>Lead</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Account</TableHead>
                <TableHead className="w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-24" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-32" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-40" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-20" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-20" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-16" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-20" /></TableCell>
                    <TableCell><div className="h-4 bg-muted animate-pulse rounded w-6" /></TableCell>
                  </TableRow>
                ))
              ) : messages.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center py-8">
                    <div className="text-muted-foreground">
                      <Mail className="w-12 h-12 mx-auto mb-4 opacity-20" />
                      <p className="text-lg font-medium">Geen berichten gevonden</p>
                      <p className="text-sm">
                        {activeAccounts.length === 0 
                          ? 'Configureer eerst IMAP accounts om berichten op te halen.'
                          : 'Klik op "Ophalen" om nieuwe berichten op te halen.'
                        }
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                messages.map((message) => (
                  <TableRow key={message.id} className="hover:bg-muted/20">
                    <TableCell>
                      <Checkbox
                        checked={selectedMessages.has(message.id)}
                        onCheckedChange={() => handleSelectMessage(message.id)}
                      />
                    </TableCell>
                    <TableCell className="text-sm">
                      {formatDate(message.receivedAt)}
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">
                          {message.fromName || message.fromEmail}
                        </div>
                        {message.fromName && (
                          <div className="text-sm text-muted-foreground">
                            {message.fromEmail}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className={`${!message.isRead ? 'font-semibold' : ''}`}>
                        {message.subject}
                      </div>
                      <div className="text-sm text-muted-foreground truncate max-w-xs">
                        {message.snippet}
                      </div>
                    </TableCell>
                    <TableCell>
                      {message.linkedCampaignId ? (
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary" className="text-xs">
                            {message.linkedCampaignName}
                          </Badge>
                          {message.weakLink && (
                            <Badge variant="outline" className="text-xs text-orange-600">
                              onzeker
                            </Badge>
                          )}
                        </div>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      {message.linkedLeadId ? (
                        <Badge variant="outline" className="text-xs">
                          {message.linkedLeadEmail}
                        </Badge>
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(message)}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {message.accountLabel}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Sheet>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0"
                          onClick={() => setSelectedMessage(message)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <SheetContent className="w-[400px] sm:w-[540px]">
                          <SheetHeader>
                            <SheetTitle>Bericht Details</SheetTitle>
                            <SheetDescription>
                              View message details and headers
                            </SheetDescription>
                          </SheetHeader>
                          {selectedMessage && <MessageDetails message={selectedMessage} />}
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
                {Math.min((query.page || 1) * ITEMS_PER_PAGE, total)} of {total} messages
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
    </div>
  );
}

// Message Details Component
function MessageDetails({ message }: { message: InboxMessageOut }) {
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleMarkAsRead = async () => {
    try {
      await inboxService.markAsRead(message.id);
      message.isRead = !message.isRead; // Optimistic update
      toast({
        title: 'Success',
        description: `Message marked as ${message.isRead ? 'read' : 'unread'}`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update message status',
        variant: 'destructive'
      });
    }
  };

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'dd MMMM yyyy \'om\' HH:mm', { locale: nl });
  };

  return (
    <div className="space-y-6 py-6">
      {/* Header */}
      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium text-muted-foreground">Van</label>
          <p className="text-lg">{message.fromName || message.fromEmail}</p>
          {message.fromName && (
            <p className="text-sm text-muted-foreground">{message.fromEmail}</p>
          )}
        </div>
        
        <div>
          <label className="text-sm font-medium text-muted-foreground">Onderwerp</label>
          <p className="text-lg font-medium">{message.subject}</p>
        </div>
        
        <div>
          <label className="text-sm font-medium text-muted-foreground">Ontvangen</label>
          <p>{formatDate(message.receivedAt)}</p>
        </div>
      </div>

      {/* Badges */}
      <div className="flex flex-wrap gap-2">
        {!message.isRead && <Badge className="bg-blue-100 text-blue-800">Nieuw</Badge>}
        {message.weakLink && (
          <Badge variant="outline" className="text-orange-600 border-orange-300">
            <AlertTriangle className="w-3 h-3 mr-1" />
            Onzekere koppeling
          </Badge>
        )}
        {message.encodingIssue && (
          <Badge variant="outline" className="text-red-600 border-red-300">
            Encoding issue
          </Badge>
        )}
      </div>

      {/* Links */}
      {(message.linkedCampaignId || message.linkedLeadId) && (
        <div className="space-y-2">
          <label className="text-sm font-medium text-muted-foreground">Gekoppeld aan</label>
          <div className="flex gap-2">
            {message.linkedCampaignId && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate(`/campaigns/${message.linkedCampaignId}`)}
              >
                Campagne: {message.linkedCampaignName}
              </Button>
            )}
            {message.linkedLeadId && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/leads')}
              >
                Lead: {message.linkedLeadEmail}
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Headers */}
      <div>
        <label className="text-sm font-medium text-muted-foreground mb-2 block">Headers</label>
        <Card className="p-4 bg-muted/30">
          <div className="space-y-2 text-sm font-mono">
            <div><strong>Message-ID:</strong> {message.messageId || 'N/A'}</div>
            <div><strong>In-Reply-To:</strong> {message.inReplyTo || 'N/A'}</div>
            <div><strong>References:</strong> {message.references?.join(', ') || 'N/A'}</div>
            <div><strong>To:</strong> {message.toEmail || 'N/A'}</div>
          </div>
        </Card>
      </div>

      {/* Snippet */}
      <div>
        <label className="text-sm font-medium text-muted-foreground mb-2 block">Bericht</label>
        <Card className="p-4 max-h-64 overflow-y-auto">
          <p className="whitespace-pre-wrap text-sm">{message.snippet}</p>
        </Card>
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-4 border-t">
        <Button
          variant="outline"
          onClick={handleMarkAsRead}
        >
          <CheckCheck className="w-4 h-4 mr-2" />
          {message.isRead ? 'Markeer als ongelezen' : 'Markeer als gelezen'}
        </Button>
      </div>
    </div>
  );
}
