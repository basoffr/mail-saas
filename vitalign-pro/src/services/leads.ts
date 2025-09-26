import { Lead, LeadsQuery, LeadsResponse, LeadStatus, ImportJobStatus, ImportPreview, ImportMapping } from '@/types/lead';

// Backend -> UI status mapping (centralized)
export type BackendLeadStatus = 'active' | 'suppressed' | 'bounced';

export const toUiLeadStatus = (s: BackendLeadStatus | string) => {
  switch (s) {
    case 'active':
      return { label: 'Actief', tone: 'success' as const };
    case 'suppressed':
      return { label: 'Onderdrukt', tone: 'warning' as const };
    case 'bounced':
      return { label: 'Bounced', tone: 'destructive' as const };
    default:
      return { label: String(s), tone: 'default' as const };
  }
};

export const toneToBadgeClass = (tone: 'success' | 'warning' | 'destructive' | 'default') => {
  switch (tone) {
    case 'success':
      return 'bg-success/15 text-success-foreground border border-success/20';
    case 'warning':
      return 'bg-warning/15 text-warning-foreground border border-warning/20';
    case 'destructive':
      return 'bg-destructive/15 text-destructive-foreground border border-destructive/20';
    default:
      return 'bg-muted text-muted-foreground';
  }
};

// Mock data
const mockLeads: Lead[] = [
  {
    id: '1',
    email: 'john.doe@acme.com',
    companyName: 'Acme Corporation',
    domain: 'acme.com',
    url: 'https://acme.com',
    tags: ['enterprise', 'saas'],
    status: LeadStatus.QUALIFIED,
    lastMailed: new Date('2024-01-15'),
    lastOpened: new Date('2024-01-16'),
    imageKey: 'acme-logo',
    vars: { industry: 'Technology', employees: 500, revenue: 10000000 },
    createdAt: new Date('2024-01-10'),
    updatedAt: new Date('2024-01-16')
  },
  {
    id: '2', 
    email: 'jane.smith@techstart.io',
    companyName: 'TechStart',
    domain: 'techstart.io',
    url: 'https://techstart.io',
    tags: ['startup', 'fintech'],
    status: LeadStatus.NEW,
    vars: { industry: 'Fintech', employees: 25 },
    createdAt: new Date('2024-01-12'),
    updatedAt: new Date('2024-01-12')
  },
  {
    id: '3',
    email: 'michael@globalcorp.org',
    companyName: 'Global Corp',
    domain: 'globalcorp.org',
    url: 'https://globalcorp.org',
    tags: ['enterprise', 'manufacturing'],
    status: LeadStatus.CONTACTED,
    lastMailed: new Date('2024-01-14'),
    imageKey: 'global-logo',
    vars: { industry: 'Manufacturing', employees: 1200, location: 'Germany' },
    createdAt: new Date('2024-01-08'),
    updatedAt: new Date('2024-01-14')
  },
  {
    id: '4',
    email: 'sarah.jones@innovate.co.uk',
    companyName: 'Innovate Ltd',
    domain: 'innovate.co.uk',
    url: 'https://innovate.co.uk',
    tags: ['startup', 'ai'],
    status: LeadStatus.RESPONDED,
    lastMailed: new Date('2024-01-13'),
    lastOpened: new Date('2024-01-17'),
    vars: { industry: 'AI/ML', employees: 50, funding: 'Series A' },
    createdAt: new Date('2024-01-09'),
    updatedAt: new Date('2024-01-17')
  },
  {
    id: '5',
    email: 'info@startup.com',
    companyName: 'Startup Inc',
    domain: 'startup.com',
    status: LeadStatus.BOUNCED,
    tags: ['startup'],
    vars: { industry: 'E-commerce' },
    createdAt: new Date('2024-01-11'),
    updatedAt: new Date('2024-01-11')
  }
];

let mockImportJobs: ImportJobStatus[] = [];

