import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Upload, File, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { FileDropzone } from '@/components/reports/FileDropzone';
import { BindingSelector } from '@/components/reports/BindingSelector';
import type { ReportFileType } from '@/types/report';
import { reportsService } from '@/services/reports';

const ALLOWED_TYPES: ReportFileType[] = ['pdf', 'xlsx', 'png', 'jpg', 'jpeg'];
const MAX_SIZE = 10 * 1024 * 1024; // 10MB

export default function ReportUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [bindingType, setBindingType] = useState<'none' | 'lead' | 'campaign'>('none');
  const [bindingId, setBindingId] = useState<string>('');
  const [uploading, setUploading] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();

  const validateFile = (file: File): boolean => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    
    if (!extension || !ALLOWED_TYPES.includes(extension as ReportFileType)) {
      toast({
        title: 'Invalid file type',
        description: `Please select a file with one of these extensions: ${ALLOWED_TYPES.join(', ')}`,
        variant: 'destructive',
      });
      return false;
    }

    if (file.size > MAX_SIZE) {
      toast({
        title: 'File too large',
        description: `File size must be less than ${MAX_SIZE / 1024 / 1024}MB`,
        variant: 'destructive',
      });
      return false;
    }

    return true;
  };

  const handleFileSelect = (selectedFile: File) => {
    if (validateFile(selectedFile)) {
      setFile(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    try {
      const payload = {
        file,
        ...(bindingType === 'lead' && bindingId && { leadId: bindingId }),
        ...(bindingType === 'campaign' && bindingId && { campaignId: bindingId }),
      };

      await reportsService.uploadReport(payload);
      
      toast({
        title: 'Success',
        description: 'File uploaded successfully',
      });
      
      navigate('/reports');
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to upload file',
        variant: 'destructive',
      });
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${Math.round(bytes / Math.pow(1024, i))} ${sizes[i]}`;
  };

  const canUpload = file && (bindingType === 'none' || bindingId);

  return (
    <div className="min-h-screen bg-gradient-subtle p-6">
      <div className="mx-auto max-w-2xl space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link to="/reports">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-foreground">Upload File</h1>
            <p className="text-muted-foreground">Upload a single file with optional binding</p>
          </div>
        </div>

        {/* Upload Form */}
        <Card className="rounded-2xl border-0 bg-card/60 backdrop-blur-sm p-6 space-y-6">
          {/* File Selection */}
          <div className="space-y-2">
            <Label>Select File</Label>
            <FileDropzone
              onFileSelect={handleFileSelect}
              accept={ALLOWED_TYPES.map(t => `.${t}`).join(',')}
              maxSize={MAX_SIZE}
            />
            
            {file && (
              <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                <div className="flex items-center gap-3">
                  <File className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium">{file.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setFile(null)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>

          {/* Binding Options */}
          <div className="space-y-4">
            <Label>Bind To (Optional)</Label>
            
            <Select value={bindingType} onValueChange={(value: any) => {
              setBindingType(value);
              setBindingId('');
            }}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No Binding</SelectItem>
                <SelectItem value="lead">Lead</SelectItem>
                <SelectItem value="campaign">Campaign</SelectItem>
              </SelectContent>
            </Select>

            {bindingType !== 'none' && (
              <BindingSelector
                type={bindingType as 'lead' | 'campaign'}
                value={bindingId}
                onChange={setBindingId}
              />
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4">
            <Link to="/reports">
              <Button variant="outline">Cancel</Button>
            </Link>
            <Button
              onClick={handleUpload}
              disabled={!canUpload || uploading}
            >
              {uploading ? (
                <>
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload File
                </>
              )}
            </Button>
          </div>
        </Card>

        {/* Info */}
        <Card className="rounded-2xl border-0 bg-card/60 backdrop-blur-sm p-4">
          <h3 className="font-semibold mb-2">Upload Requirements</h3>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• Supported formats: PDF, Excel, PNG, JPG, JPEG</li>
            <li>• Maximum file size: 10MB</li>
            <li>• Files can be bound to leads or campaigns for organization</li>
            <li>• Binding is optional and can be changed later</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}