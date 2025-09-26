import { useState, useEffect } from 'react';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { reportsService } from '@/services/reports';

interface BindingSelectorProps {
  type: 'lead' | 'campaign';
  value: string;
  onChange: (id: string) => void;
}

export function BindingSelector({ type, value, onChange }: BindingSelectorProps) {
  const [search, setSearch] = useState('');
  const [options, setOptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedItem, setSelectedItem] = useState<any>(null);

  useEffect(() => {
    if (search.length >= 2) {
      searchOptions();
    } else {
      setOptions([]);
    }
  }, [search, type]);

  const searchOptions = async () => {
    setLoading(true);
    try {
      const results = type === 'lead' 
        ? await reportsService.searchLeads(search)
        : await reportsService.searchCampaigns(search);
      setOptions(results);
    } catch (error) {
      setOptions([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (item: any) => {
    setSelectedItem(item);
    onChange(item.id);
    setSearch('');
    setOptions([]);
  };

  const handleClear = () => {
    setSelectedItem(null);
    onChange('');
    setSearch('');
    setOptions([]);
  };

  if (selectedItem) {
    return (
      <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
        <div>
          <p className="font-medium">
            {type === 'lead' ? selectedItem.email : selectedItem.name}
          </p>
          {type === 'lead' && selectedItem.company && (
            <p className="text-sm text-muted-foreground">{selectedItem.company}</p>
          )}
        </div>
        <Button size="sm" variant="ghost" onClick={handleClear}>
          Clear
        </Button>
      </div>
    );
  }

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder={`Search ${type}s...`}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {options.length > 0 && (
        <Card className="absolute top-full left-0 right-0 z-10 mt-1 p-2 max-h-60 overflow-y-auto">
          {options.map((item) => (
            <button
              key={item.id}
              onClick={() => handleSelect(item)}
              className="w-full text-left p-2 rounded hover:bg-muted transition-colors"
            >
              <p className="font-medium">
                {type === 'lead' ? item.email : item.name}
              </p>
              {type === 'lead' && item.company && (
                <p className="text-sm text-muted-foreground">{item.company}</p>
              )}
            </button>
          ))}
        </Card>
      )}

      {loading && (
        <Card className="absolute top-full left-0 right-0 z-10 mt-1 p-4">
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-3 w-3/4" />
          </div>
        </Card>
      )}

      {search.length >= 2 && !loading && options.length === 0 && (
        <Card className="absolute top-full left-0 right-0 z-10 mt-1 p-4 text-center text-muted-foreground">
          No {type}s found
        </Card>
      )}
    </div>
  );
}