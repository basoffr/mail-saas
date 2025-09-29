import React from 'react';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface DnsStatus {
  spf: boolean;
  dkim: boolean;
  dmarc: boolean;
}

interface DnsChecklistProps {
  status: DnsStatus;
  loading?: boolean;
}

interface DnsItemProps {
  name: string;
  status: boolean;
  description: string;
}

const DnsItem: React.FC<DnsItemProps> = ({ name, status, description }) => {
  const Icon = status ? CheckCircle : XCircle;
  const badgeVariant = status ? 'default' : 'destructive';
  const iconColor = status ? 'text-success' : 'text-destructive';

  return (
    <div className="flex items-center justify-between p-3 rounded-lg border bg-card">
      <div className="flex items-center gap-3">
        <Icon className={`h-5 w-5 ${iconColor}`} />
        <div>
          <p className="font-medium text-foreground">{name}</p>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
      <Badge variant={badgeVariant} className="font-medium">
        {status ? 'OK' : 'NOK'}
      </Badge>
    </div>
  );
};

export const DnsChecklist: React.FC<DnsChecklistProps> = ({
  status,
  loading = false
}) => {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex items-center justify-between p-3 rounded-lg border bg-card">
            <div className="flex items-center gap-3">
              <div className="h-5 w-5 bg-muted animate-pulse rounded-full" />
              <div className="space-y-1">
                <div className="h-4 bg-muted animate-pulse rounded w-16" />
                <div className="h-3 bg-muted animate-pulse rounded w-32" />
              </div>
            </div>
            <div className="h-6 bg-muted animate-pulse rounded w-12" />
          </div>
        ))}
      </div>
    );
  }

  const dnsItems = [
    {
      name: 'SPF',
      status: status.spf,
      description: 'Sender Policy Framework record'
    },
    {
      name: 'DKIM',
      status: status.dkim,
      description: 'DomainKeys Identified Mail signature'
    },
    {
      name: 'DMARC',
      status: status.dmarc,
      description: 'Domain-based Message Authentication'
    }
  ];

  const allConfigured = Object.values(status).every(Boolean);
  const noneConfigured = Object.values(status).every(s => !s);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <AlertCircle className={`h-4 w-4 ${
          allConfigured ? 'text-success' : 
          noneConfigured ? 'text-destructive' : 'text-warning'
        }`} />
        <p className="text-sm font-medium">
          {allConfigured ? 'Alle DNS records zijn geconfigureerd' :
           noneConfigured ? 'Geen DNS records geconfigureerd' :
           'Sommige DNS records ontbreken'}
        </p>
      </div>
      
      <div className="space-y-3">
        {dnsItems.map((item) => (
          <DnsItem
            key={item.name}
            name={item.name}
            status={item.status}
            description={item.description}
          />
        ))}
      </div>
      
      {!allConfigured && (
        <div className="p-3 rounded-lg bg-warning/10 border border-warning/20">
          <p className="text-sm text-warning-foreground">
            <strong>Let op:</strong> Ontbrekende DNS records kunnen de deliverability van je emails beïnvloeden.
            Configureer alle records voor optimale prestaties.
          </p>
        </div>
      )}
    </div>
  );
};
