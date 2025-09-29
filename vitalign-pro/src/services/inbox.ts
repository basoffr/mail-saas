import { 
  InboxMessageOut, 
  InboxListResponse, 
  FetchStartResponse, 
  MarkReadResponse,
  MailAccountOut,
  InboxRunOut,
  InboxQuery 
} from '@/types/inbox';

// Mock data
const mockMessages: InboxMessageOut[] = [
  {
    id: 'msg-001',
    accountId: 'acc-001',
    accountLabel: 'info@domain1.com',
    folder: 'INBOX',
    uid: 1001,
    messageId: '<reply-001@gmail.com>',
    inReplyTo: '<campaign-msg-001@domain1.com>',
    references: ['<campaign-msg-001@domain1.com>'],
    fromEmail: 'john.doe@gmail.com',
    fromName: 'John Doe',
    toEmail: 'info@domain1.com',
    subject: 'Re: Welkom bij onze service!',
    snippet: 'Bedankt voor jullie bericht. Ik ben geïnteresseerd in meer informatie over jullie diensten. Kunnen we een afspraak inplannen?',
    rawSize: 1024,
    receivedAt: '2025-09-26T14:30:00Z',
    isRead: false,
    linkedCampaignId: 'campaign-001',
    linkedCampaignName: 'Welcome Campaign',
    linkedLeadId: 'lead-001',
    linkedLeadEmail: 'john.doe@gmail.com',
    linkedMessageId: 'msg-out-001',
    weakLink: false,
    encodingIssue: false
  },
  {
    id: 'msg-002',
    accountId: 'acc-001',
    accountLabel: 'info@domain1.com',
    folder: 'INBOX',
    uid: 1002,
    messageId: '<reply-002@outlook.com>',
    fromEmail: 'sarah.smith@outlook.com',
    fromName: 'Sarah Smith',
    toEmail: 'info@domain1.com',
    subject: 'Vraag over prijzen',
    snippet: 'Hallo, ik heb jullie website bekeken en ben benieuwd naar de prijzen van jullie premium pakket.',
    rawSize: 512,
    receivedAt: '2025-09-26T13:15:00Z',
    isRead: true,
    linkedLeadId: 'lead-002',
    linkedLeadEmail: 'sarah.smith@outlook.com',
    weakLink: true,
    encodingIssue: false
  },
  {
    id: 'msg-003',
    accountId: 'acc-002',
    accountLabel: 'support@domain2.com',
    folder: 'INBOX',
    uid: 2001,
    messageId: '<reply-003@company.nl>',
    inReplyTo: '<campaign-msg-002@domain2.com>',
    references: ['<campaign-msg-002@domain2.com>'],
    fromEmail: 'info@company.nl',
    fromName: 'Bedrijf BV',
    toEmail: 'support@domain2.com',
    subject: 'Re: Nieuwe functionaliteiten beschikbaar',
    snippet: 'Interessant! We zouden graag een demo willen zien van de nieuwe functionaliteiten.',
    rawSize: 768,
    receivedAt: '2025-09-26T12:45:00Z',
    isRead: false,
    linkedCampaignId: 'campaign-002',
    linkedCampaignName: 'Feature Update Campaign',
    linkedLeadId: 'lead-003',
    linkedLeadEmail: 'info@company.nl',
    linkedMessageId: 'msg-out-002',
    weakLink: false,
    encodingIssue: false
  },
  {
    id: 'msg-004',
    accountId: 'acc-001',
    accountLabel: 'info@domain1.com',
    folder: 'INBOX',
    uid: 1003,
    messageId: '<reply-004@gmail.com>',
    fromEmail: 'test@example.com',
    fromName: null,
    toEmail: 'info@domain1.com',
    subject: 'Unsubscribe request',
    snippet: 'Please remove me from your mailing list.',
    rawSize: 256,
    receivedAt: '2025-09-26T11:20:00Z',
    isRead: true,
    linkedLeadId: 'lead-004',
    linkedLeadEmail: 'test@example.com',
    weakLink: true,
    encodingIssue: false
  }
];

