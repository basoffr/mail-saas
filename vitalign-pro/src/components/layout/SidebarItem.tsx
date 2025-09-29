import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SidebarItemProps {
  href: string;
  icon: LucideIcon;
  label: string;
  collapsed?: boolean;
  badge?: string | number;
}

export const SidebarItem: React.FC<SidebarItemProps> = ({
  href,
  icon: Icon,
  label,
  collapsed = false,
  badge
}) => {
  const location = useLocation();
  const isActive = location.pathname === href || location.pathname.startsWith(href + '/');

  const buttonContent = (
    <Button
      variant="ghost"
      size={collapsed ? "icon" : "default"}
      className={cn(
        "w-full justify-start gap-3 h-10 px-3",
        collapsed && "px-2 justify-center",
        isActive && "bg-sidebar-accent text-sidebar-accent-foreground font-medium",
        "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
        "transition-colors duration-200"
      )}
      asChild
    >
      <Link to={href} aria-current={isActive ? "page" : undefined}>
        <Icon className="h-4 w-4 shrink-0" />
        {!collapsed && (
          <>
            <span className="truncate">{label}</span>
            {badge && (
              <span className="ml-auto text-xs bg-sidebar-primary text-sidebar-primary-foreground px-1.5 py-0.5 rounded-full">
                {badge}
              </span>
            )}
          </>
        )}
      </Link>
    </Button>
  );

  if (collapsed) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          {buttonContent}
        </TooltipTrigger>
        <TooltipContent side="right" className="flex items-center gap-2">
          {label}
          {badge && (
            <span className="text-xs bg-primary text-primary-foreground px-1.5 py-0.5 rounded-full">
              {badge}
            </span>
          )}
        </TooltipContent>
      </Tooltip>
    );
  }

  return buttonContent;
};