// Simulate API delays
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const leadsService = {
  async getLeads(query: LeadsQuery = {}): Promise<LeadsResponse> {
    await delay(300);
    
    let filtered = [...mockLeads];
    
    // Apply filters
    if (query.search) {
      const search = query.search.toLowerCase();
      filtered = filtered.filter(lead => 
        lead.email.toLowerCase().includes(search) ||
        lead.companyName?.toLowerCase().includes(search) ||
        lead.domain?.toLowerCase().includes(search)
      );
    }
    
    if (query.status?.length) {
      filtered = filtered.filter(lead => query.status!.includes(lead.status));
    }
    
    if (query.tags?.length) {
      filtered = filtered.filter(lead => 
        query.tags!.some(tag => lead.tags.includes(tag))
      );
    }
    
    if (query.hasImage !== undefined) {
      filtered = filtered.filter(lead => 
        query.hasImage ? !!lead.imageKey : !lead.imageKey
      );
    }
    
    if (query.hasVars !== undefined) {
      filtered = filtered.filter(lead => 
        query.hasVars ? Object.keys(lead.vars).length > 0 : Object.keys(lead.vars).length === 0
      );
    }
    
    if (query.tld?.length) {
      filtered = filtered.filter(lead => {
        if (!lead.domain) return false;
        return query.tld!.some(tld => lead.domain!.endsWith(tld));
      });
    }
    
    // Apply sorting
    if (query.sortBy) {
      filtered.sort((a, b) => {
        let aVal, bVal;
        
        switch (query.sortBy) {
          case 'email':
            aVal = a.email;
            bVal = b.email;
            break;
          case 'companyName':
            aVal = a.companyName || '';
            bVal = b.companyName || '';
            break;
          case 'lastMailed':
            aVal = a.lastMailed?.getTime() || 0;
            bVal = b.lastMailed?.getTime() || 0;
            break;
          case 'lastOpened':
            aVal = a.lastOpened?.getTime() || 0;
            bVal = b.lastOpened?.getTime() || 0;
            break;
          case 'createdAt':
            aVal = a.createdAt.getTime();
            bVal = b.createdAt.getTime();
            break;
          default:
            aVal = a.email;
            bVal = b.email;
        }
        
        if (query.sortOrder === 'desc') {
          return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
        }
        return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
      });
    }
    
    // Apply pagination
    const page = query.page || 1;
    const limit = query.limit || 25;
    const startIndex = (page - 1) * limit;
    const paginatedItems = filtered.slice(startIndex, startIndex + limit);
    
    return {
      items: paginatedItems,
      total: filtered.length
    };
  },

  async getLead(id: string): Promise<Lead | null> {
    await delay(200);
    return mockLeads.find(lead => lead.id === id) || null;
  },

  async importLeads(file: File, mapping: ImportMapping): Promise<ImportJobStatus> {
    await delay(500);
    
    const jobId = `import-${Date.now()}`;
    const job: ImportJobStatus = {
      id: jobId,
      status: 'pending',
      progress: 0,
      inserted: 0,
      updated: 0,
      skipped: 0,
      errors: [],
      createdAt: new Date()
    };
    
    mockImportJobs.push(job);
    
    // Simulate processing
    setTimeout(() => {
      const jobIndex = mockImportJobs.findIndex(j => j.id === jobId);
      if (jobIndex !== -1) {
        mockImportJobs[jobIndex] = {
          ...job,
          status: 'completed',
          progress: 100,
          inserted: 15,
          updated: 3,
          skipped: 2,
          completedAt: new Date()
        };
      }
    }, 3000);
    
    return job;
  },

  async getImportJob(jobId: string): Promise<ImportJobStatus | null> {
    await delay(100);
    return mockImportJobs.find(job => job.id === jobId) || null;
  },

  async previewImport(file: File): Promise<ImportPreview> {
    await delay(400);
    
    // Mock CSV preview
    return {
      headers: ['email', 'company_name', 'domain', 'industry', 'employees'],
      rows: [
        ['test1@example.com', 'Test Company 1', 'example.com', 'Technology', '100'],
        ['test2@example.com', 'Test Company 2', 'test.org', 'Healthcare', '50'],
        ['test3@example.com', 'Test Company 3', 'demo.io', 'Finance', '200'],
        ['john.doe@acme.com', 'Acme Corporation', 'acme.com', 'Technology', '500'], // Duplicate
        ['test4@example.com', 'Test Company 4', 'sample.net', 'Education', '75']
      ],
      duplicates: [3] // Row index 3 is a duplicate
    };
  },

  async getImageUrl(imageKey: string): Promise<string> {
    await delay(100);
    // Return mock image URLs
    const mockImages: Record<string, string> = {
      'acme-logo': 'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=200&h=200&fit=crop',
      'global-logo': 'https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=200&h=200&fit=crop'
    };
    
    return mockImages[imageKey] || 'https://images.unsplash.com/photo-1560472355-536de3962603?w=200&h=200&fit=crop';
  }
};