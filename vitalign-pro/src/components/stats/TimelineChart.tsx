import React from 'react';
import { Card } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TimelinePoint } from '@/types/stats';
import { format } from 'date-fns';
import { nl } from 'date-fns/locale';

interface TimelineChartProps {
  data: TimelinePoint[];
  loading?: boolean;
  title?: string;
}

export const TimelineChart: React.FC<TimelineChartProps> = ({
  data,
  loading = false,
  title = "Verzonden en Opens per Dag"
}) => {
  if (loading) {
    return (
      <Card className="p-6 shadow-card rounded-2xl">
        <div className="space-y-4">
          <div className="h-6 bg-muted animate-pulse rounded w-48" />
          <div className="h-64 bg-muted animate-pulse rounded" />
        </div>
      </Card>
    );
  }

  // Format data for chart - defensive guard
  const safeData = data ?? [];
  const chartData = safeData.map(point => ({
    ...point,
    formattedDate: format(new Date(point.date), 'dd/MM', { locale: nl })
  }));

  const customTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const date = safeData.find(d => format(new Date(d.date), 'dd/MM', { locale: nl }) === label)?.date;
      const formattedDate = date ? format(new Date(date), 'dd MMMM yyyy', { locale: nl }) : label;
      
      return (
        <div className="bg-popover border border-border rounded-lg p-3 shadow-lg">
          <p className="font-medium text-foreground mb-2">{formattedDate}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="p-6 shadow-card rounded-2xl">
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-foreground">{title}</h3>
        
        {safeData.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <p className="text-lg font-medium">Geen data beschikbaar</p>
              <p className="text-sm">Er zijn nog geen verzendgegevens voor deze periode.</p>
            </div>
          </div>
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis 
                  dataKey="formattedDate" 
                  className="text-xs"
                  tick={{ fontSize: 12 }}
                />
                <YAxis 
                  className="text-xs"
                  tick={{ fontSize: 12 }}
                />
                <Tooltip content={customTooltip} />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="sent" 
                  stroke="hsl(var(--primary))" 
                  strokeWidth={2}
                  name="Verzonden"
                  dot={{ fill: 'hsl(var(--primary))', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: 'hsl(var(--primary))', strokeWidth: 2 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="opens" 
                  stroke="hsl(var(--chart-2))" 
                  strokeWidth={2}
                  name="Opens"
                  dot={{ fill: 'hsl(var(--chart-2))', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: 'hsl(var(--chart-2))', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </Card>
  );
};
