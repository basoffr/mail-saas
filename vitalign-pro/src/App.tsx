import { useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AppSidebar, MobileSidebar } from "@/components/layout/AppSidebar";
import { AppTopbar } from "@/components/layout/AppTopbar";
import Login from "./pages/Login";
import Leads from "./pages/leads/Leads";
import LeadImport from "./pages/leads/LeadImport";
import BulkImport from "./pages/import/BulkImport";
import Campaigns from "./pages/campaigns/Campaigns";
import CampaignNew from "./pages/campaigns/CampaignNewSimplified";
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
          <AuthProvider>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              
              {/* Protected routes with layout */}
              <Route path="/*" element={
                <ProtectedRoute>
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
                          
                          {/* Admin-only routes */}
                          <Route path="/leads" element={<ProtectedRoute requireAdmin><Leads /></ProtectedRoute>} />
                          <Route path="/leads/import" element={<ProtectedRoute requireAdmin><LeadImport /></ProtectedRoute>} />
                          <Route path="/import/bulk" element={<ProtectedRoute requireAdmin><BulkImport /></ProtectedRoute>} />
                          <Route path="/campaigns" element={<ProtectedRoute requireAdmin><Campaigns /></ProtectedRoute>} />
                          <Route path="/campaigns/new" element={<ProtectedRoute requireAdmin><CampaignNew /></ProtectedRoute>} />
                          <Route path="/campaigns/:id" element={<ProtectedRoute requireAdmin><CampaignDetail /></ProtectedRoute>} />
                          <Route path="/templates" element={<ProtectedRoute requireAdmin><Templates /></ProtectedRoute>} />
                          <Route path="/templates/:id" element={<ProtectedRoute requireAdmin><TemplateDetail /></ProtectedRoute>} />
                          <Route path="/reports" element={<ProtectedRoute requireAdmin><Reports /></ProtectedRoute>} />
                          <Route path="/reports/upload" element={<ProtectedRoute requireAdmin><ReportUpload /></ProtectedRoute>} />
                          <Route path="/reports/bulk" element={<ProtectedRoute requireAdmin><ReportBulk /></ProtectedRoute>} />
                          <Route path="/settings" element={<ProtectedRoute requireAdmin><Settings /></ProtectedRoute>} />
                          
                          {/* Viewer + Admin routes */}
                          <Route path="/stats" element={<Statistics />} />
                          <Route path="/inbox" element={<Inbox />} />
                          
                          {/* Catch-all */}
                          <Route path="*" element={<NotFound />} />
                        </Routes>
                      </main>
                    </div>
                  </div>
                </ProtectedRoute>
              } />
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
