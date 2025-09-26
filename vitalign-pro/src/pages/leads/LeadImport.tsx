import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { 
  Upload, 
  ArrowLeft, 
  FileX, 
  CheckCircle, 
  AlertCircle, 
  Download,
  Loader2,
  FileSpreadsheet
} from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { ImportMapping, ImportPreview, ImportJobStatus } from '@/types/lead';
import { leadsService } from '@/services/leads';
import { useImportJobPolling } from '@/hooks/useImportJobPolling';
import { useToast } from '@/hooks/use-toast';

const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB
const ACCEPTED_TYPES = {
  'text/csv': ['.csv'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/vnd.ms-excel': ['.xls']
};

const LEAD_FIELDS = [
  { value: 'email', label: 'Email *', required: true },
  { value: 'companyName', label: 'Company Name' },
  { value: 'domain', label: 'Domain' },
  { value: 'url', label: 'Website URL' },
  { value: 'tags', label: 'Tags (comma-separated)' },
  { value: 'status', label: 'Status' },
  { value: 'imageKey', label: 'Image Key' },
  { value: '', label: 'Skip Column' }
];

type ImportStep = 'upload' | 'mapping' | 'confirm' | 'progress';

export default function LeadImport() {
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [step, setStep] = useState<ImportStep>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [mapping, setMapping] = useState<ImportMapping>({});
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  
  const { job, stopPolling } = useImportJobPolling(jobId);

  const onDrop = useCallback(async (acceptedFiles: File[], rejectedFiles: any[]) => {
    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      if (rejection.file.size > MAX_FILE_SIZE) {
        toast({
          title: 'File too large',
          description: 'File size must be less than 20MB',
          variant: 'destructive'
        });
      } else {
        toast({
          title: 'Invalid file type',
          description: 'Please upload a CSV or Excel file',
          variant: 'destructive'
        });
      }
      return;
    }

    const selectedFile = acceptedFiles[0];
    setFile(selectedFile);
    
    setLoading(true);
    try {
      const previewData = await leadsService.previewImport(selectedFile);
      setPreview(previewData);
      
      // Auto-map common columns
      const autoMapping: ImportMapping = {};
      previewData.headers.forEach(header => {
        const lowerHeader = header.toLowerCase();
        if (lowerHeader.includes('email')) autoMapping[header] = 'email';
        else if (lowerHeader.includes('company') || lowerHeader.includes('bedrijf')) autoMapping[header] = 'companyName';
        else if (lowerHeader.includes('domain')) autoMapping[header] = 'domain';
        else if (lowerHeader.includes('url') || lowerHeader.includes('website')) autoMapping[header] = 'url';
        else if (lowerHeader.includes('tag')) autoMapping[header] = 'tags';
        else if (lowerHeader.includes('status')) autoMapping[header] = 'status';
      });
      setMapping(autoMapping);
      
      setStep('mapping');
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to process file. Please check the format.',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    maxSize: MAX_FILE_SIZE
  });

  const handleMappingComplete = () => {
    const hasEmailMapping = Object.values(mapping).includes('email');
    if (!hasEmailMapping) {
      toast({
        title: 'Email required',
        description: 'Please map at least one column to Email field',
        variant: 'destructive'
      });
      return;
    }
    
    setStep('confirm');
  };

  const handleStartImport = async () => {
    if (!file) return;
    
    setLoading(true);
    try {
      const job = await leadsService.importLeads(file, mapping);
      setJobId(job.id);
      setStep('progress');
      
      toast({
        title: 'Import started',
        description: 'Your leads are being processed...'
      });
    } catch (error) {
      toast({
        title: 'Import failed',
        description: 'Failed to start import process',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const getMappedPreviewData = () => {
    if (!preview) return [];
    
    return preview.rows.slice(0, 20).map((row, index) => ({
      index,
      data: preview.headers.reduce((acc, header, i) => {
        const mappedField = mapping[header];
        if (mappedField && mappedField !== '') {
          acc[mappedField] = row[i];
        }
        return acc;
      }, {} as Record<string, string>),
      isDuplicate: preview.duplicates.includes(index)
    }));
  };

  const renderUploadStep = () => (
    <Card className="p-8 shadow-card rounded-2xl">
      <div className="text-center space-y-6">
        <div className="mx-auto w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center">
          <FileSpreadsheet className="w-8 h-8 text-primary" />
        </div>
        
        <div>
          <h2 className="text-2xl font-bold mb-2">Upload Lead File</h2>
          <p className="text-muted-foreground">
            Upload a CSV or Excel file to import your leads
          </p>
        </div>

        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-2xl p-12 cursor-pointer transition-all ${
            isDragActive 
              ? 'border-primary bg-primary/5' 
              : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/20'
          }`}
        >
          <input {...getInputProps()} />
          <div className="text-center space-y-4">
            <Upload className="w-12 h-12 mx-auto text-muted-foreground" />
            <div>
              <p className="text-lg font-medium">
                {isDragActive ? 'Drop your file here' : 'Drag & drop your file here'}
              </p>
              <p className="text-muted-foreground">
                or <span className="text-primary font-medium">browse</span> to choose a file
              </p>
            </div>
            <div className="text-sm text-muted-foreground">
              Supported formats: CSV, XLSX, XLS (max 20MB)
            </div>
          </div>
        </div>

        {loading && (
          <div className="flex items-center justify-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Processing file...</span>
          </div>
        )}

        <div className="text-xs text-muted-foreground bg-muted/30 rounded-lg p-4">
          <p className="font-medium mb-2">File Requirements:</p>
          <ul className="space-y-1">
            <li>• First row should contain column headers</li>
            <li>• Email column is required</li>
            <li>• Maximum 20MB file size</li>
            <li>• CSV, XLSX, or XLS format</li>
          </ul>
        </div>
      </div>
    </Card>
  );

  const renderMappingStep = () => (
    <div className="space-y-6">
      <Card className="p-6 shadow-card rounded-2xl">
        <h2 className="text-2xl font-bold mb-4">Map Columns</h2>
        <p className="text-muted-foreground mb-6">
          Map your file columns to lead fields. Email is required.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {preview?.headers.map((header, index) => (
            <div key={header} className="flex items-center gap-3">
              <div className="min-w-0 flex-1">
                <p className="font-medium truncate">{header}</p>
                <p className="text-sm text-muted-foreground truncate">
                  Sample: {preview.rows[0]?.[index] || 'N/A'}
                </p>
              </div>
              <Select
                value={mapping[header] || ''}
                onValueChange={(value) => {
                  setMapping(prev => ({ ...prev, [header]: value }));
                }}
              >
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Select field..." />
                </SelectTrigger>
                <SelectContent className="bg-popover border border-border">
                  {LEAD_FIELDS.map(field => (
                    <SelectItem key={field.value} value={field.value}>
                      {field.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ))}
        </div>

        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={() => setStep('upload')}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <Button
            onClick={handleMappingComplete}
            className="bg-gradient-primary hover:shadow-glow"
          >
            Continue to Preview
          </Button>
        </div>
      </Card>

      <Card className="p-6 shadow-card rounded-2xl">
        <h3 className="font-semibold mb-4">Preview (First 20 rows)</h3>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Row</TableHead>
                {Object.entries(mapping)
                  .filter(([_, field]) => field && field !== '')
                  .map(([header, field]) => (
                    <TableHead key={header}>{LEAD_FIELDS.find(f => f.value === field)?.label || field}</TableHead>
                  ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {getMappedPreviewData().map((row) => (
                <TableRow key={row.index} className={row.isDuplicate ? 'bg-warning/10' : ''}>
                  <TableCell className="font-mono text-sm">
                    {row.index + 1}
                    {row.isDuplicate && (
                      <Badge variant="destructive" className="ml-2 text-xs">
                        Duplicate
                      </Badge>
                    )}
                  </TableCell>
                  {Object.entries(mapping)
                    .filter(([_, field]) => field && field !== '')
                    .map(([header, field]) => (
                      <TableCell key={header} className="max-w-32 truncate">
                        {row.data[field!] || '-'}
                      </TableCell>
                    ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        {preview && preview.duplicates.length > 0 && (
          <div className="mt-4 p-4 bg-warning/10 border border-warning/20 rounded-lg">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-warning" />
              <span className="font-medium">Duplicates detected</span>
            </div>
            <p className="text-sm text-muted-foreground mt-1">
              {preview.duplicates.length} potential duplicate(s) found. These will be skipped during import.
            </p>
          </div>
        )}
      </Card>
    </div>
  );

  const renderConfirmStep = () => (
    <Card className="p-8 shadow-card rounded-2xl">
      <div className="text-center space-y-6">
        <div className="mx-auto w-16 h-16 bg-accent/10 rounded-2xl flex items-center justify-center">
          <CheckCircle className="w-8 h-8 text-accent" />
        </div>
        
        <div>
          <h2 className="text-2xl font-bold mb-2">Ready to Import</h2>
          <p className="text-muted-foreground">
            Review your import settings and start the process
          </p>
        </div>

        <div className="bg-muted/30 rounded-2xl p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="font-medium text-muted-foreground">File</p>
              <p className="font-mono">{file?.name}</p>
            </div>
            <div>
              <p className="font-medium text-muted-foreground">Size</p>
              <p>{file && (file.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
            <div>
              <p className="font-medium text-muted-foreground">Total Rows</p>
              <p>{preview?.rows.length || 0}</p>
            </div>
            <div>
              <p className="font-medium text-muted-foreground">Duplicates</p>
              <p>{preview?.duplicates.length || 0}</p>
            </div>
          </div>

          <div>
            <p className="font-medium text-muted-foreground mb-2">Column Mapping</p>
            <div className="space-y-1 text-sm">
              {Object.entries(mapping)
                .filter(([_, field]) => field && field !== '')
                .map(([header, field]) => (
                  <div key={header} className="flex justify-between">
                    <span className="font-mono">{header}</span>
                    <span>→ {LEAD_FIELDS.find(f => f.value === field)?.label}</span>
                  </div>
                ))}
            </div>
          </div>
        </div>

        <div className="flex gap-4">
          <Button
            variant="outline"
            onClick={() => setStep('mapping')}
            className="flex-1"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Mapping
          </Button>
          <Button
            onClick={handleStartImport}
            disabled={loading}
            className="flex-1 bg-gradient-accent hover:shadow-glow"
          >
            {loading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            Start Import
          </Button>
        </div>
      </div>
    </Card>
  );

  const renderProgressStep = () => (
    <Card className="p-8 shadow-card rounded-2xl">
      <div className="text-center space-y-6">
        <div className="mx-auto w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center">
          {job?.status === 'completed' ? (
            <CheckCircle className="w-8 h-8 text-accent" />
          ) : job?.status === 'failed' ? (
            <AlertCircle className="w-8 h-8 text-destructive" />
          ) : (
            <Loader2 className="w-8 h-8 text-primary animate-spin" />
          )}
        </div>
        
        <div>
          <h2 className="text-2xl font-bold mb-2">
            {job?.status === 'completed' ? 'Import Complete!' :
             job?.status === 'failed' ? 'Import Failed' :
             'Import in Progress'}
          </h2>
          <p className="text-muted-foreground">
            {job?.status === 'completed' ? 'Your leads have been successfully imported' :
             job?.status === 'failed' ? 'There was an error during the import process' :
             'Please wait while we process your leads...'}
          </p>
        </div>

        {job && (
          <>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{job.progress}%</span>
              </div>
              <Progress value={job.progress} className="h-3" />
            </div>

            <div className="bg-muted/30 rounded-2xl p-6">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-accent">{job.inserted}</div>
                  <div className="text-sm text-muted-foreground">Inserted</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-warning">{job.updated}</div>
                  <div className="text-sm text-muted-foreground">Updated</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-muted-foreground">{job.skipped}</div>
                  <div className="text-sm text-muted-foreground">Skipped</div>
                </div>
              </div>
            </div>

            {job.errors.length > 0 && (
              <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-destructive" />
                    <span className="font-medium">Errors Found</span>
                  </div>
                  <Button size="sm" variant="outline">
                    <Download className="w-4 h-4 mr-2" />
                    Download Error Report
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground">
                  {job.errors.length} error(s) occurred during import. Download the report for details.
                </p>
              </div>
            )}
          </>
        )}

        <div className="flex gap-4">
          {job?.status === 'completed' && (
            <Button
              onClick={() => navigate('/leads')}
              className="flex-1 bg-gradient-primary hover:shadow-glow"
            >
              View Leads
            </Button>
          )}
          <Button
            variant="outline"
            onClick={() => {
              stopPolling();
              setStep('upload');
              setFile(null);
              setPreview(null);
              setMapping({});
              setJobId(null);
            }}
            className="flex-1"
          >
            Import Another File
          </Button>
        </div>
      </div>
    </Card>
  );

  return (
    <div className="min-h-screen bg-gradient-subtle p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/leads')}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Leads
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-foreground">Import Leads</h1>
              <p className="text-muted-foreground">Upload and process your lead data</p>
            </div>
          </div>
        </div>

        {/* Progress Steps */}
        <Card className="p-4 shadow-card rounded-2xl">
          <div className="flex items-center justify-between">
            {[
              { key: 'upload', label: 'Upload File', icon: Upload },
              { key: 'mapping', label: 'Map Columns', icon: FileSpreadsheet },
              { key: 'confirm', label: 'Confirm', icon: CheckCircle },
              { key: 'progress', label: 'Import', icon: Loader2 }
            ].map((stepItem, index) => {
              const StepIcon = stepItem.icon;
              const isActive = step === stepItem.key;
              const isCompleted = ['upload', 'mapping', 'confirm', 'progress'].indexOf(stepItem.key) < 
                                  ['upload', 'mapping', 'confirm', 'progress'].indexOf(step);
              
              return (
                <div key={stepItem.key} className="flex items-center">
                  <div className={`flex items-center gap-2 ${isActive ? 'text-primary' : isCompleted ? 'text-accent' : 'text-muted-foreground'}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 ${
                      isActive ? 'border-primary bg-primary/10' : 
                      isCompleted ? 'border-accent bg-accent/10' : 
                      'border-muted'
                    }`}>
                      <StepIcon className="w-4 h-4" />
                    </div>
                    <span className="font-medium hidden sm:block">{stepItem.label}</span>
                  </div>
                  {index < 3 && (
                    <div className={`w-8 h-0.5 mx-2 ${isCompleted ? 'bg-accent' : 'bg-muted'}`} />
                  )}
                </div>
              );
            })}
          </div>
        </Card>

        {/* Step Content */}
        {step === 'upload' && renderUploadStep()}
        {step === 'mapping' && renderMappingStep()}
        {step === 'confirm' && renderConfirmStep()}
        {step === 'progress' && renderProgressStep()}
      </div>
    </div>
  );
}