import { Template, TemplatePreviewResponse, TestsendPayload, TemplatesResponse, TemplateVarItem } from '@/types/template';
import { authService, buildQueryString } from './auth';
import { 
  toUiTemplate, 
  toUiTemplatesList, 
  toUiTemplatePreview, 
  toUiTemplateVariables,
  UiTemplate 
} from './adapters/templatesAdapter';

export const templatesService = {
  async getTemplates(): Promise<TemplatesResponse> {
    try {
      console.log('Calling templates API:', `${authService.getConfig().baseUrl}/templates`);
      const response = await authService.apiCall<any>('/templates');
      const transformed = toUiTemplatesList(response);
      return transformed as TemplatesResponse;
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
    const response = await authService.apiCall<any>(`/templates/${id}`);
    return toUiTemplate(response) as Template;
  },

  async getTemplatePreview(templateId: string, leadId?: string): Promise<TemplatePreviewResponse> {
    const queryString = buildQueryString({ lead_id: leadId });
    const endpoint = `/templates/${templateId}/preview${queryString ? `?${queryString}` : ''}`;
    const response = await authService.apiCall<any>(endpoint);
    return toUiTemplatePreview(response);
  },

  async getTemplateVariables(templateId: string): Promise<TemplateVarItem[]> {
    const response = await authService.apiCall<any>(`/templates/${templateId}/variables`);
    return toUiTemplateVariables(response);
  },

  async sendTest(templateId: string, payload: TestsendPayload): Promise<{ ok: boolean }> {
    return await authService.apiCall<{ ok: boolean }>(`/templates/${templateId}/testsend`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }
};