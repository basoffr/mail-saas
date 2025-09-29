import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
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
  RefreshCw, 
  CheckCheck, 
  Mail,
  AlertTriangle,
  Eye,
  Loader2,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { InboxMessageOut } from '@/types/inbox';
import { inboxService } from '@/services/inbox';
import { useToast } from '@/hooks/use-toast';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';

interface RepliesPanelProps {
  campaignId: string;
  campaignName?: string;
}

const ITEMS_PER_PAGE = 10; // Smaller for panel

export function RepliesPanel({ campaignId, campaignName }: RepliesPanelProps) {
  const { toast } = useToast();
  
  const [messages, setMessages] = useState<InboxMessageOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchLoading, setFetchLoading] = useState(false);
  const [selectedMessages, setSelectedMessages] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [selectedMessage, setSelectedMessage] = useState<InboxMessageOut | null>(null);

  const fetchMessages = async () => {
    setLoading(true);
    try {
      const response = await inboxService.getMessages({
        campaignId,
        page,
        pageSize: ITEMS_PER_PAGE
      });
      setMessages(response.items);
      setTotal(response.total);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load replies',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleFetch = async () => {
    setFetchLoading(true);
    try {
      await inboxService.fetchMessages();
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
  }, [campaignId, page]);

  const totalPages = Math.ceil(total / ITEMS_PER_PAGE);

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'dd/MM HH:mm', { locale: nl });
  };

  const getStatusBadge = (message: InboxMessageOut) => {
    if (!message.isRead) {
      return <Badge className="bg-blue-100 text-blue-800 text-xs">Nieuw</Badge>;
    }
    return <Badge variant="outline" className="text-xs">Gelezen</Badge>;
  };

  return (
    <Card className="p-6 shadow-card rounded-2xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold">Replies</h2>
          <p className="text-sm text-muted-foreground">
            Inkomende berichten voor {campaignName || 'deze campagne'}
          </p>
        </div>
        <Button
          onClick={handleFetch}
          disabled={fetchLoading}
          size="sm"
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

      {selectedMessages.size > 0 && (
        <div className="flex items-center gap-4 p-3 bg-primary/5 rounded-lg border border-primary/20 mb-4">
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

      <div className="rounded-lg border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/30">
              <TableHead className="w-8">
                <Checkbox
                  checked={messages.length > 0 && selectedMessages.size === messages.length}
                  onCheckedChange={handleSelectAll}
                />
              </TableHead>
              <TableHead className="w-20">Datum</TableHead>
              <TableHead>Van</TableHead>
              <TableHead>Onderwerp</TableHead>
              <TableHead className="w-16">Status</TableHead>
              <TableHead className="w-8"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell><div className="h-4 bg-muted animate-pulse rounded" /></TableCell>
                  <TableCell><div className="h-4 bg-muted animate-pulse rounded w-16" /></TableCell>
                  <TableCell><div className="h-4 bg-muted animate-pulse rounded w-24" /></TableCell>
                  <TableCell><div className="h-4 bg-muted animate-pulse rounded w-32" /></TableCell>
                  <TableCell><div className="h-4 bg-muted animate-pulse rounded w-12" /></TableCell>
                  <TableCell><div className="h-4 bg-muted animate-pulse rounded w-6" /></TableCell>
                </TableRow>
              ))
            ) : messages.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-6">
                  <div className="text-muted-foreground">
                    <Mail className="w-8 h-8 mx-auto mb-2 opacity-20" />
                    <p className="text-sm font-medium">Geen replies gevonden</p>
                    <p className="text-xs">Klik op "Ophalen" om nieuwe berichten op te halen.</p>
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
                  <TableCell className="text-xs">
                    {formatDate(message.receivedAt)}
                  </TableCell>
                  <TableCell>
                    <div className="max-w-32">
                      <div className="font-medium text-sm truncate">
                        {message.fromName || message.fromEmail}
                      </div>
                      {message.fromName && (
                        <div className="text-xs text-muted-foreground truncate">
                          {message.fromEmail}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className={`${!message.isRead ? 'font-semibold' : ''} max-w-48`}>
                      <div className="text-sm truncate">{message.subject}</div>
                      <div className="text-xs text-muted-foreground truncate">
                        {message.snippet}
                      </div>
                    </div>
                    {message.weakLink && (
                      <Badge variant="outline" className="text-xs text-orange-600 mt-1">
                        onzeker
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    {getStatusBadge(message)}
                  </TableCell>
                  <TableCell>
                    <Sheet>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => setSelectedMessage(message)}
                      >
                        <Eye className="w-3 h-3" />
                      </Button>
                      <SheetContent className="w-[400px] sm:w-[540px]">
                        <SheetHeader>
                          <SheetTitle>Reply Details</SheetTitle>
                          <SheetDescription>
                            View reply message details
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
      </div>

      {/* Pagination */}
      {total > ITEMS_PER_PAGE && (
        <div className="flex items-center justify-between mt-4">
          <div className="text-xs text-muted-foreground">
            Showing {((page - 1) * ITEMS_PER_PAGE) + 1} to{' '}
            {Math.min(page * ITEMS_PER_PAGE, total)} of {total} replies
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(prev => prev - 1)}
              disabled={page <= 1}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <div className="text-xs">
              {page} / {totalPages}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(prev => prev + 1)}
              disabled={page >= totalPages}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
}

// Message Details Component (simplified for panel)
function MessageDetails({ message }: { message: InboxMessageOut }) {
  const { toast } = useToast();

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
    <div className="space-y-4 py-6">
      {/* Header */}
      <div className="space-y-3">
        <div>
          <label className="text-sm font-medium text-muted-foreground">Van</label>
          <p className="text-lg">{message.fromName || message.fromEmail}</p>
          {message.fromName && (
            <p className="text-sm text-muted-foreground">{message.fromEmail}</p>
          )}
        </div>
        
        <div>
          <label className="text-sm font-medium text-muted-foreground">Onderwerp</label>
          <p className="font-medium">{message.subject}</p>
        </div>
        
        <div>
          <label className="text-sm font-medium text-muted-foreground">Ontvangen</label>
          <p className="text-sm">{formatDate(message.receivedAt)}</p>
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

      {/* Lead info */}
      {message.linkedLeadId && (
        <div>
          <label className="text-sm font-medium text-muted-foreground">Lead</label>
          <p className="text-sm">{message.linkedLeadEmail}</p>
        </div>
      )}

      {/* Snippet */}
      <div>
        <label className="text-sm font-medium text-muted-foreground mb-2 block">Bericht</label>
        <Card className="p-3 max-h-32 overflow-y-auto">
          <p className="whitespace-pre-wrap text-sm">{message.snippet}</p>
        </Card>
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-4 border-t">
        <Button
          variant="outline"
          size="sm"
          onClick={handleMarkAsRead}
        >
          <CheckCheck className="w-4 h-4 mr-2" />
          {message.isRead ? 'Markeer als ongelezen' : 'Markeer als gelezen'}
        </Button>
      </div>
    </div>
  );
}
