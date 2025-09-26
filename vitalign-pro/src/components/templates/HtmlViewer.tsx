import { Badge } from '@/components/ui/badge';

interface HtmlViewerProps {
  content: string;
}

export function HtmlViewer({ content }: HtmlViewerProps) {
  // Highlight template variables in the content
  const highlightVariables = (text: string) => {
    // Match {{variable}} and {{variable|helper}} patterns
    const variableRegex = /\{\{([^}]+)\}\}/g;
    const parts = text.split(variableRegex);
    
    return parts.map((part, index) => {
      if (index % 2 === 1) {
        // This is a variable (every odd index after split)
        return (
          <Badge 
            key={index} 
            variant="secondary" 
            className="mx-1 font-mono text-xs"
          >
            {`{{${part}}}`}
          </Badge>
        );
      }
      return part;
    });
  };

  return (
    <div className="space-y-2">
      {content.split('\n').map((line, index) => (
        <div key={index} className="leading-relaxed">
          {highlightVariables(line)}
        </div>
      ))}
    </div>
  );
}