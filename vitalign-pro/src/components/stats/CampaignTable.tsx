import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ArrowUpDown, Download, ExternalLink } from 'lucide-react';
import { CampaignStats } from '@/types/stats';

interface CampaignTableProps {
  data: CampaignStats[];
  loading?: boolean;
  onExport?: () => void;
}

type SortField = 'name' | 'sent' | 'openRate' | 'bounces';
type SortOrder = 'asc' | 'desc';

export const CampaignTable: React.FC<CampaignTableProps> = ({
  data,
  loading = false,
  onExport
}) => {
  const [sortField, setSortField] = useState<SortField>('sent');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const safeData = data ?? [];
  const sortedData = [...safeData].sort((a, b) => {
    let aValue: string | number;
    let bValue: string | number;

    switch (sortField) {
      case 'name':
        aValue = a.name;
        bValue = b.name;
        break;
      case 'sent':
        aValue = a.sent;
        bValue = b.sent;
        break;
      case 'openRate':
        aValue = a.openRate;
        bValue = b.openRate;
        break;
      case 'bounces':
        aValue = a.bounces;
        bValue = b.bounces;
        break;
      default:
        aValue = a.sent;
        bValue = b.sent;
    }

    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return sortOrder === 'asc' 
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    }

    return sortOrder === 'asc' 
      ? (aValue as number) - (bValue as number)
      : (bValue as number) - (aValue as number);
  });

  const SortButton: React.FC<{ field: SortField; children: React.ReactNode }> = ({ field, children }) => (
    <Button
      variant="ghost"
      size="sm"
      className="h-auto p-0 font-medium hover:bg-transparent"
      onClick={() => handleSort(field)}
    >
      <span className="flex items-center gap-1">
        {children}
        <ArrowUpDown className="h-3 w-3" />
      </span>
    </Button>
  );

  if (loading) {
    return (
      <Card className="shadow-card rounded-2xl overflow-hidden">
        <div className="p-6 border-b">
          <div className="flex items-center justify-between">
            <div className="h-6 bg-muted animate-pulse rounded w-32" />
            <div className="h-9 bg-muted animate-pulse rounded w-24" />
          </div>
        </div>
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/30">
              <TableHead>Campagne</TableHead>
              <TableHead>Verzonden</TableHead>
              <TableHead>Open Rate</TableHead>
              <TableHead>Bounces</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 4 }).map((_, i) => (
              <TableRow key={i}>
                <TableCell><div className="h-4 bg-muted animate-pulse rounded w-48" /></TableCell>
                <TableCell><div className="h-4 bg-muted animate-pulse rounded w-16" /></TableCell>
                <TableCell><div className="h-4 bg-muted animate-pulse rounded w-12" /></TableCell>
                <TableCell><div className="h-4 bg-muted animate-pulse rounded w-8" /></TableCell>
                <TableCell><div className="h-4 bg-muted animate-pulse rounded w-6" /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    );
  }

  return (
    <Card className="shadow-card rounded-2xl overflow-hidden">
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-foreground">Per Campagne</h3>
          {onExport && (
            <Button
              variant="outline"
              size="sm"
              onClick={onExport}
              className="gap-2"
            >
              <Download className="h-4 w-4" />
              Export CSV
            </Button>
          )}
        </div>
      </div>

      <Table>
        <TableHeader>
          <TableRow className="bg-muted/30">
            <TableHead>
              <SortButton field="name">Campagne</SortButton>
            </TableHead>
            <TableHead>
              <SortButton field="sent">Verzonden</SortButton>
            </TableHead>
            <TableHead>
              <SortButton field="openRate">Open Rate</SortButton>
            </TableHead>
            <TableHead>
              <SortButton field="bounces">Bounces</SortButton>
            </TableHead>
            <TableHead className="w-12"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedData.length === 0 ? (
            <TableRow>
              <TableCell colSpan={5} className="text-center py-8">
                <div className="text-muted-foreground">
                  <p className="text-lg font-medium">Geen campagnegegevens</p>
                  <p className="text-sm">Er zijn nog geen campagnes met verzendgegevens.</p>
                </div>
              </TableCell>
            </TableRow>
          ) : (
            sortedData.map((campaign) => (
              <TableRow key={campaign.id} className="hover:bg-muted/20">
                <TableCell>
                  <div className="space-y-1">
                    <p className="font-medium text-foreground">{campaign.name}</p>
                    <p className="text-xs text-muted-foreground">ID: {campaign.id}</p>
                  </div>
                </TableCell>
                <TableCell>{campaign.sent.toLocaleString()}</TableCell>
                <TableCell>
                  <span className={`font-medium ${
                    campaign.openRate >= 0.3 ? 'text-success' : 
                    campaign.openRate >= 0.2 ? 'text-warning' : 'text-destructive'
                  }`}>
                    {(campaign.openRate * 100).toFixed(1)}%
                  </span>
                </TableCell>
                <TableCell>
                  <span className={`font-medium ${
                    campaign.bounces === 0 ? 'text-success' : 
                    campaign.bounces < 20 ? 'text-warning' : 'text-destructive'
                  }`}>
                    {campaign.bounces}
                  </span>
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0"
                    asChild
                  >
                    <Link to={`/campaigns/${campaign.id}`}>
                      <ExternalLink className="h-4 w-4" />
                    </Link>
                  </Button>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Card>
  );
};
