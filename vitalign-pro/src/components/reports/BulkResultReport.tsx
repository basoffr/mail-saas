import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { CheckCircle, XCircle, Download } from 'lucide-react';
import type { BulkUploadResult } from '@/types/report';

interface BulkResultReportProps {
  result: BulkUploadResult;
}

export function BulkResultReport({ result }: BulkResultReportProps) {
  const successRate = Math.round((result.uploaded / result.total) * 100);

  const downloadResultsCsv = () => {
    const csvContent = [
      'Filename,Status,Target,Error',
      ...result.mappings.map(mapping => 
        `"${mapping.fileName}","${mapping.status}","${mapping.to?.kind || ''}:${mapping.to?.id || ''}","${mapping.error || ''}"`
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bulk_upload_results_${new Date().getTime()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 text-center">
          <div className="text-2xl font-bold text-foreground">{result.total}</div>
          <div className="text-sm text-muted-foreground">Total Files</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-2xl font-bold text-green-600">{result.uploaded}</div>
          <div className="text-sm text-muted-foreground">Uploaded</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-2xl font-bold text-red-600">{result.failed}</div>
          <div className="text-sm text-muted-foreground">Failed</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-2xl font-bold text-primary">{successRate}%</div>
          <div className="text-sm text-muted-foreground">Success Rate</div>
        </Card>
      </div>

      {/* Results Table */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold">Upload Results</h3>
          <Button variant="outline" size="sm" onClick={downloadResultsCsv}>
            <Download className="h-4 w-4 mr-2" />
            Download CSV
          </Button>
        </div>
        
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">Status</TableHead>
                <TableHead>Filename</TableHead>
                <TableHead>Target</TableHead>
                <TableHead>Error</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {result.mappings.map((mapping, index) => (
                <TableRow key={`${mapping.fileName}-${index}`}>
                  <TableCell>
                    {mapping.status === 'ok' ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-600" />
                    )}
                  </TableCell>
                  <TableCell className="font-medium">
                    {mapping.fileName}
                  </TableCell>
                  <TableCell>
                    {mapping.to ? (
                      <Badge variant="outline">
                        {mapping.to.kind}: {mapping.to.id}
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {mapping.error && (
                      <span className="text-sm text-red-600">
                        {mapping.error}
                      </span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Summary Message */}
      <div className={`p-4 rounded-lg ${
        successRate === 100 
          ? 'bg-green-50 border border-green-200' 
          : successRate > 50 
          ? 'bg-yellow-50 border border-yellow-200'
          : 'bg-red-50 border border-red-200'
      }`}>
        <p className={`font-medium ${
          successRate === 100 
            ? 'text-green-800' 
            : successRate > 50 
            ? 'text-yellow-800'
            : 'text-red-800'
        }`}>
          {successRate === 100 
            ? '✅ All files uploaded successfully!'
            : successRate > 50
            ? `⚠️ ${result.uploaded} of ${result.total} files uploaded successfully.`
            : `❌ Upload completed with errors. Only ${result.uploaded} of ${result.total} files uploaded.`
          }
        </p>
        {result.failed > 0 && (
          <p className="text-sm text-muted-foreground mt-1">
            Review the errors above and download the CSV for detailed results.
          </p>
        )}
      </div>
    </div>
  );
}