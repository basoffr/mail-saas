import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Copy, Check } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface CopyFieldProps {
  label: string;
  value: string;
  onCopy?: (value: string) => Promise<boolean>;
}

export const CopyField: React.FC<CopyFieldProps> = ({
  label,
  value,
  onCopy
}) => {
  const { toast } = useToast();
  const [copied, setCopied] = useState(false);
  const [copying, setCopying] = useState(false);

  const handleCopy = async () => {
    setCopying(true);
    
    try {
      let success = false;
      
      if (onCopy) {
        success = await onCopy(value);
      } else {
        // Default clipboard API
        await navigator.clipboard.writeText(value);
        success = true;
      }
      
      if (success) {
        setCopied(true);
        toast({
          title: 'Gekopieerd!',
          description: `${label} is gekopieerd naar het klembord`,
        });
        
        // Reset copied state after 2 seconds
        setTimeout(() => setCopied(false), 2000);
      } else {
        throw new Error('Copy failed');
      }
    } catch (error) {
      toast({
        title: 'Kopiëren mislukt',
        description: 'Kon de tekst niet kopiëren naar het klembord',
        variant: 'destructive'
      });
    } finally {
      setCopying(false);
    }
  };

  return (
    <div className="space-y-2">
      <Label htmlFor={`copy-field-${label.toLowerCase().replace(/\s+/g, '-')}`}>
        {label}
      </Label>
      <div className="flex gap-2">
        <Input
          id={`copy-field-${label.toLowerCase().replace(/\s+/g, '-')}`}
          value={value}
          readOnly
          className="flex-1 bg-muted/50"
        />
        <Button
          variant="outline"
          size="sm"
          onClick={handleCopy}
          disabled={copying}
          className="gap-2 min-w-[80px]"
        >
          {copied ? (
            <>
              <Check className="h-4 w-4 text-success" />
              <span className="text-success">OK</span>
            </>
          ) : (
            <>
              <Copy className="h-4 w-4" />
              Kopieer
            </>
          )}
        </Button>
      </div>
    </div>
  );
};
