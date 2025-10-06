import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  Upload, 
  FileSpreadsheet, 
  Image as ImageIcon, 
  FileText,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Trash2
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { authService } from '@/services/auth';

interface BulkImportResult {
  leads_imported: number;
  screenshots_uploaded: number;
  reports_uploaded: number;
  leads_complete: number;
  warnings: string[];
}

export default function BulkImport() {
  const { toast } = useToast();
  
  const [listName, setListName] = useState('');
  const [excelFile, setExcelFile] = useState<File | null>(null);
  const [screenshotsZip, setScreenshotsZip] = useState<File | null>(null);
  const [reportsZip, setReportsZip] = useState<File | null>(null);
  
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<BulkImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (
    file: File | null, 
    setter: React.Dispatch<React.SetStateAction<File | null>>
  ) => {
    setter(file);
    setError(null);
    setResult(null);
  };

  const handleClearData = async () => {
    if (!confirm('⚠️ WAARSCHUWING: Dit verwijdert ALLE data uit de database EN storage!\n\nInclusive:\n- Leads\n- Reports\n- Screenshots\n- Alle bestanden\n\nWeet je het zeker?')) {
      return;
    }

    try {
      setUploading(true);
      
      const response = await authService.apiCall<any>('/clear-all-data', {
        method: 'POST'
      });

      const counts = response;
      const message = `Verwijderd:\n` +
        `• ${counts.deleted_leads || 0} leads\n` +
        `• ${counts.deleted_files || 0} bestanden\n` +
        `• ${counts.deleted_reports || 0} reports\n` +
        `• ${counts.deleted_assets || 0} assets`;

      toast({
        title: 'Data verwijderd',
        description: message,
      });

    } catch (err: any) {
      toast({
        title: 'Fout',
        description: err.message || 'Failed to clear data',
        variant: 'destructive'
      });
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!listName.trim()) {
      setError('Lijst naam is verplicht');
      return;
    }
    
    if (!excelFile) {
      setError('Excel bestand is verplicht');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      setResult(null);

      // Create FormData
      const formData = new FormData();
      formData.append('excel_file', excelFile);
      formData.append('list_name', listName);
      
      if (screenshotsZip) {
        formData.append('screenshots_zip', screenshotsZip);
      }
      
      if (reportsZip) {
        formData.append('reports_zip', reportsZip);
      }

      // Upload via API
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/bulk-import`,
        {
          method: 'POST',
          headers: authService.getAuthHeadersForFormData(),
          body: formData
        }
      );

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      setResult(data.data);

      toast({
        title: 'Import succesvol!',
        description: `${data.data.leads_imported} leads geïmporteerd`,
      });

    } catch (err: any) {
      setError(err.message || 'Import failed');
      toast({
        title: 'Import mislukt',
        description: err.message,
        variant: 'destructive'
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Bulk Import</h1>
        <p className="text-muted-foreground mt-2">
          Upload leads, screenshots en reports in één keer. Alles wordt automatisch aan elkaar gelinkt.
        </p>
      </div>

      {/* Clear Data Button */}
      <Card className="p-4 mb-6 border-destructive/50 bg-destructive/5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-destructive">Danger Zone</h3>
            <p className="text-sm text-muted-foreground">
              Verwijder alle data uit de database voor een clean slate
            </p>
          </div>
          <Button
            variant="destructive"
            onClick={handleClearData}
            disabled={uploading}
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Clear All Data
          </Button>
        </div>
      </Card>

      <form onSubmit={handleSubmit}>
        {/* List Name */}
        <Card className="p-6 mb-6">
          <div className="space-y-2">
            <Label htmlFor="listName">Lijst Naam *</Label>
            <Input
              id="listName"
              value={listName}
              onChange={(e) => setListName(e.target.value)}
              placeholder="bijv. Q4 2024 Batch"
              disabled={uploading}
            />
            <p className="text-sm text-muted-foreground">
              Alle leads worden toegevoegd aan deze lijst
            </p>
          </div>
        </Card>

        {/* Excel Upload */}
        <Card className="p-6 mb-6">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-primary" />
              <Label>Excel Bestand *</Label>
            </div>
            
            <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={(e) => handleFileChange(e.target.files?.[0] || null, setExcelFile)}
                className="hidden"
                id="excel-upload"
                disabled={uploading}
              />
              <label htmlFor="excel-upload" className="cursor-pointer">
                {excelFile ? (
                  <div className="flex items-center justify-center gap-2 text-green-600">
                    <CheckCircle2 className="w-5 h-5" />
                    <span className="font-medium">{excelFile.name}</span>
                  </div>
                ) : (
                  <>
                    <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      Klik om Excel te uploaden (.xlsx, .xls)
                    </p>
                  </>
                )}
              </label>
            </div>

            <div className="text-xs text-muted-foreground space-y-1">
              <p className="font-semibold">Verwachte kolommen:</p>
              <ul className="list-disc list-inside pl-2 space-y-1">
                <li><strong>email</strong> (verplicht)</li>
                <li><strong>domain</strong> (verplicht) - bijv. labelnoir.nl</li>
                <li>company / Bedrijfsnaam</li>
                <li>url</li>
                <li>keyword / Keyword</li>
                <li>google_rank / Google Rank</li>
                <li>city / plaats</li>
                <li>phone / telefoon</li>
              </ul>
            </div>
          </div>
        </Card>

        {/* Screenshots Upload */}
        <Card className="p-6 mb-6">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <ImageIcon className="w-5 h-5 text-primary" />
              <Label>Screenshots ZIP (optioneel)</Label>
            </div>
            
            <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
              <input
                type="file"
                accept=".zip"
                onChange={(e) => handleFileChange(e.target.files?.[0] || null, setScreenshotsZip)}
                className="hidden"
                id="screenshots-upload"
                disabled={uploading}
              />
              <label htmlFor="screenshots-upload" className="cursor-pointer">
                {screenshotsZip ? (
                  <div className="flex items-center justify-center gap-2 text-green-600">
                    <CheckCircle2 className="w-5 h-5" />
                    <span className="font-medium">{screenshotsZip.name}</span>
                  </div>
                ) : (
                  <>
                    <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      Klik om screenshots ZIP te uploaden
                    </p>
                  </>
                )}
              </label>
            </div>

            <p className="text-xs text-muted-foreground">
              Bestandsnaam format: <code className="bg-muted px-1 py-0.5 rounded">labelnoir_hash.png</code>
              <br />
              Wordt automatisch gelinkt aan leads op basis van domain
            </p>
          </div>
        </Card>

        {/* Reports Upload */}
        <Card className="p-6 mb-6">
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-primary" />
              <Label>Reports ZIP (optioneel)</Label>
            </div>
            
            <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
              <input
                type="file"
                accept=".zip"
                onChange={(e) => handleFileChange(e.target.files?.[0] || null, setReportsZip)}
                className="hidden"
                id="reports-upload"
                disabled={uploading}
              />
              <label htmlFor="reports-upload" className="cursor-pointer">
                {reportsZip ? (
                  <div className="flex items-center justify-center gap-2 text-green-600">
                    <CheckCircle2 className="w-5 h-5" />
                    <span className="font-medium">{reportsZip.name}</span>
                  </div>
                ) : (
                  <>
                    <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      Klik om reports ZIP te uploaden
                    </p>
                  </>
                )}
              </label>
            </div>

            <p className="text-xs text-muted-foreground">
              Bestandsnaam format: <code className="bg-muted px-1 py-0.5 rounded">labelnoir_report.pdf</code>
              <br />
              Wordt automatisch gelinkt aan leads op basis van domain
            </p>
          </div>
        </Card>

        {/* Error */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Result */}
        {result && (
          <Card className="p-6 mb-6 bg-green-50 border-green-200">
            <h3 className="font-semibold text-green-900 mb-4">Import Succesvol!</h3>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-sm text-green-700">Leads geïmporteerd</p>
                <p className="text-2xl font-bold text-green-900">{result.leads_imported}</p>
              </div>
              <div>
                <p className="text-sm text-green-700">Complete leads</p>
                <p className="text-2xl font-bold text-green-900">{result.leads_complete}</p>
              </div>
              <div>
                <p className="text-sm text-green-700">Screenshots</p>
                <p className="text-2xl font-bold text-green-900">{result.screenshots_uploaded}</p>
              </div>
              <div>
                <p className="text-sm text-green-700">Reports</p>
                <p className="text-2xl font-bold text-green-900">{result.reports_uploaded}</p>
              </div>
            </div>

            {result.warnings.length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-semibold text-orange-900 mb-2">
                  Warnings ({result.warnings.length})
                </p>
                <div className="text-xs text-orange-800 max-h-40 overflow-y-auto">
                  {result.warnings.slice(0, 10).map((warning, idx) => (
                    <p key={idx}>• {warning}</p>
                  ))}
                  {result.warnings.length > 10 && (
                    <p className="italic">... en {result.warnings.length - 10} meer</p>
                  )}
                </div>
              </div>
            )}
          </Card>
        )}

        {/* Submit */}
        <Button 
          type="submit" 
          className="w-full" 
          size="lg"
          disabled={uploading || !listName || !excelFile}
        >
          {uploading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Importeren...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4 mr-2" />
              Start Bulk Import
            </>
          )}
        </Button>
      </form>
    </div>
  );
}
