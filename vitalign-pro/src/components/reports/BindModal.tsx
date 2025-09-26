import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { BindingSelector } from './BindingSelector';
import type { ReportItem } from '@/types/report';
import { reportsService } from '@/services/reports';

interface BindModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  report: ReportItem | null;
  onSuccess: () => void;
}

export function BindModal({ open, onOpenChange, report, onSuccess }: BindModalProps) {
  const [bindingType, setBindingType] = useState<'lead' | 'campaign'>('lead');
  const [bindingId, setBindingId] = useState('');
  const [binding, setBinding] = useState(false);
  const { toast } = useToast();

  const handleBind = async () => {
    if (!report || !bindingId) return;

    setBinding(true);
    try {
      await reportsService.bindReport({
        reportId: report.id,
        ...(bindingType === 'lead' ? { leadId: bindingId } : { campaignId: bindingId }),
      });

      toast({
        title: 'Success',
        description: `Report bound to ${bindingType} successfully`,
      });

      onOpenChange(false);
      onSuccess();
    } catch (error) {
      toast({
        title: 'Error',
        description: `Failed to bind report to ${bindingType}`,
        variant: 'destructive',
      });
    } finally {
      setBinding(false);
    }
  };

  const handleClose = () => {
    setBindingId('');
    onOpenChange(false);
  };

  if (!report) return null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Bind Report</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <p className="text-sm text-muted-foreground mb-2">File:</p>
            <p className="font-medium">{report.filename}</p>
          </div>

          <div className="space-y-2">
            <Label>Bind To</Label>
            <Select value={bindingType} onValueChange={(value: any) => {
              setBindingType(value);
              setBindingId('');
            }}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="lead">Lead</SelectItem>
                <SelectItem value="campaign">Campaign</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Select {bindingType}</Label>
            <BindingSelector
              type={bindingType}
              value={bindingId}
              onChange={setBindingId}
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button 
              onClick={handleBind}
              disabled={!bindingId || binding}
            >
              {binding ? (
                <>
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent" />
                  Binding...
                </>
              ) : (
                `Bind to ${bindingType}`
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}