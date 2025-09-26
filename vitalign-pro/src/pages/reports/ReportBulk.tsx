import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Package, ChevronRight, ChevronLeft, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { FileDropzone } from '@/components/reports/FileDropzone';
import { BulkMappingTable } from '@/components/reports/BulkMappingTable';
import { BulkResultReport } from '@/components/reports/BulkResultReport';
import type { BulkMode, BulkMapRow, BulkUploadResult } from '@/types/report';
import { reportsService } from '@/services/reports';

const MAX_SIZE = 100 * 1024 * 1024; // 100MB

type Step = 'upload' | 'mapping' | 'result';

export default function ReportBulk() {
  const [currentStep, setCurrentStep] = useState<Step>('upload');
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [mode, setMode] = useState<BulkMode>('by_email');
  const [mappings, setMappings] = useState<BulkMapRow[]>([]);
  const [result, setResult] = useState<BulkUploadResult | null>(null);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();

  const validateZipFile = (file: File): boolean => {
    if (!file.name.toLowerCase().endsWith('.zip')) {
      toast({
        title: 'Invalid file type',
        description: 'Please select a ZIP file',
        variant: 'destructive',
      });
      return false;
    }

    if (file.size > MAX_SIZE) {
      toast({
        title: 'File too large',
        description: `ZIP file must be less than ${MAX_SIZE / 1024 / 1024}MB`,
        variant: 'destructive',
      });
      return false;
    }

    return true;
  };

  const handleZipSelect = (file: File) => {
    if (validateZipFile(file)) {
      setZipFile(file);
    }
  };

  const handleGenerateMapping = async () => {
    if (!zipFile) return;

    setLoading(true);
    try {
      const mappingData = await reportsService.generateBulkMapping(zipFile, mode);
      setMappings(mappingData);
      setCurrentStep('mapping');
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to generate mapping preview',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleProcessUpload = async () => {
    if (!zipFile) return;

    setLoading(true);
    try {
      const uploadResult = await reportsService.bulkUpload(zipFile, mode);
      setResult(uploadResult);
      setCurrentStep('result');
      
      toast({
        title: 'Bulk upload completed',
        description: `${uploadResult.uploaded} files uploaded, ${uploadResult.failed} failed`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to process bulk upload',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const getMappingStats = () => {
    const matched = mappings.filter(m => m.status === 'matched').length;
    const unmatched = mappings.filter(m => m.status === 'unmatched').length;
    const ambiguous = mappings.filter(m => m.status === 'ambiguous').length;
    return { matched, unmatched, ambiguous, total: mappings.length };
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${Math.round(bytes / Math.pow(1024, i))} ${sizes[i]}`;
  };

  const renderStep = () => {
    switch (currentStep) {
      case 'upload':
        return (
          <Card className="rounded-2xl border-0 bg-card/60 backdrop-blur-sm p-6 space-y-6">
            <div>
              <h2 className="text-xl font-semibold mb-2">Step 1: Upload ZIP File</h2>
              <p className="text-muted-foreground">
                Select a ZIP file containing your reports and choose the mapping mode.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Mapping Mode</label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card 
                    className={`p-4 cursor-pointer border-2 transition-colors ${
                      mode === 'by_email' ? 'border-primary bg-primary/5' : 'border-muted'
                    }`}
                    onClick={() => setMode('by_email')}
                  >
                    <h3 className="font-semibold">By Email</h3>
                    <p className="text-sm text-muted-foreground">
                      Match files to leads by extracting email addresses from filenames
                    </p>
                  </Card>
                  <Card 
                    className={`p-4 cursor-pointer border-2 transition-colors ${
                      mode === 'by_image_key' ? 'border-primary bg-primary/5' : 'border-muted'
                    }`}
                    onClick={() => setMode('by_image_key')}
                  >
                    <h3 className="font-semibold">By Image Key</h3>
                    <p className="text-sm text-muted-foreground">
                      Match files using image key patterns in filenames
                    </p>
                  </Card>
                </div>
              </div>

              <FileDropzone
                onFileSelect={handleZipSelect}
                accept=".zip"
                maxSize={MAX_SIZE}
              />

              {zipFile && (
                <div className="p-4 bg-muted rounded-lg">
                  <div className="flex items-center gap-3">
                    <Package className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{zipFile.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatFileSize(zipFile.size)} • Mode: {mode.replace('_', ' ')}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end">
              <Button 
                onClick={handleGenerateMapping}
                disabled={!zipFile || loading}
              >
                {loading ? (
                  <>
                    <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent" />
                    Processing...
                  </>
                ) : (
                  <>
                    Next: Preview Mapping
                    <ChevronRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </Card>
        );

      case 'mapping':
        const stats = getMappingStats();
        return (
          <div className="space-y-6">
            <Card className="rounded-2xl border-0 bg-card/60 backdrop-blur-sm p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-xl font-semibold mb-2">Step 2: Review Mapping</h2>
                  <p className="text-muted-foreground">
                    Review and adjust the file mapping before upload.
                  </p>
                </div>
                <div className="grid grid-cols-4 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-foreground">{stats.total}</div>
                    <div className="text-sm text-muted-foreground">Total</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600">{stats.matched}</div>
                    <div className="text-sm text-muted-foreground">Matched</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-yellow-600">{stats.ambiguous}</div>
                    <div className="text-sm text-muted-foreground">Ambiguous</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-red-600">{stats.unmatched}</div>
                    <div className="text-sm text-muted-foreground">Unmatched</div>
                  </div>
                </div>
              </div>

              <BulkMappingTable 
                mappings={mappings}
                onMappingsChange={setMappings}
              />

              <div className="flex justify-between pt-6">
                <Button 
                  variant="outline"
                  onClick={() => setCurrentStep('upload')}
                >
                  <ChevronLeft className="mr-2 h-4 w-4" />
                  Back
                </Button>
                <Button 
                  onClick={handleProcessUpload}
                  disabled={stats.matched === 0 || loading}
                >
                  {loading ? (
                    <>
                      <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent" />
                      Uploading...
                    </>
                  ) : (
                    `Upload ${stats.matched} Files`
                  )}
                </Button>
              </div>
            </Card>
          </div>
        );

      case 'result':
        return (
          <div className="space-y-6">
            <Card className="rounded-2xl border-0 bg-card/60 backdrop-blur-sm p-6">
              <div className="text-center mb-6">
                <h2 className="text-xl font-semibold mb-2">Step 3: Upload Complete</h2>
                <p className="text-muted-foreground">
                  Your bulk upload has been processed.
                </p>
              </div>

              {result && <BulkResultReport result={result} />}

              <div className="flex justify-center gap-2 pt-6">
                <Button 
                  variant="outline"
                  onClick={() => navigate('/reports')}
                >
                  View All Reports
                </Button>
                <Button onClick={() => {
                  setCurrentStep('upload');
                  setZipFile(null);
                  setMappings([]);
                  setResult(null);
                }}>
                  Upload Another ZIP
                </Button>
              </div>
            </Card>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-subtle p-6">
      <div className="mx-auto max-w-4xl space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link to="/reports">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-foreground">Bulk Upload</h1>
            <p className="text-muted-foreground">Upload multiple files via ZIP with automatic mapping</p>
          </div>
        </div>

        {/* Progress */}
        <Card className="rounded-2xl border-0 bg-card/60 backdrop-blur-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex gap-4">
              <Badge variant={currentStep === 'upload' ? 'default' : 'secondary'}>
                1. Upload
              </Badge>
              <Badge variant={currentStep === 'mapping' ? 'default' : 'secondary'}>
                2. Mapping
              </Badge>
              <Badge variant={currentStep === 'result' ? 'default' : 'secondary'}>
                3. Results
              </Badge>
            </div>
          </div>
          <Progress 
            value={currentStep === 'upload' ? 33 : currentStep === 'mapping' ? 66 : 100} 
            className="h-2"
          />
        </Card>

        {renderStep()}
      </div>
    </div>
  );
}