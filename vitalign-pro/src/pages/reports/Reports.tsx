import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, Upload, Package, Filter, Download, Link2, Unlink, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import type { ReportItem, ReportsQuery, ReportFileType } from '@/types/report';
import { reportsService } from '@/services/reports';
import { BindModal } from '@/components/reports/BindModal';
import { ViewerModal } from '@/components/reports/ViewerModal';

const FILE_TYPE_LABELS = {
  pdf: 'PDF',
  xlsx: 'Excel',
  png: 'PNG',
  jpg: 'JPG', 
  jpeg: 'JPEG',
};

const FILE_TYPE_COLORS = {
  pdf: 'bg-red-100 text-red-800',
  xlsx: 'bg-green-100 text-green-800',
  png: 'bg-blue-100 text-blue-800',
  jpg: 'bg-purple-100 text-purple-800',
  jpeg: 'bg-purple-100 text-purple-800',
};

export default function Reports() {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [selectedTypes, setSelectedTypes] = useState<ReportFileType[]>([]);
  const [bindModalOpen, setBindModalOpen] = useState(false);
  const [viewerModalOpen, setViewerModalOpen] = useState(false);
  const [selectedReport, setSelectedReport] = useState<ReportItem | null>(null);
  const { toast } = useToast();

  const [query, setQuery] = useState<ReportsQuery>({
    page: 1,
    pageSize: 20,
    search: '',
    boundFilter: 'all',
  });

  useEffect(() => {
    loadReports();
  }, [query]);

  const loadReports = async () => {
    setLoading(true);
    try {
      const result = await reportsService.getReports({
        ...query,
        types: selectedTypes.length > 0 ? selectedTypes : undefined,
      });
      setReports(result.items);
      setTotal(result.total);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load reports',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTypeToggle = (type: ReportFileType) => {
    setSelectedTypes(prev =>
      prev.includes(type)
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  const handleBind = (report: ReportItem) => {
    setSelectedReport(report);
    setBindModalOpen(true);
  };

  const handleUnbind = async (reportId: string) => {
    try {
      await reportsService.unbindReport(reportId);
      toast({
        title: 'Success',
        description: 'Report unbound successfully',
      });
      loadReports();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to unbind report',
        variant: 'destructive',
      });
    }
  };

  const handleView = (report: ReportItem) => {
    setSelectedReport(report);
    setViewerModalOpen(true);
  };

  const handleDownload = async (reportId: string, filename: string) => {
    try {
      const url = await reportsService.getDownloadUrl(reportId);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      toast({
        title: 'Success',
        description: 'Download started',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to download file',
        variant: 'destructive',
      });
    }
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${Math.round(bytes / Math.pow(1024, i))} ${sizes[i]}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('nl-NL', {
      timeZone: 'Europe/Amsterdam',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="min-h-screen bg-gradient-subtle p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Reports</h1>
            <p className="text-muted-foreground">Manage your uploaded files and documents</p>
          </div>
          <div className="flex gap-2">
            <Link to="/reports/upload">
              <Button>
                <Upload className="mr-2 h-4 w-4" />
                Upload File
              </Button>
            </Link>
            <Link to="/reports/bulk">
              <Button variant="outline">
                <Package className="mr-2 h-4 w-4" />
                Bulk Upload
              </Button>
            </Link>
          </div>
        </div>

        {/* Filters */}
        <Card className="rounded-2xl border-0 bg-card/60 backdrop-blur-sm p-6">
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by filename..."
                  value={query.search}
                  onChange={(e) => setQuery({ ...query, search: e.target.value, page: 1 })}
                  className="pl-9"
                />
              </div>
              <Select
                value={query.boundFilter}
                onValueChange={(value) => setQuery({ ...query, boundFilter: value as any, page: 1 })}
              >
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Files</SelectItem>
                  <SelectItem value="bound">Bound Files</SelectItem>
                  <SelectItem value="unbound">Unbound Files</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">File Types:</span>
              {Object.entries(FILE_TYPE_LABELS).map(([type, label]) => (
                <div key={type} className="flex items-center space-x-2">
                  <Checkbox
                    id={type}
                    checked={selectedTypes.includes(type as ReportFileType)}
                    onCheckedChange={() => handleTypeToggle(type as ReportFileType)}
                  />
                  <label htmlFor={type} className="text-sm font-medium cursor-pointer">
                    {label}
                  </label>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Results */}
        <Card className="rounded-2xl border-0 bg-card/60 backdrop-blur-sm">
          {loading ? (
            <div className="p-6 space-y-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center space-x-4">
                  <Skeleton className="h-12 w-12 rounded" />
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-48" />
                    <Skeleton className="h-3 w-32" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>File</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Bound To</TableHead>
                  <TableHead>Uploaded</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reports.map((report) => (
                  <TableRow key={report.id}>
                    <TableCell className="font-medium">{report.filename}</TableCell>
                    <TableCell>
                      <Badge 
                        variant="outline"
                        className={FILE_TYPE_COLORS[report.type]}
                      >
                        {FILE_TYPE_LABELS[report.type]}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatFileSize(report.sizeBytes)}</TableCell>
                    <TableCell>
                      {report.boundTo ? (
                        <Badge variant="secondary">
                          {report.boundTo.kind}: {report.boundTo.label}
                        </Badge>
                      ) : (
                        <span className="text-muted-foreground">Unbound</span>
                      )}
                    </TableCell>
                    <TableCell>{formatDate(report.uploadedAt)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleView(report)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDownload(report.id, report.filename)}
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                        {report.boundTo ? (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleUnbind(report.id)}
                          >
                            <Unlink className="h-4 w-4" />
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleBind(report)}
                          >
                            <Link2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}

          {reports.length === 0 && !loading && (
            <div className="p-12 text-center">
              <Package className="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 className="mt-2 text-sm font-semibold">No reports found</h3>
              <p className="text-muted-foreground">Get started by uploading your first file.</p>
            </div>
          )}
        </Card>

        {/* Pagination */}
        {total > query.pageSize && (
          <div className="flex justify-center gap-2">
            <Button
              variant="outline"
              disabled={query.page === 1}
              onClick={() => setQuery({ ...query, page: query.page - 1 })}
            >
              Previous
            </Button>
            <span className="flex items-center px-4 text-sm">
              Page {query.page} of {Math.ceil(total / query.pageSize)}
            </span>
            <Button
              variant="outline"
              disabled={query.page >= Math.ceil(total / query.pageSize)}
              onClick={() => setQuery({ ...query, page: query.page + 1 })}
            >
              Next
            </Button>
          </div>
        )}
      </div>

      {/* Modals */}
      <BindModal
        open={bindModalOpen}
        onOpenChange={setBindModalOpen}
        report={selectedReport}
        onSuccess={loadReports}
      />

      <ViewerModal
        open={viewerModalOpen}
        onOpenChange={setViewerModalOpen}
        report={selectedReport}
      />
    </div>
  );
}