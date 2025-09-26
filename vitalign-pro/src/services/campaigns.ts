import { 
  Campaign, 
  CampaignDetail, 
  CampaignCreatePayload, 
  CampaignStatus, 
  CampaignMessage, 
  MessageStatus, 
  DryRunResult 
} from '@/types/campaign';

// Mock data
const mockCampaigns: Campaign[] = [
  {
    id: '1',
    name: 'Q1 Product Launch Outreach',
    status: CampaignStatus.RUNNING,
    templateId: '1',
    templateName: 'Product Demo Invitation',
    targetCount: 500,
    sentCount: 342,
    openCount: 127,
    clickCount: 23,
    bounceCount: 8,
    replyCount: 12,
    startDate: new Date('2024-01-15T09:00:00'),
    createdAt: new Date('2024-01-10T14:30:00'),
    updatedAt: new Date('2024-01-18T16:45:00')
  },
  {
    id: '2',
    name: 'Welcome Series - New Leads',
    status: CampaignStatus.PAUSED,
    templateId: '2',
    templateName: 'Welcome Email',
    targetCount: 1200,
    sentCount: 890,
    openCount: 445,
    clickCount: 89,
    bounceCount: 15,
    replyCount: 34,
    startDate: new Date('2024-01-08T08:00:00'),
    createdAt: new Date('2024-01-05T11:15:00'),
    updatedAt: new Date('2024-01-17T10:20:00')
  },
  {
    id: '3',
    name: 'Enterprise Prospects Follow-up',
    status: CampaignStatus.SCHEDULED,
    templateId: '3',
    templateName: 'Follow-up Sequence',
    targetCount: 250,
    sentCount: 0,
    openCount: 0,
    clickCount: 0,
    bounceCount: 0,
    replyCount: 0,
    startDate: new Date('2024-01-25T09:30:00'),
    createdAt: new Date('2024-01-18T16:00:00'),
    updatedAt: new Date('2024-01-18T16:00:00')
  },
  {
    id: '4',
    name: 'Holiday Promotion Campaign',
    status: CampaignStatus.COMPLETED,
    templateId: '4',
    templateName: 'Holiday Special Offer',
    targetCount: 2000,
    sentCount: 1987,
    openCount: 892,
    clickCount: 234,
    bounceCount: 43,
    replyCount: 67,
    startDate: new Date('2023-12-01T10:00:00'),
    endDate: new Date('2023-12-24T23:59:00'),
    createdAt: new Date('2023-11-25T09:00:00'),
    updatedAt: new Date('2023-12-24T23:59:00')
  }
];

const mockMessages: CampaignMessage[] = [
  {
    id: '1',
    campaignId: '1',
    leadId: '1',
    leadEmail: 'john.doe@acme.com',
    leadCompany: 'Acme Corporation',
    status: MessageStatus.OPENED,
    sentAt: new Date('2024-01-15T09:15:00'),
    deliveredAt: new Date('2024-01-15T09:16:00'),
    openedAt: new Date('2024-01-15T14:30:00'),
    attempts: 1,
    isFollowUp: false,
    templateSnapshot: 'Email content here...'
  },
  {
    id: '2',
    campaignId: '1',
    leadId: '2',
    leadEmail: 'jane.smith@techstart.io',
    leadCompany: 'TechStart',
    status: MessageStatus.BOUNCED,
    sentAt: new Date('2024-01-15T09:20:00'),
    bouncedAt: new Date('2024-01-15T09:21:00'),
    attempts: 1,
    isFollowUp: false,
    templateSnapshot: 'Email content here...'
  },
  {
    id: '3',
    campaignId: '1',
    leadId: '3',
    leadEmail: 'michael@globalcorp.org',
    leadCompany: 'Global Corp',
    status: MessageStatus.REPLIED,
    sentAt: new Date('2024-01-15T10:00:00'),
    deliveredAt: new Date('2024-01-15T10:01:00'),
    openedAt: new Date('2024-01-15T11:30:00'),
    repliedAt: new Date('2024-01-15T15:45:00'),
    attempts: 1,
    isFollowUp: false,
    templateSnapshot: 'Email content here...'
  }
];

let mockCampaignDetails: Record<string, CampaignDetail> = {};

// Initialize mock detail data
mockCampaigns.forEach(campaign => {
  mockCampaignDetails[campaign.id] = {
    ...campaign,
    settings: {
      followUp: {
        enabled: true,
        days: 3,
        attachmentRequired: false
      },
      dedupe: {
        suppressBounced: true,
        contactedLastDays: 14,
        onePerDomain: false
      },
      domains: ['com', 'org', 'io'],
      throttle: {
        perHour: 50,
        windowStart: '08:00',
        windowEnd: '17:00',
        weekdays: true
      },
      retry: {
        maxAttempts: 3,
        backoffHours: 24
      }
    },
    stats: {
      totalMessages: campaign.targetCount,
      sentToday: Math.floor(Math.random() * 50),
      scheduledCount: campaign.targetCount - campaign.sentCount,
      followUpCount: Math.floor(campaign.sentCount * 0.1),
      sentByDay: generateMockSentByDay(campaign.startDate, campaign.sentCount)
    }
  };
});

