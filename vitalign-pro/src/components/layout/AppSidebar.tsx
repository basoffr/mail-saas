import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sheet, SheetContent } from '@/components/ui/sheet';
import { Separator } from '@/components/ui/separator';
import { 
  Contact2, 
  Send, 
  FileCode2, 
  FolderUp, 
  BarChart3, 
  Settings, 
  ChevronsLeft, 
  ChevronsRight,
  Mail
} from 'lucide-react';
import { SidebarItem } from './SidebarItem';
import { SidebarFooter } from './SidebarFooter';
import { cn } from '@/lib/utils';

interface AppSidebarProps {
  collapsed?: boolean;
  onToggle?: (collapsed: boolean) => void;
  badges?: {
    window?: string;
    throttle?: string;
    tz?: string;
    version?: string;
  };
  className?: string;
}

interface MobileSidebarProps extends AppSidebarProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const navigationItems = [
  { href: '/leads', icon: Contact2, label: 'Leads' },
  { href: '/campaigns', icon: Send, label: 'Campagnes' },
  { href: '/templates', icon: FileCode2, label: 'Templates' },
  { href: '/reports', icon: FolderUp, label: 'Rapporten' },
  { href: '/stats', icon: BarChart3, label: 'Statistieken' },
  { href: '/inbox', icon: Mail, label: 'Inbox' },
  { href: '/settings', icon: Settings, label: 'Instellingen' },
];

const STORAGE_KEY = 'ui.sidebar.collapsed';

export const AppSidebar: React.FC<AppSidebarProps> = ({
  collapsed: controlledCollapsed,
  onToggle,
  badges = {
    window: 'Ma–Vr 08:00–17:00',
    throttle: '1/20m per domein',
    tz: 'Europe/Amsterdam',
    version: 'MVP v0.1'
  },
  className
}) => {
  const [internalCollapsed, setInternalCollapsed] = useState(() => {
    if (controlledCollapsed !== undefined) return controlledCollapsed;
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : false;
  });

  const collapsed = controlledCollapsed !== undefined ? controlledCollapsed : internalCollapsed;

  useEffect(() => {
    if (controlledCollapsed === undefined) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(internalCollapsed));
    }
  }, [internalCollapsed, controlledCollapsed]);

  const handleToggle = () => {
    const newCollapsed = !collapsed;
    if (onToggle) {
      onToggle(newCollapsed);
    } else {
      setInternalCollapsed(newCollapsed);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if ((event.ctrlKey || event.metaKey) && event.key === 'b') {
      event.preventDefault();
      handleToggle();
    }
  };

  return (
    <aside 
      className={cn(
        "sticky top-0 h-screen bg-sidebar-background border-r border-sidebar-border transition-all duration-300 ease-in-out",
        collapsed ? "w-[72px]" : "w-60",
        "hidden md:flex flex-col",
        className
      )}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3 h-14">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded bg-sidebar-primary flex items-center justify-center">
              <span className="text-xs font-bold text-sidebar-primary-foreground">M</span>
            </div>
            <span className="font-semibold text-sidebar-foreground">Mail Dashboard</span>
          </div>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={handleToggle}
          className="h-8 w-8 hover:bg-sidebar-accent"
          aria-label={collapsed ? "Sidebar uitklappen" : "Sidebar inklappen"}
        >
          {collapsed ? (
            <ChevronsRight className="h-4 w-4" />
          ) : (
            <ChevronsLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      <Separator className="bg-sidebar-border" />

      {/* Navigation */}
      <ScrollArea className="flex-1 px-3">
        <nav className="space-y-1 py-3" role="navigation" aria-label="Hoofdnavigatie">
          {navigationItems.map((item) => (
            <SidebarItem
              key={item.href}
              href={item.href}
              icon={item.icon}
              label={item.label}
              collapsed={collapsed}
            />
          ))}
        </nav>
      </ScrollArea>

      {/* Footer */}
      <SidebarFooter collapsed={collapsed} badges={badges} />
    </aside>
  );
};

export const MobileSidebar: React.FC<MobileSidebarProps> = ({
  open,
  onOpenChange,
  badges,
  ...props
}) => {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="left" className="w-60 p-0 bg-sidebar-background">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center gap-2 p-3 h-14 border-b border-sidebar-border">
            <div className="h-6 w-6 rounded bg-sidebar-primary flex items-center justify-center">
              <span className="text-xs font-bold text-sidebar-primary-foreground">M</span>
            </div>
            <span className="font-semibold text-sidebar-foreground">Mail Dashboard</span>
          </div>

          {/* Navigation */}
          <ScrollArea className="flex-1 px-3">
            <nav className="space-y-1 py-3" role="navigation" aria-label="Hoofdnavigatie">
              {navigationItems.map((item) => (
                <SidebarItem
                  key={item.href}
                  href={item.href}
                  icon={item.icon}
                  label={item.label}
                  collapsed={false}
                />
              ))}
            </nav>
          </ScrollArea>

          {/* Footer */}
          <SidebarFooter collapsed={false} badges={badges} />
        </div>
      </SheetContent>
    </Sheet>
  );
};
