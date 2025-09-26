import { Template, TemplatePreviewResponse, TestsendPayload, TemplatesResponse, TemplateVarItem } from '@/types/template';

const mockTemplates: Template[] = [
  {
    id: '1',
    name: 'Welcome Email',
    subject: 'Welcome to {{companyName}}!',
    bodyHtml: `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h1 style="color: #2563eb;">Hi {{firstName}},</h1>
        <p>Welcome to {{companyName}}! We're excited to have you on board.</p>
        <img src="{{image.cid 'hero'}}" alt="Welcome" style="width: 100%; max-width: 400px;" />
        <p>Here's what you can expect from us:</p>
        <ul>
          <li>Personalized support</li>
          <li>Regular updates</li>
          <li>Access to premium features</li>
        </ul>
        <p>Best regards,<br>The {{companyName}} Team</p>
      </div>
    `,
    updatedAt: '2024-01-15T10:30:00Z',
    assets: [
      { key: 'hero', type: 'cid' },
      { key: 'logo', type: 'static' }
    ]
  },
  {
    id: '2',
    name: 'Follow-up Sequence',
    subject: 'Following up on our conversation',
    bodyHtml: `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h1 style="color: #2563eb;">Hi {{firstName}},</h1>
        <p>I hope this email finds you well. I noticed that {{companyName}} is doing great work in the {{industry}} space.</p>
        <p>I'd love to show you how our solution can help {{companyName}} achieve even better results.</p>
        <p>Best regards,<br>Your Sales Team</p>
      </div>
    `,
    updatedAt: '2024-01-14T09:15:00Z'
  },
  {
    id: '3',
    name: 'Product Demo Invitation',
    subject: 'Exclusive demo for {{companyName}}',
    bodyHtml: `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h1 style="color: #2563eb;">Hi {{firstName}},</h1>
        <p>We'd love to show you a personalized demo of our platform.</p>
        <p>As a {{industry}} company, {{companyName}} could benefit from our specialized features.</p>
        <p>Would you be available for a 15-minute call this week?</p>
        <p>Best regards,<br>Your Sales Team</p>
      </div>
    `,
    updatedAt: '2024-01-13T14:45:00Z'
  },
  {
    id: '4',
    name: 'Case Study Share',
    subject: 'How {{industry}} companies like yours succeed',
    bodyHtml: `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h1 style="color: #2563eb;">Hi {{firstName}},</h1>
        <p>I thought you might be interested in this case study from another {{industry}} company.</p>
        <img src="{{image.cid 'case-study'}}" alt="Case Study" style="width: 100%; max-width: 400px;" />
        <p>They achieved similar results to what {{companyName}} is looking for.</p>
        <p>Would you like to discuss how this could apply to your situation?</p>
        <p>Best regards,<br>Your Sales Team</p>
      </div>
    `,
    updatedAt: '2024-01-12T11:20:00Z',
    assets: [
      { key: 'case-study', type: 'cid' }
    ]
  },
  {
    id: '5',
    name: 'Newsletter Sign-up',
    subject: 'Stay updated with {{companyName}}',
    bodyHtml: `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h1 style="color: #2563eb;">Hi there!</h1>
        <p>Thank you for your interest in our {{industry}} insights newsletter.</p>
        <p>You'll receive weekly updates with the latest trends and best practices.</p>
        <p>Welcome aboard!</p>
        <p>Best regards,<br>The Content Team</p>
      </div>
    `,
    updatedAt: '2024-01-11T16:00:00Z'
  }
];

const mockVariables: TemplateVarItem[] = [
  { key: 'firstName', required: true, source: 'lead', example: 'John' },
  { key: 'lastName', required: false, source: 'lead', example: 'Doe' },
  { key: 'companyName', required: true, source: 'lead', example: 'Acme Corp' },
  { key: 'industry', required: false, source: 'vars', example: 'Technology' },
  { key: 'image.cid', required: false, source: 'image', example: 'hero, case-study' }
];

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const templatesService = {
  async getTemplates(): Promise<TemplatesResponse> {
    await delay(200);
    return { items: mockTemplates, total: mockTemplates.length };
  },

  async getTemplate(id: string): Promise<Template> {
    await delay(200);
    const template = mockTemplates.find(t => t.id === id);
    if (!template) {
      throw new Error('Template not found');
    }
    return template;
  },

  async getTemplatePreview(templateId: string, leadId?: string): Promise<TemplatePreviewResponse> {
    await delay(300);
    
    const template = mockTemplates.find(t => t.id === templateId);
    if (!template) {
      throw new Error('Template not found');
    }

    let warnings: string[] = [];
    
    // Mock warnings based on missing variables
    if (!leadId || leadId === '5') {
      warnings.push('Missing firstName variable for this lead');
    }
    
    if (template.assets?.some(asset => asset.type === 'cid')) {
      warnings.push('Some CID images may not be available for this lead');
    }

    // Replace variables with mock data
    let html = template.bodyHtml;
    let text = template.bodyHtml.replace(/<[^>]*>/g, '').replace(/\n\s+/g, '\n').trim();
    
    if (leadId && leadId !== '5') {
      html = html
        .replace(/\{\{firstName\}\}/g, 'John')
        .replace(/\{\{lastName\}\}/g, 'Doe')
        .replace(/\{\{companyName\}\}/g, 'Acme Corp')
        .replace(/\{\{industry\}\}/g, 'Technology')
        .replace(/\{\{image\.cid\s+'[^']+'\}\}/g, 'https://via.placeholder.com/400x200');
      
      text = text
        .replace(/\{\{firstName\}\}/g, 'John')
        .replace(/\{\{lastName\}\}/g, 'Doe')
        .replace(/\{\{companyName\}\}/g, 'Acme Corp')
        .replace(/\{\{industry\}\}/g, 'Technology')
        .replace(/\{\{image\.cid\s+'[^']+'\}\}/g, '[Image: Placeholder]');
    } else {
      // Show placeholder for missing variables
      html = html.replace(/\{\{image\.cid\s+'[^']+'\}\}/g, 'https://via.placeholder.com/400x200?text=Missing+Image');
    }

    return {
      html,
      text,
      warnings: warnings.length > 0 ? warnings : undefined
    };
  },

  async getTemplateVariables(templateId: string): Promise<TemplateVarItem[]> {
    await delay(200);
    return mockVariables;
  },

  async sendTest(templateId: string, payload: TestsendPayload): Promise<{ ok: boolean }> {
    await delay(500);
    
    // Validate email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(payload.to)) {
      throw new Error('Invalid email address');
    }
    
    return { ok: true };
  }
};