function generateMockSentByDay(startDate: Date, totalSent: number): { date: string; sent: number }[] {
  const data = [];
  const days = 14;
  const avgPerDay = Math.floor(totalSent / days);
  
  for (let i = 0; i < days; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    
    // Add some randomness to make it look realistic
    const variance = Math.floor(avgPerDay * 0.3);
    const sent = Math.max(0, avgPerDay + Math.floor(Math.random() * variance * 2) - variance);
    
    data.push({
      date: date.toISOString().split('T')[0],
      sent
    });
  }
  
  return data;
}

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const campaignsService = {
  async getCampaigns(): Promise<{ items: Campaign[]; total: number }> {
    await delay(300);
    return {
      items: mockCampaigns,
      total: mockCampaigns.length
    };
  },

  async createCampaign(payload: CampaignCreatePayload): Promise<{ id: string }> {
    await delay(500);
    const id = `campaign-${Date.now()}`;
    
    const newCampaign: Campaign = {
      id,
      name: payload.name,
      status: payload.startType === 'now' ? CampaignStatus.RUNNING : CampaignStatus.SCHEDULED,
      templateId: payload.templateId,
      templateName: 'Template Name', // Would be fetched
      targetCount: payload.leadIds?.length || 0,
      sentCount: 0,
      openCount: 0,
      clickCount: 0,
      bounceCount: 0,
      replyCount: 0,
      startDate: payload.scheduledStart || new Date(),
      createdAt: new Date(),
      updatedAt: new Date()
    };
    
    mockCampaigns.unshift(newCampaign);
    return { id };
  },

  async getCampaign(id: string): Promise<CampaignDetail | null> {
    await delay(200);
    return mockCampaignDetails[id] || null;
  },

  async pauseCampaign(id: string): Promise<{ ok: boolean }> {
    await delay(300);
    const campaign = mockCampaigns.find(c => c.id === id);
    if (campaign) {
      campaign.status = CampaignStatus.PAUSED;
      campaign.updatedAt = new Date();
      if (mockCampaignDetails[id]) {
        mockCampaignDetails[id].status = CampaignStatus.PAUSED;
        mockCampaignDetails[id].updatedAt = new Date();
      }
    }
    return { ok: true };
  },

  async resumeCampaign(id: string): Promise<{ ok: boolean }> {
    await delay(300);
    const campaign = mockCampaigns.find(c => c.id === id);
    if (campaign) {
      campaign.status = CampaignStatus.RUNNING;
      campaign.updatedAt = new Date();
      if (mockCampaignDetails[id]) {
        mockCampaignDetails[id].status = CampaignStatus.RUNNING;
        mockCampaignDetails[id].updatedAt = new Date();
      }
    }
    return { ok: true };
  },

  async stopCampaign(id: string): Promise<{ ok: boolean }> {
    await delay(300);
    const campaign = mockCampaigns.find(c => c.id === id);
    if (campaign) {
      campaign.status = CampaignStatus.STOPPED;
      campaign.endDate = new Date();
      campaign.updatedAt = new Date();
      if (mockCampaignDetails[id]) {
        mockCampaignDetails[id].status = CampaignStatus.STOPPED;
        mockCampaignDetails[id].endDate = new Date();
        mockCampaignDetails[id].updatedAt = new Date();
      }
    }
    return { ok: true };
  },

  async duplicateCampaign(id: string): Promise<{ id: string }> {
    await delay(400);
    const original = mockCampaigns.find(c => c.id === id);
    if (!original) throw new Error('Campaign not found');

    const newId = `campaign-${Date.now()}`;
    const duplicate: Campaign = {
      ...original,
      id: newId,
      name: `${original.name} (Copy)`,
      status: CampaignStatus.DRAFT,
      sentCount: 0,
      openCount: 0,
      clickCount: 0,
      bounceCount: 0,
      replyCount: 0,
      startDate: new Date(),
      createdAt: new Date(),
      updatedAt: new Date()
    };

    mockCampaigns.unshift(duplicate);
    return { id: newId };
  },

  async dryRunCampaign(id: string): Promise<DryRunResult> {
    await delay(800);
    const campaign = mockCampaignDetails[id];
    if (!campaign) throw new Error('Campaign not found');

    return {
      totalPlanned: campaign.targetCount,
      byDay: generateMockSentByDay(new Date(), campaign.targetCount).slice(0, 7).map(item => ({
        date: item.date,
        planned: item.sent
      })),
      warnings: [
        'Lead john@example.com is missing firstName variable',
        '3 leads have bounced emails in the last 30 days'
      ]
    };
  },

  async getCampaignMessages(campaignId: string): Promise<CampaignMessage[]> {
    await delay(300);
    return mockMessages.filter(msg => msg.campaignId === campaignId);
  },

  async resendMessage(messageId: string): Promise<{ ok: boolean }> {
    await delay(400);
    const message = mockMessages.find(m => m.id === messageId);
    if (message) {
      message.status = MessageStatus.PENDING;
      message.attempts += 1;
      message.sentAt = undefined;
      message.deliveredAt = undefined;
      message.bouncedAt = undefined;
      message.failedAt = undefined;
    }
    return { ok: true };
  }
};