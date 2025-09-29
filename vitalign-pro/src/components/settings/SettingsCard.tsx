import React from 'react';
import { Card } from '@/components/ui/card';

interface SettingsCardProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  loading?: boolean;
}

export const SettingsCard: React.FC<SettingsCardProps> = ({
  title,
  description,
  children,
  loading = false
}) => {
  if (loading) {
    return (
      <Card className="p-6 shadow-card rounded-2xl">
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="h-6 bg-muted animate-pulse rounded w-48" />
            {description && <div className="h-4 bg-muted animate-pulse rounded w-64" />}
          </div>
          <div className="space-y-3">
            <div className="h-10 bg-muted animate-pulse rounded" />
            <div className="h-10 bg-muted animate-pulse rounded" />
            <div className="h-10 bg-muted animate-pulse rounded" />
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6 shadow-card rounded-2xl">
      <div className="space-y-6">
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-foreground">{title}</h3>
          {description && (
            <p className="text-sm text-muted-foreground">{description}</p>
          )}
        </div>
        <div className="space-y-4">
          {children}
        </div>
      </div>
    </Card>
  );
};
