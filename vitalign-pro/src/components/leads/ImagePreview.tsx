import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { ImageIcon, AlertCircle } from 'lucide-react';
import { leadsService } from '@/services/leads';

interface ImagePreviewProps {
  imageKey?: string;
  alt?: string;
  className?: string;
}

export function ImagePreview({ imageKey, alt, className }: ImagePreviewProps) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!imageKey) {
      setImageUrl(null);
      setError(false);
      return;
    }

    setLoading(true);
    setError(false);

    leadsService.getImageUrl(imageKey)
      .then(url => {
        setImageUrl(url);
      })
      .catch(() => {
        setError(true);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [imageKey]);

  if (!imageKey) {
    return (
      <Card className={`p-6 border-dashed border-2 ${className}`}>
        <div className="flex flex-col items-center justify-center text-muted-foreground">
          <ImageIcon className="w-8 h-8 mb-2" />
          <span className="text-sm">No image</span>
        </div>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </Card>
    );
  }

  if (error || !imageUrl) {
    return (
      <Card className={`p-6 border-destructive/50 ${className}`}>
        <div className="flex flex-col items-center justify-center text-destructive">
          <AlertCircle className="w-8 h-8 mb-2" />
          <span className="text-sm">Failed to load image</span>
          {imageKey && (
            <span className="text-xs text-muted-foreground mt-1">Key: {imageKey}</span>
          )}
        </div>
      </Card>
    );
  }

  return (
    <Card className={`overflow-hidden ${className}`}>
      <img
        src={imageUrl}
        alt={alt || `Image ${imageKey}`}
        className="w-full h-full object-cover"
        onError={() => setError(true)}
      />
    </Card>
  );
}