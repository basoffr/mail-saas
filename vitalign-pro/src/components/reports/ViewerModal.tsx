import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Download, ExternalLink } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import type { ReportItem } from '@/types/report';
import { reportsService } from '@/services/reports';

interface ViewerModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  report: ReportItem | null;
}

export function ViewerModal({ open, onOpenChange, report }: ViewerModalProps) {
  const { toast } = useToast();

  const handleDownload = async () => {
    if (!report) return;

    try {
      const url = await reportsService.getDownloadUrl(report.id);
      const a = document.createElement('a');
      a.href = url;
      a.download = report.filename;
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

  const renderPreview = () => {
    if (!report) return null;

    const isImage = ['png', 'jpg', 'jpeg'].includes(report.type);
    const isPdf = report.type === 'pdf';

    if (isImage) {
      // Mock image URL for preview
      const mockImageUrl = `https://via.placeholder.com/400x300/6366f1/ffffff?text=${report.filename}`;
      return (
        <div className="mt-4 text-center">
          <img 
            src={mockImageUrl} 
            alt={report.filename}
            className="max-w-full max-h-96 mx-auto rounded-lg border"
          />
        </div>
      );
    }

    if (isPdf) {
      return (
        <div className="mt-4 p-8 bg-muted rounded-lg text-center">
          <p className="text-muted-foreground mb-4">PDF Preview</p>
          <div className="bg-white border rounded p-4 max-w-sm mx-auto">
            <div className="h-40 bg-gray-100 rounded mb-2 flex items-center justify-center">
              <span className="text-gray-500 text-sm">PDF Document</span>
            </div>
            <p className="text-xs text-gray-600 truncate">{report.filename}</p>
          </div>
        </div>
      );
    }

    return (
      <div className="mt-4 p-8 bg-muted rounded-lg text-center">
        <p className="text-muted-foreground">
          Preview not available for {report.type.toUpperCase()} files
        </p>
        <p className="text-sm text-muted-foreground mt-2">
          Use the download button to view the file
        </p>
      </div>
    );
  };

  if (!report) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>File Viewer</span>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={handleDownload}>
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
            </div>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* File Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-muted/50 rounded-lg">
            <div>
              <p className="text-sm text-muted-foreground">Filename</p>
              <p className="font-medium">{report.filename}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Type</p>
              <Badge variant="outline">{report.type.toUpperCase()}</Badge>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Size</p>
              <p className="font-medium">{formatFileSize(report.sizeBytes)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Uploaded</p>
              <p className="font-medium">{formatDate(report.uploadedAt)}</p>
            </div>
            {report.boundTo && (
              <div className="md:col-span-2">
                <p className="text-sm text-muted-foreground">Bound To</p>
                <Badge variant="secondary">
                  {report.boundTo.kind}: {report.boundTo.label}
                </Badge>
              </div>
            )}
          </div>

          {/* Preview */}
          {renderPreview()}
        </div>
      </DialogContent>
    </Dialog>
  );
}