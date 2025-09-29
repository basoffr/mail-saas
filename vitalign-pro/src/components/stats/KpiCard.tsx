import React from 'react';
import { Card } from '@/components/ui/card';
import { LucideIcon } from 'lucide-react';

interface KpiCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  loading?: boolean;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  icon: Icon,
  trend,
  loading = false
}) => {
  if (loading) {
    return (
      <Card className="p-6 shadow-card rounded-2xl">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="h-4 bg-muted animate-pulse rounded w-24" />
            <div className="h-8 bg-muted animate-pulse rounded w-16" />
          </div>
          <div className="h-12 w-12 bg-muted animate-pulse rounded-full" />
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6 shadow-card rounded-2xl hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <div className="flex items-baseline gap-2">
            <p className="text-2xl font-bold text-foreground">{value}</p>
            {trend && (
              <span className={`text-xs font-medium ${
                trend.isPositive ? 'text-success' : 'text-destructive'
              }`}>
                {trend.isPositive ? '+' : ''}{trend.value}%
              </span>
            )}
          </div>
        </div>
        <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
          <Icon className="h-6 w-6 text-primary" />
        </div>
      </div>
    </Card>
  );
};
