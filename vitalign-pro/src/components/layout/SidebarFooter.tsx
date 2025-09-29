import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Plus } from 'lucide-react';

interface SidebarFooterProps {
  collapsed?: boolean;
  badges?: {
    window?: string;
    throttle?: string;
    tz?: string;
    version?: string;
  };
}

export const SidebarFooter: React.FC<SidebarFooterProps> = ({
  collapsed = false,
  badges = {}
}) => {
  return (
    <div className="mt-auto p-3 space-y-3">
      <Separator className="bg-sidebar-border" />
      
      {/* New Campaign Button */}
      <Button
        size={collapsed ? "icon" : "sm"}
        className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
        asChild
      >
        <Link to="/campaigns/new">
          <Plus className="h-4 w-4" />
          {!collapsed && <span className="ml-2">Nieuwe Campagne</span>}
        </Link>
      </Button>

      {/* Status Badges */}
      {!collapsed && (badges.window || badges.throttle || badges.tz) && (
        <div className="space-y-1">
          {badges.window && (
            <Badge variant="secondary" className="w-full justify-center text-xs">
              {badges.window}
            </Badge>
          )}
          {badges.throttle && (
            <Badge variant="secondary" className="w-full justify-center text-xs">
              {badges.throttle}
            </Badge>
          )}
          {badges.tz && (
            <Badge variant="outline" className="w-full justify-center text-xs">
              TZ: {badges.tz}
            </Badge>
          )}
        </div>
      )}

      {/* Version Badge */}
      {badges.version && (
        <div className="flex justify-center">
          <Badge variant="outline" className="text-xs text-muted-foreground">
            {badges.version}
          </Badge>
        </div>
      )}
    </div>
  );
};