const mockAccounts: MailAccountOut[] = [
  {
    id: 'acc-001',
    label: 'info@domain1.com',
    imapHost: 'imap.domain1.com',
    imapPort: 993,
    useSsl: true,
    usernameMasked: 'inf***@domain1.com',
    active: true,
    lastFetchAt: '2025-09-26T15:00:00Z',
    lastSeenUid: 1003
  },
  {
    id: 'acc-002',
    label: 'support@domain2.com',
    imapHost: 'imap.domain2.com',
    imapPort: 993,
    useSsl: true,
    usernameMasked: 'sup***@domain2.com',
    active: true,
    lastFetchAt: '2025-09-26T14:45:00Z',
    lastSeenUid: 2001
  }
];

const mockRuns: InboxRunOut[] = [
  {
    id: 'run-001',
    accountId: 'acc-001',
    startedAt: '2025-09-26T15:00:00Z',
    finishedAt: '2025-09-26T15:00:15Z',
    newCount: 2,
    error: null
  },
  {
    id: 'run-002',
    accountId: 'acc-002',
    startedAt: '2025-09-26T14:45:00Z',
    finishedAt: '2025-09-26T14:45:08Z',
    newCount: 1,
    error: null
  }
];

class InboxService {
  private lastFetchTime = 0;
  private readonly minFetchInterval = 2 * 60 * 1000; // 2 minutes

  async fetchMessages(): Promise<FetchStartResponse> {
    const now = Date.now();
    if (now - this.lastFetchTime < this.minFetchInterval) {
      throw new Error('Please wait before fetching again. Minimum interval is 2 minutes.');
    }

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    this.lastFetchTime = now;
    return {
      ok: true,
      run_id: `run-${Date.now()}`
    };
  }

  async getMessages(query: InboxQuery = {}): Promise<InboxListResponse> {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 300));

    let filteredMessages = [...mockMessages];

    // Apply filters
    if (query.accountId) {
      filteredMessages = filteredMessages.filter(msg => msg.accountId === query.accountId);
    }

    if (query.campaignId) {
      filteredMessages = filteredMessages.filter(msg => msg.linkedCampaignId === query.campaignId);
    }

    if (query.unread !== undefined) {
      filteredMessages = filteredMessages.filter(msg => !msg.isRead === query.unread);
    }

    if (query.q) {
      const searchTerm = query.q.toLowerCase();
      filteredMessages = filteredMessages.filter(msg => 
        msg.fromEmail.toLowerCase().includes(searchTerm) ||
        msg.fromName?.toLowerCase().includes(searchTerm) ||
        msg.subject.toLowerCase().includes(searchTerm)
      );
    }

    if (query.from) {
      filteredMessages = filteredMessages.filter(msg => 
        msg.receivedAt >= query.from!
      );
    }

    if (query.to) {
      filteredMessages = filteredMessages.filter(msg => 
        msg.receivedAt <= query.to!
      );
    }

    // Sort by receivedAt desc (default)
    filteredMessages.sort((a, b) => new Date(b.receivedAt).getTime() - new Date(a.receivedAt).getTime());

    // Pagination
    const page = query.page || 1;
    const pageSize = query.pageSize || 25;
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedMessages = filteredMessages.slice(startIndex, endIndex);

    return {
      items: paginatedMessages,
      total: filteredMessages.length
    };
  }

  async markAsRead(messageId: string): Promise<MarkReadResponse> {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 200));

    // Update mock data
    const message = mockMessages.find(msg => msg.id === messageId);
    if (message) {
      message.isRead = true;
    }

    return { ok: true };
  }

  async getAccounts(): Promise<{ items: MailAccountOut[] }> {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 200));

    return { items: mockAccounts };
  }

  async testAccount(accountId: string): Promise<{ ok: boolean; message: string }> {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));

    return {
      ok: true,
      message: 'Connection successful'
    };
  }

  async toggleAccount(accountId: string): Promise<{ ok: boolean }> {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 300));

    const account = mockAccounts.find(acc => acc.id === accountId);
    if (account) {
      account.active = !account.active;
    }

    return { ok: true };
  }

  async getRuns(query: { accountId?: string; page?: number; pageSize?: number } = {}): Promise<{ items: InboxRunOut[]; total: number }> {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 200));

    let filteredRuns = [...mockRuns];

    if (query.accountId) {
      filteredRuns = filteredRuns.filter(run => run.accountId === query.accountId);
    }

    // Sort by startedAt desc
    filteredRuns.sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime());

    // Pagination
    const page = query.page || 1;
    const pageSize = query.pageSize || 25;
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedRuns = filteredRuns.slice(startIndex, endIndex);

    return {
      items: paginatedRuns,
      total: filteredRuns.length
    };
  }
}

export const inboxService = new InboxService();
