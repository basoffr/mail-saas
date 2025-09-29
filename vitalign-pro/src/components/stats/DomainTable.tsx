import React, { useState } from 'react';
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
import { ArrowUpDown, Download } from 'lucide-react';
import { DomainStats } from '@/types/stats';

interface DomainTableProps {
  data: DomainStats[];
  loading?: boolean;
  onExport?: () => void;
}

type SortField = 'domain' | 'sent' | 'openRate' | 'bounces';
type SortOrder = 'asc' | 'desc';

export const DomainTable: React.FC<DomainTableProps> = ({
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

  const sortedData = [...data].sort((a, b) => {
    let aValue: string | number;
    let bValue: string | number;

    switch (sortField) {
      case 'domain':
        aValue = a.domain;
        bValue = b.domain;
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
              <TableHead>Domein</TableHead>
              <TableHead>Verzonden</TableHead>
              <TableHead>Open Rate</TableHead>
              <TableHead>Bounces</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 4 }).map((_, i) => (
              <TableRow key={i}>
                <TableCell><div className="h-4 bg-muted animate-pulse rounded w-32" /></TableCell>
                <TableCell><div className="h-4 bg-muted animate-pulse rounded w-16" /></TableCell>
                <TableCell><div className="h-4 bg-muted animate-pulse rounded w-12" /></TableCell>
                <TableCell><div className="h-4 bg-muted animate-pulse rounded w-8" /></TableCell>
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
          <h3 className="text-lg font-semibold text-foreground">Per Domein</h3>
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
              <SortButton field="domain">Domein</SortButton>
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
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedData.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-8">
                <div className="text-muted-foreground">
                  <p className="text-lg font-medium">Geen domeingegevens</p>
                  <p className="text-sm">Er zijn nog geen verzendgegevens beschikbaar.</p>
                </div>
              </TableCell>
            </TableRow>
          ) : (
            sortedData.map((domain) => (
              <TableRow key={domain.domain} className="hover:bg-muted/20">
                <TableCell className="font-medium">{domain.domain}</TableCell>
                <TableCell>{domain.sent.toLocaleString()}</TableCell>
                <TableCell>
                  <span className={`font-medium ${
                    domain.openRate >= 0.3 ? 'text-success' : 
                    domain.openRate >= 0.2 ? 'text-warning' : 'text-destructive'
                  }`}>
                    {(domain.openRate * 100).toFixed(1)}%
                  </span>
                </TableCell>
                <TableCell>
                  <span className={`font-medium ${
                    domain.bounces === 0 ? 'text-success' : 
                    domain.bounces < 20 ? 'text-warning' : 'text-destructive'
                  }`}>
                    {domain.bounces}
                  </span>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Card>
  );
};
