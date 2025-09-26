import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FileDropzoneProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  maxSize?: number;
  className?: string;
}

export function FileDropzone({ onFileSelect, accept, maxSize, className }: FileDropzoneProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: accept ? { 'application/octet-stream': accept.split(',') } : undefined,
    maxSize,
    multiple: false,
  });

  return (
    <div className={cn('space-y-2', className)}>
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          'hover:border-primary/50 hover:bg-primary/5',
          isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'
        )}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
        {isDragActive ? (
          <p className="text-primary">Drop the file here...</p>
        ) : (
          <div>
            <p className="text-foreground font-medium mb-2">
              Click to upload or drag and drop
            </p>
            {accept && (
              <p className="text-sm text-muted-foreground mb-1">
                Supported formats: {accept.replace(/\./g, '').toUpperCase()}
              </p>
            )}
            {maxSize && (
              <p className="text-sm text-muted-foreground">
                Maximum size: {Math.round(maxSize / 1024 / 1024)}MB
              </p>
            )}
          </div>
        )}
      </div>

      {fileRejections.length > 0 && (
        <div className="space-y-1">
          {fileRejections.map(({ file, errors }) => (
            <div key={file.name} className="text-sm text-red-600">
              {errors.map(error => (
                <p key={error.code}>{error.message}</p>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}