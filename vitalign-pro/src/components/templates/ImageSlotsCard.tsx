import { Image } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface Asset {
  key: string;
  type: 'static' | 'cid';
}

interface ImageSlotsCardProps {
  assets: Asset[];
}

export function ImageSlotsCard({ assets }: ImageSlotsCardProps) {
  const staticAssets = assets.filter(asset => asset.type === 'static');
  const cidAssets = assets.filter(asset => asset.type === 'cid');

  return (
    <Card className="rounded-2xl shadow-soft p-6">
      <div className="flex items-center gap-2 mb-4">
        <Image className="h-5 w-5" />
        <h2 className="text-lg font-semibold">Afbeeldingen</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Static Images */}
        <div>
          <h3 className="font-medium mb-3 flex items-center gap-2">
            Statische afbeeldingen
            <Badge variant="outline">{staticAssets.length}</Badge>
          </h3>
          {staticAssets.length > 0 ? (
            <div className="space-y-2">
              {staticAssets.map((asset) => (
                <div key={asset.key} className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                  <div className="w-8 h-8 bg-primary/10 rounded flex items-center justify-center">
                    <Image className="h-4 w-4 text-primary" />
                  </div>
                  <div className="flex-1">
                    <p className="font-mono text-sm">{asset.key}</p>
                    <p className="text-xs text-muted-foreground">Dezelfde afbeelding voor alle ontvangers</p>
                  </div>
                  <Badge variant="secondary">Statisch</Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">Geen statische afbeeldingen</p>
          )}
        </div>

        {/* CID Images */}
        <div>
          <h3 className="font-medium mb-3 flex items-center gap-2">
            Per-lead afbeeldingen (CID)
            <Badge variant="outline">{cidAssets.length}</Badge>
          </h3>
          {cidAssets.length > 0 ? (
            <div className="space-y-2">
              {cidAssets.map((asset) => (
                <div key={asset.key} className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                  <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded flex items-center justify-center">
                    <Image className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <p className="font-mono text-sm">{asset.key}</p>
                    <p className="text-xs text-muted-foreground">Unieke afbeelding per lead (indien beschikbaar)</p>
                  </div>
                  <Badge variant="default">CID</Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">Geen per-lead afbeeldingen</p>
          )}
        </div>
      </div>

      {assets.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <Image className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p>Deze template gebruikt geen afbeeldingen</p>
        </div>
      )}
    </Card>
  );
}