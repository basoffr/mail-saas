import type { 
  ReportItem, 
  ReportsQuery, 
  BulkUploadResult, 
  ReportUploadPayload, 
  ReportBindPayload,
  BulkMode,
  BulkMapRow 
} from '@/types/report';

// Mock data
const mockReports: ReportItem[] = [
  {
    id: '1',
    filename: 'campaign_report_q1.pdf',
    type: 'pdf',
    sizeBytes: 2548000,
    uploadedAt: '2024-03-15T14:30:00Z',
    boundTo: { kind: 'campaign', id: 'camp1', label: 'Q1 Marketing Campaign' },
    checksum: 'abc123',
  },
  {
    id: '2',
    filename: 'lead_analysis.xlsx',
    type: 'xlsx',
    sizeBytes: 1024000,
    uploadedAt: '2024-03-14T09:15:00Z',
    boundTo: { kind: 'lead', id: 'lead1', label: 'john@example.com' },
    checksum: 'def456',
  },
  {
    id: '3',
    filename: 'product_hero.jpg',
    type: 'jpg',
    sizeBytes: 512000,
    uploadedAt: '2024-03-13T16:45:00Z',
    boundTo: null,
    checksum: 'ghi789',
  },
  {
    id: '4',
    filename: 'monthly_stats.png',
    type: 'png',
    sizeBytes: 256000,
    uploadedAt: '2024-03-12T11:20:00Z',
    boundTo: { kind: 'campaign', id: 'camp2', label: 'Monthly Newsletter' },
    checksum: 'jkl012',
  },
];

// Mock leads and campaigns for binding
const mockLeads = [
  { id: 'lead1', email: 'john@example.com', company: 'ACME Corp' },
  { id: 'lead2', email: 'jane@techstart.io', company: 'TechStart' },
  { id: 'lead3', email: 'mike@innovate.com', company: 'Innovate Ltd' },
];

const mockCampaigns = [
  { id: 'camp1', name: 'Q1 Marketing Campaign' },
  { id: 'camp2', name: 'Monthly Newsletter' },
  { id: 'camp3', name: 'Product Launch 2024' },
];

