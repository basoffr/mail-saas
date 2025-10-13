import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Calendar, RefreshCw, Loader2 } from 'lucide-react';
import { campaignsService } from '@/services/campaigns';
import { ScheduleResponse, ScheduledMessage } from '@/types/campaign';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';
import { useToast } from '@/hooks/use-toast';

interface ScheduleTimelineProps {
  campaignId: string;
}

const DOMAINS = [
  { value: 'all', label: 'Alle Domeinen' },
  { value: 'punthelder-vindbaarheid.nl', label: 'Vindbaarheid' },
  { value: 'punthelder-seo.nl', label: 'SEO' },
  { value: 'punthelder-zoekmachine.nl', label: 'Zoekmachine' },
  { value: 'punthelder-marketing.nl', label: 'Marketing' },
];

const statusColors: Record<string, string> = {
  queued: 'bg-blue-100 text-blue-800',
  sent: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  canceled: 'bg-gray-100 text-gray-800',
  opened: 'bg-purple-100 text-purple-800',
};

export function ScheduleTimeline({ campaignId }: ScheduleTimelineProps) {
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState('all');
  const { toast } = useToast();

  useEffect(() => {
    fetchSchedule();
  }, [campaignId, selectedDomain]);

  const fetchSchedule = async () => {
    setLoading(true);
    try {
      const options: any = { limit: 200 };
      if (selectedDomain !== 'all') {
        options.domain = selectedDomain;
      }
      
      const data = await campaignsService.getSchedule(campaignId, options);
      setSchedule(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Kon schedule niet laden',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const groupBySlot = (messages: ScheduledMessage[]) => {
    const grouped: Record<string, ScheduledMessage[]> = {};
    messages.forEach((msg) => {
      const slotKey = format(new Date(msg.scheduledAt), 'yyyy-MM-dd HH:mm');
      if (!grouped[slotKey]) {
        grouped[slotKey] = [];
      }
      grouped[slotKey].push(msg);
    });
    return grouped;
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      </Card>
    );
  }

  if (!schedule) {
    return (
      <Card className="p-6">
        <div className="text-center text-muted-foreground">
          Geen schedule data beschikbaar
        </div>
      </Card>
    );
  }

  const groupedSlots = groupBySlot(schedule.slots);

  return (
    <Card className="p-6">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-primary" />
            <h3 className="text-lg font-semibold">Schedule Timeline</h3>
            <Badge variant="outline">{schedule.totalCount} messages</Badge>
          </div>
          <div className="flex items-center gap-2">
            <Select value={selectedDomain} onValueChange={setSelectedDomain}>
              <SelectTrigger className="w-[200px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DOMAINS.map((domain) => (
                  <SelectItem key={domain.value} value={domain.value}>
                    {domain.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={fetchSchedule}>
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Stream Info */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-blue-50 rounded-lg">
            <div className="text-sm font-medium text-blue-900">Stream A (M1, M3)</div>
            <div className="text-xs text-blue-700">
              Slots: {schedule.streams.A.map(m => `:${m.toString().padStart(2, '0')}`).join(', ')}
            </div>
          </div>
          <div className="p-3 bg-purple-50 rounded-lg">
            <div className="text-sm font-medium text-purple-900">Stream B (M2, M4)</div>
            <div className="text-xs text-purple-700">
              Slots: {schedule.streams.B.map(m => `:${m.toString().padStart(2, '0')}`).join(', ')}
            </div>
          </div>
        </div>

        {/* Timeline Table */}
        <div className="border rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[180px]">Tijdslot</TableHead>
                <TableHead className="w-[120px]">Domain</TableHead>
                <TableHead className="w-[80px]">Mail</TableHead>
                <TableHead className="w-[100px]">Alias</TableHead>
                <TableHead className="w-[120px]">Lead ID</TableHead>
                <TableHead className="w-[100px]">Status</TableHead>
                <TableHead>Reden</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Object.entries(groupedSlots).map(([slot, messages]) => (
                <React.Fragment key={slot}>
                  {messages.map((msg, idx) => (
                    <TableRow key={msg.messageId} className={idx === 0 ? 'border-t-2' : ''}>
                      {idx === 0 && (
                        <TableCell 
                          rowSpan={messages.length}
                          className="font-medium bg-gray-50"
                        >
                          <div className="text-sm">
                            {format(new Date(msg.scheduledAt), 'dd MMM yyyy', { locale: nl })}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {format(new Date(msg.scheduledAt), 'HH:mm')}
                          </div>
                          <Badge variant="outline" className="mt-1">
                            {messages.length}x
                          </Badge>
                        </TableCell>
                      )}
                      <TableCell className="text-sm">
                        {msg.domainUsed.split('.')[0].replace('punthelder-', '')}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">M{msg.mailNumber}</Badge>
                      </TableCell>
                      <TableCell className="text-xs">
                        {msg.alias}
                      </TableCell>
                      <TableCell className="text-xs font-mono">
                        {msg.leadId.substring(0, 8)}...
                      </TableCell>
                      <TableCell>
                        <Badge className={statusColors[msg.status] || 'bg-gray-100'}>
                          {msg.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {msg.cancelReason || '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        </div>

        {schedule.slots.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            Geen geplande messages gevonden
          </div>
        )}
      </div>
    </Card>
  );
}
