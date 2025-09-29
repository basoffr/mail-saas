import { useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppSidebar, MobileSidebar } from "@/components/layout/AppSidebar";
import { AppTopbar } from "@/components/layout/AppTopbar";
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
import Statistics from "./pages/Statistics";
import Settings from "./pages/Settings";
import Inbox from "./pages/Inbox";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <div className="flex h-screen bg-background">
            {/* Desktop Sidebar */}
            <AppSidebar />
            
            {/* Mobile Sidebar */}
            <MobileSidebar 
              open={mobileSidebarOpen} 
              onOpenChange={setMobileSidebarOpen}
            />

            {/* Main Content */}
            <div className="flex-1 flex flex-col overflow-hidden">
              <AppTopbar onOpenSidebar={() => setMobileSidebarOpen(true)} />
              
              <main className="flex-1 overflow-auto">
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
                  <Route path="/stats" element={<Statistics />} />
                  <Route path="/inbox" element={<Inbox />} />
                  <Route path="/settings" element={<Settings />} />
                  {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </main>
            </div>
          </div>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
