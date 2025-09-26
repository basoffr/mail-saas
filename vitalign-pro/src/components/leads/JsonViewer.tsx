import React from 'react';
import { Card } from '@/components/ui/card';

interface JsonViewerProps {
  data: any;
  title?: string;
}

export function JsonViewer({ data, title }: JsonViewerProps) {
  const formatValue = (value: any, depth: number = 0): React.ReactNode => {
    if (value === null) return <span className="text-muted-foreground">null</span>;
    if (value === undefined) return <span className="text-muted-foreground">undefined</span>;
    
    if (typeof value === 'string') {
      return <span className="text-green-600">"{value}"</span>;
    }
    
    if (typeof value === 'number') {
      return <span className="text-blue-600">{value}</span>;
    }
    
    if (typeof value === 'boolean') {
      return <span className="text-purple-600">{value.toString()}</span>;
    }
    
    if (Array.isArray(value)) {
      if (value.length === 0) return <span className="text-muted-foreground">[]</span>;
      
      return (
        <div>
          <span className="text-muted-foreground">[</span>
          <div className="ml-4">
            {value.map((item, index) => (
              <div key={index} className="flex">
                {formatValue(item, depth + 1)}
                {index < value.length - 1 && <span className="text-muted-foreground">,</span>}
              </div>
            ))}
          </div>
          <span className="text-muted-foreground">]</span>
        </div>
      );
    }
    
    if (typeof value === 'object') {
      const entries = Object.entries(value);
      if (entries.length === 0) return <span className="text-muted-foreground">{}</span>;
      
      return (
        <div>
          <span className="text-muted-foreground">{'{'}</span>
          <div className="ml-4">
            {entries.map(([key, val], index) => (
              <div key={key} className="flex gap-2">
                <span className="text-red-600">"{key}"</span>
                <span className="text-muted-foreground">:</span>
                {formatValue(val, depth + 1)}
                {index < entries.length - 1 && <span className="text-muted-foreground">,</span>}
              </div>
            ))}
          </div>
          <span className="text-muted-foreground">{'}'}</span>
        </div>
      );
    }
    
    return <span>{String(value)}</span>;
  };

  return (
    <Card className="p-4">
      {title && (
        <h3 className="text-sm font-medium mb-3 text-card-foreground">{title}</h3>
      )}
      <div className="bg-muted/30 rounded-lg p-3 overflow-auto max-h-96">
        <pre className="text-sm font-mono whitespace-pre-wrap">
          {formatValue(data)}
        </pre>
      </div>
    </Card>
  );
}