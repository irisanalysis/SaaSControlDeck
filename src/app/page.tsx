import { Sidebar, SidebarContent, SidebarHeader, SidebarInset } from '@/components/ui/sidebar';
import Header from '@/components/layout/header';
import SidebarNav from '@/components/layout/sidebar-nav';
import ProfileCard from '@/components/dashboard/profile-card';
import SettingsCard from '@/components/dashboard/settings-card';
import IntegrationsCard from '@/components/dashboard/integrations-card';
import DeviceManagementCard from '@/components/dashboard/device-management-card';
import PendingApprovalsCard from '@/components/dashboard/pending-approvals-card';
import AiHelp from '@/components/ai/ai-help';

export default function Home() {
  return (
    <>
      <Sidebar>
        <SidebarHeader>
          <div className="flex items-center gap-2 p-2">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-6 w-6 text-primary"
            >
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
            </svg>
            <h1 className="text-lg font-semibold">SaaS Deck</h1>
          </div>
        </SidebarHeader>
        <SidebarContent className="p-0">
          <SidebarNav />
        </SidebarContent>
      </Sidebar>
      <SidebarInset>
        <Header />
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          <div className="mx-auto grid max-w-7xl auto-rows-max grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <ProfileCard />
            </div>
            <div className="lg:col-span-1">
              <PendingApprovalsCard />
            </div>
            <div className="lg:col-span-3">
              <SettingsCard />
            </div>
            <div className="lg:col-span-2">
              <IntegrationsCard />
            </div>
            <div className="lg:col-span-1">
              <DeviceManagementCard />
            </div>
          </div>
        </main>
      </SidebarInset>
      <AiHelp />
    </>
  );
}
