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
import { Input } from '@/components/ui/input';
import { Calendar, RefreshCw, Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
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
  const [currentDay, setCurrentDay] = useState(1);
  const [jumpToDay, setJumpToDay] = useState('');
  const { toast } = useToast();

  useEffect(() => {
    fetchSchedule(currentDay);
  }, [campaignId, selectedDomain, currentDay]);

  const fetchSchedule = async (day: number) => {
    setLoading(true);
    try {
      const options: any = { day };
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

  const handlePreviousDay = () => {
    if (currentDay > 1) {
      setCurrentDay(currentDay - 1);
    }
  };

  const handleNextDay = () => {
    if (schedule && currentDay < (schedule.totalDays || 1)) {
      setCurrentDay(currentDay + 1);
    }
  };

  const handleJumpToDay = () => {
    const day = parseInt(jumpToDay);
    if (day && day >= 1 && schedule && day <= (schedule.totalDays || 1)) {
      setCurrentDay(day);
      setJumpToDay('');
    } else {
      toast({
        title: 'Ongeldige dag',
        description: `Voer een getal in tussen 1 en ${schedule?.totalDays || 1}`,
        variant: 'destructive',
      });
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
            <Badge variant="outline">{schedule.totalCount} messages totaal</Badge>
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
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => fetchSchedule(currentDay)}
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* V2.3: Per-Day Pagination Controls */}
        <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePreviousDay}
              disabled={currentDay === 1 || loading}
              className="gap-1"
            >
              <ChevronLeft className="w-4 h-4" />
              Vorige Dag
            </Button>
            
            <div className="flex flex-col items-center px-4">
              <div className="text-lg font-semibold text-blue-900">
                Dag {schedule?.currentDay || currentDay} van {schedule?.totalDays || '...'}
              </div>
              {schedule?.dayDate && (
                <div className="text-sm text-blue-700">
                  {format(new Date(schedule.dayDate), 'EEEE d MMMM yyyy', { locale: nl })}
                </div>
              )}
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={handleNextDay}
              disabled={currentDay === (schedule?.totalDays || 1) || loading}
              className="gap-1"
            >
              Volgende Dag
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-sm">
              {schedule?.messagesThisDay || 0} messages deze dag
            </Badge>
            
            <div className="flex items-center gap-2 ml-4">
              <span className="text-sm text-muted-foreground">Spring naar dag:</span>
              <Input
                type="number"
                min="1"
                max={schedule?.totalDays || 1}
                value={jumpToDay}
                onChange={(e) => setJumpToDay(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleJumpToDay()}
                placeholder="Dag #"
                className="w-20"
              />
              <Button 
                size="sm" 
                onClick={handleJumpToDay}
                disabled={!jumpToDay || loading}
              >
                Go
              </Button>
            </div>
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
