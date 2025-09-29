import { Template, TemplatePreviewResponse, TestsendPayload, TemplatesResponse, TemplateVarItem } from '@/types/template';
import { authService, buildQueryString } from './auth';

export const templatesService = {
  async getTemplates(): Promise<TemplatesResponse> {
    try {
      console.log('Calling templates API:', `${authService.getConfig().baseUrl}/templates`);
      return await authService.apiCall<TemplatesResponse>('/templates');
    } catch (error) {
      console.warn('Templates API call failed, using fallback:', error);
      console.log('API Base URL:', authService.getConfig().baseUrl);
      
      // Fallback voor development als backend niet draait
      return {
        items: [],
        total: 0
      };
    }
  },

  async getTemplate(id: string): Promise<Template> {
    return await authService.apiCall<Template>(`/templates/${id}`);
  },

  async getTemplatePreview(templateId: string, leadId?: string): Promise<TemplatePreviewResponse> {
    const queryString = buildQueryString({ lead_id: leadId });
    const endpoint = `/templates/${templateId}/preview${queryString ? `?${queryString}` : ''}`;
    return await authService.apiCall<TemplatePreviewResponse>(endpoint);
  },

  async getTemplateVariables(templateId: string): Promise<TemplateVarItem[]> {
    return await authService.apiCall<TemplateVarItem[]>(`/templates/${templateId}/variables`);
  },

  async sendTest(templateId: string, payload: TestsendPayload): Promise<{ ok: boolean }> {
    return await authService.apiCall<{ ok: boolean }>(`/templates/${templateId}/testsend`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }
};