export const reportsService = {
  async getReports(query: ReportsQuery): Promise<{ items: ReportItem[]; total: number }> {
    await new Promise(resolve => setTimeout(resolve, 500)); // Simulate network delay
    
    let filtered = [...mockReports];

    // Apply filters
    if (query.search) {
      const search = query.search.toLowerCase();
      filtered = filtered.filter(r => 
        r.filename.toLowerCase().includes(search)
      );
    }

    if (query.types?.length) {
      filtered = filtered.filter(r => query.types!.includes(r.type));
    }

    if (query.boundFilter === 'bound') {
      filtered = filtered.filter(r => r.boundTo);
    } else if (query.boundFilter === 'unbound') {
      filtered = filtered.filter(r => !r.boundTo);
    }

    if (query.boundKind) {
      filtered = filtered.filter(r => r.boundTo?.kind === query.boundKind);
    }

    if (query.boundId) {
      filtered = filtered.filter(r => r.boundTo?.id === query.boundId);
    }

    // Apply pagination
    const start = (query.page - 1) * query.pageSize;
    const items = filtered.slice(start, start + query.pageSize);

    return { items, total: filtered.length };
  },

  async uploadReport(payload: ReportUploadPayload): Promise<ReportItem> {
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const report: ReportItem = {
      id: `report_${Date.now()}`,
      filename: payload.file.name,
      type: payload.file.name.split('.').pop()?.toLowerCase() as any,
      sizeBytes: payload.file.size,
      uploadedAt: new Date().toISOString(),
      boundTo: payload.leadId 
        ? { kind: 'lead', id: payload.leadId, label: mockLeads.find(l => l.id === payload.leadId)?.email }
        : payload.campaignId
        ? { kind: 'campaign', id: payload.campaignId, label: mockCampaigns.find(c => c.id === payload.campaignId)?.name }
        : null,
      checksum: Math.random().toString(36).substring(7),
    };

    mockReports.unshift(report);
    return report;
  },

  async bulkUpload(zipFile: File, mode: BulkMode): Promise<BulkUploadResult> {
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Mock parsing ZIP contents
    const mockFiles = [
      'hero_image.jpg',
      'john@example.com_report.pdf',
      'campaign_stats.xlsx',
      'product_banner.png',
      'jane@techstart.io_analysis.pdf',
    ];

    const mappings = mockFiles.map(fileName => {
      const baseKey = fileName.replace(/\.(jpg|png|pdf|xlsx)$/i, '');
      
      if (mode === 'by_email') {
        const emailMatch = baseKey.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
        if (emailMatch) {
          const lead = mockLeads.find(l => l.email === emailMatch[1]);
          return {
            fileName,
            to: lead ? { kind: 'lead' as const, id: lead.id } : undefined,
            status: lead ? 'ok' as const : 'failed' as const,
            error: lead ? undefined : 'No matching lead found',
          };
        }
      } else if (mode === 'by_image_key') {
        // Mock image key matching
        return {
          fileName,
          to: { kind: 'image_key' as const },
          status: Math.random() > 0.2 ? 'ok' as const : 'failed' as const,
          error: Math.random() > 0.2 ? undefined : 'Invalid image key format',
        };
      }

      return {
        fileName,
        status: 'failed' as const,
        error: 'No matching target found',
      };
    });

    const uploaded = mappings.filter(m => m.status === 'ok').length;

    return {
      total: mockFiles.length,
      uploaded,
      failed: mockFiles.length - uploaded,
      mappings,
    };
  },

  async generateBulkMapping(zipFile: File, mode: BulkMode): Promise<BulkMapRow[]> {
    await new Promise(resolve => setTimeout(resolve, 1000));

    const mockFiles = [
      'hero_image.jpg',
      'john@example.com_report.pdf',
      'campaign_stats.xlsx',
      'product_banner.png',
      'jane@techstart.io_analysis.pdf',
      'unknown_file.jpg',
    ];

    return mockFiles.map(fileName => {
      const baseKey = fileName.replace(/\.(jpg|png|pdf|xlsx)$/i, '');
      
      if (mode === 'by_email') {
        const emailMatch = baseKey.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
        if (emailMatch) {
          const lead = mockLeads.find(l => l.email === emailMatch[1]);
          return {
            fileName,
            baseKey,
            target: lead ? { kind: 'lead' as const, id: lead.id, email: lead.email } : undefined,
            status: lead ? 'matched' as const : 'unmatched' as const,
            reason: lead ? undefined : 'No matching lead found for email',
          };
        }
      } else if (mode === 'by_image_key') {
        return {
          fileName,
          baseKey,
          target: { kind: 'image_key' as const },
          status: Math.random() > 0.3 ? 'matched' as const : 'unmatched' as const,
          reason: Math.random() > 0.3 ? undefined : 'Invalid image key format',
        };
      }

      return {
        fileName,
        baseKey,
        status: 'unmatched' as const,
        reason: 'No matching pattern found',
      };
    });
  },

  async bindReport(payload: ReportBindPayload): Promise<{ ok: true }> {
    await new Promise(resolve => setTimeout(resolve, 300));
    
    const report = mockReports.find(r => r.id === payload.reportId);
    if (report) {
      if (payload.leadId) {
        const lead = mockLeads.find(l => l.id === payload.leadId);
        report.boundTo = { kind: 'lead', id: payload.leadId, label: lead?.email };
      } else if (payload.campaignId) {
        const campaign = mockCampaigns.find(c => c.id === payload.campaignId);
        report.boundTo = { kind: 'campaign', id: payload.campaignId, label: campaign?.name };
      }
    }
    
    return { ok: true };
  },

  async unbindReport(reportId: string): Promise<{ ok: true }> {
    await new Promise(resolve => setTimeout(resolve, 300));
    
    const report = mockReports.find(r => r.id === reportId);
    if (report) {
      report.boundTo = null;
    }
    
    return { ok: true };
  },

  async getDownloadUrl(reportId: string): Promise<string> {
    await new Promise(resolve => setTimeout(resolve, 200));
    // Mock download URL
    return `https://api.example.com/reports/${reportId}/download`;
  },

  // Helper methods for binding
  async searchLeads(query: string): Promise<Array<{ id: string; email: string; company?: string }>> {
    await new Promise(resolve => setTimeout(resolve, 300));
    
    const search = query.toLowerCase();
    return mockLeads.filter(l => 
      l.email.toLowerCase().includes(search) || 
      l.company?.toLowerCase().includes(search)
    );
  },

  async searchCampaigns(query: string): Promise<Array<{ id: string; name: string }>> {
    await new Promise(resolve => setTimeout(resolve, 300));
    
    const search = query.toLowerCase();
    return mockCampaigns.filter(c => 
      c.name.toLowerCase().includes(search)
    );
  },
};