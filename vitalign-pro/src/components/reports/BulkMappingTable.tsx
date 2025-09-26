import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { AlertTriangle, CheckCircle, XCircle, Search } from 'lucide-react';
import type { BulkMapRow } from '@/types/report';

interface BulkMappingTableProps {
  mappings: BulkMapRow[];
  onMappingsChange: (mappings: BulkMapRow[]) => void;
}

export function BulkMappingTable({ mappings, onMappingsChange }: BulkMappingTableProps) {
  const [searchFilter, setSearchFilter] = useState('');

  const filteredMappings = mappings.filter(mapping =>
    mapping.fileName.toLowerCase().includes(searchFilter.toLowerCase()) ||
    mapping.baseKey.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const getStatusIcon = (status: BulkMapRow['status']) => {
    switch (status) {
      case 'matched':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'unmatched':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'ambiguous':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
    }
  };

  const getStatusBadge = (status: BulkMapRow['status']) => {
    switch (status) {
      case 'matched':
        return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">Matched</Badge>;
      case 'unmatched':
        return <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">Unmatched</Badge>;
      case 'ambiguous':
        return <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">Ambiguous</Badge>;
    }
  };

  const getTargetDisplay = (mapping: BulkMapRow) => {
    if (!mapping.target) return '-';

    switch (mapping.target.kind) {
      case 'lead':
        return mapping.target.email || mapping.target.id;
      case 'campaign':
        return `Campaign: ${mapping.target.id}`;
      case 'image_key':
        return `Image Key: ${mapping.baseKey}`;
      default:
        return '-';
    }
  };

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search files..."
          value={searchFilter}
          onChange={(e) => setSearchFilter(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12">Status</TableHead>
              <TableHead>Filename</TableHead>
              <TableHead>Base Key</TableHead>
              <TableHead>Target</TableHead>
              <TableHead>Reason</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredMappings.map((mapping, index) => (
              <TableRow key={`${mapping.fileName}-${index}`}>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(mapping.status)}
                  </div>
                </TableCell>
                <TableCell className="font-medium">
                  {mapping.fileName}
                </TableCell>
                <TableCell className="font-mono text-sm">
                  {mapping.baseKey}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(mapping.status)}
                    <span className="text-sm text-muted-foreground">
                      {getTargetDisplay(mapping)}
                    </span>
                  </div>
                </TableCell>
                <TableCell>
                  {mapping.reason && (
                    <span className="text-sm text-muted-foreground">
                      {mapping.reason}
                    </span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {filteredMappings.length === 0 && (
          <div className="p-8 text-center text-muted-foreground">
            No files found matching your search
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="flex justify-between items-center text-sm text-muted-foreground">
        <span>
          Showing {filteredMappings.length} of {mappings.length} files
        </span>
        <span>
          Only matched files will be uploaded
        </span>
      </div>
    </div>
  );
}