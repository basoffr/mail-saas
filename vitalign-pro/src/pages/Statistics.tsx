import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  BarChart3, 
  Mail, 
  MousePointer, 
  AlertTriangle,
  Download,
  Calendar
} from 'lucide-react';
import { KpiCard } from '@/components/stats/KpiCard';
import { TimelineChart } from '@/components/stats/TimelineChart';
import { DomainTable } from '@/components/stats/DomainTable';
import { CampaignTable } from '@/components/stats/CampaignTable';
import { statsService } from '@/services/stats';
import { StatsSummary, StatsQuery } from '@/types/stats';
import { useToast } from '@/hooks/use-toast';
import { format, subDays } from 'date-fns';

const Statistics = () => {
  const { toast } = useToast();
  const [data, setData] = useState<StatsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [query, setQuery] = useState<StatsQuery>({
    from: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    to: format(new Date(), 'yyyy-MM-dd')
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const summary = await statsService.getSummary(query);
      setData(summary);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load statistics',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (scope: 'global' | 'domain' | 'campaign') => {
    setExporting(true);
    try {
      const csvData = await statsService.exportData({ ...query, scope });
      
      // Create and download CSV file
      const blob = new Blob([csvData], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `statistics-${scope}-${format(new Date(), 'yyyy-MM-dd')}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      toast({
        title: 'Export Successful',
        description: `${scope} statistics exported successfully`,
      });
    } catch (error) {
      toast({
        title: 'Export Failed',
        description: 'Failed to export statistics',
        variant: 'destructive'
      });
    } finally {
      setExporting(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [query]);

  return (
    <div className="min-h-screen bg-gradient-subtle p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <div className="flex items-center gap-3">
              <BarChart3 className="h-6 w-6 text-primary" />
              <h1 className="text-3xl font-bold text-foreground">Statistieken</h1>
            </div>
            <p className="text-muted-foreground">Inzicht in je email campagne prestaties</p>
          </div>
          <Button
            onClick={() => handleExport('global')}
            disabled={exporting || loading}
            className="bg-gradient-primary hover:shadow-glow gap-2"
          >
            <Download className="w-4 h-4" />
            Export Global CSV
          </Button>
        </div>

        {/* Filters */}
        <Card className="p-6 shadow-card rounded-2xl">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="from-date">Van Datum</Label>
                <Input
                  id="from-date"
                  type="date"
                  value={query.from || ''}
                  onChange={(e) => setQuery(prev => ({ ...prev, from: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="to-date">Tot Datum</Label>
                <Input
                  id="to-date"
                  type="date"
                  value={query.to || ''}
                  onChange={(e) => setQuery(prev => ({ ...prev, to: e.target.value }))}
                />
              </div>
            </div>
            <div className="flex items-end">
              <Button
                onClick={fetchData}
                disabled={loading}
                variant="outline"
                className="gap-2"
              >
                <Calendar className="w-4 h-4" />
                Update
              </Button>
            </div>
          </div>
        </Card>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <KpiCard
            title="Totaal Verzonden"
            value={data?.global.totalSent.toLocaleString() || '0'}
            icon={Mail}
            loading={loading}
          />
          <KpiCard
            title="Open Rate"
            value={data ? `${(data.global.openRate * 100).toFixed(1)}%` : '0%'}
            icon={MousePointer}
            loading={loading}
          />
          <KpiCard
            title="Bounces"
            value={data?.global.bounces.toLocaleString() || '0'}
            icon={AlertTriangle}
            loading={loading}
          />
        </div>

        {/* Timeline Chart */}
        <TimelineChart
          data={data?.timeline || []}
          loading={loading}
        />

        {/* Tables */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <DomainTable
            data={data?.domains || []}
            loading={loading}
            onExport={() => handleExport('domain')}
          />
          <CampaignTable
            data={data?.campaigns || []}
            loading={loading}
            onExport={() => handleExport('campaign')}
          />
        </div>
      </div>
    </div>
  );
};

export default Statistics;
