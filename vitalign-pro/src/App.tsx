import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Leads from "./pages/leads/Leads";
import LeadImport from "./pages/leads/LeadImport";
import Campaigns from "./pages/campaigns/Campaigns";
import CampaignNew from "./pages/campaigns/CampaignNew";
import CampaignDetail from "./pages/campaigns/CampaignDetail";
import Templates from "./pages/templates/Templates";
import TemplateDetail from "./pages/templates/TemplateDetail";
import Reports from "./pages/reports/Reports";
import ReportUpload from "./pages/reports/ReportUpload";
import ReportBulk from "./pages/reports/ReportBulk";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route path="/" element={<Navigate to="/leads" replace />} />
          <Route path="/leads" element={<Leads />} />
          <Route path="/leads/import" element={<LeadImport />} />
          <Route path="/campaigns" element={<Campaigns />} />
          <Route path="/campaigns/new" element={<CampaignNew />} />
          <Route path="/campaigns/:id" element={<CampaignDetail />} />
          <Route path="/templates" element={<Templates />} />
          <Route path="/templates/:id" element={<TemplateDetail />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/reports/upload" element={<ReportUpload />} />
          <Route path="/reports/bulk" element={<ReportBulk />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
