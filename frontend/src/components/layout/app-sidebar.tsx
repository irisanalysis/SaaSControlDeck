"use client";

import * as React from "react";
import {
  AudioWaveform,
  BookOpen,
  Bot,
  Command,
  Frame,
  GalleryVerticalEnd,
  Map,
  PieChart,
  Settings2,
  SquareTerminal,
  LayoutDashboard,
  FileText,
  BarChart2,
  Briefcase,
  Users,
  Shield,
  CreditCard,
  Bell,
  Zap,
  Database,
  Globe,
  Activity,
} from "lucide-react";

import { NavMain } from "@/components/layout/nav-main";
import { NavProjects } from "@/components/layout/nav-projects";
import { NavUser } from "@/components/layout/nav-user";
import { TeamSwitcher } from "@/components/layout/team-switcher";
import {
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar";

// This is sample data for demonstration
const data = {
  user: {
    name: "Sarah Johnson",
    email: "sarah@acme.com",
    avatar: "/avatars/sarah.jpg",
  },
  teams: [
    {
      name: "Acme Inc",
      logo: GalleryVerticalEnd,
      plan: "Enterprise",
    },
    {
      name: "Acme Corp.",
      logo: AudioWaveform,
      plan: "Startup",
    },
    {
      name: "Evil Corp.",
      logo: Command,
      plan: "Free",
    },
  ],
  navMain: [
    {
      title: "Dashboard",
      url: "/",
      icon: LayoutDashboard,
      isActive: true,
      badge: "3",
    },
    {
      title: "Documents",
      url: "#",
      icon: FileText,
      badge: "12",
      items: [
        {
          title: "All Documents",
          url: "#",
          badge: "45",
        },
        {
          title: "Templates",
          url: "#",
          badge: "8",
        },
        {
          title: "Shared with me",
          url: "#",
          badge: "7",
        },
        {
          title: "Recent",
          url: "#",
        },
        {
          title: "Archived",
          url: "#",
          badge: "2",
        },
      ],
    },
    {
      title: "Analytics",
      url: "#",
      icon: BarChart2,
      items: [
        {
          title: "Overview",
          url: "#",
        },
        {
          title: "Traffic",
          url: "#",
        },
        {
          title: "User Behavior",
          url: "#",
        },
        {
          title: "Conversion Rates",
          url: "#",
        },
        {
          title: "Reports",
          url: "#",
          badge: "5",
        },
      ],
    },
    {
      title: "Team",
      url: "#",
      icon: Users,
      badge: "15",
      items: [
        {
          title: "Members",
          url: "#",
          badge: "15",
        },
        {
          title: "Roles & Permissions",
          url: "#",
        },
        {
          title: "Invitations",
          url: "#",
          badge: "3",
        },
        {
          title: "Activity Log",
          url: "#",
        },
      ],
    },
    {
      title: "Accounting",
      url: "#",
      icon: Briefcase,
      items: [
        {
          title: "Invoices",
          url: "#",
          badge: "8",
        },
        {
          title: "Billing",
          url: "#",
        },
        {
          title: "Subscriptions",
          url: "#",
          badge: "2",
        },
        {
          title: "Payment Methods",
          url: "#",
        },
        {
          title: "Transaction History",
          url: "#",
        },
      ],
    },
  ],
  projects: [
    {
      name: "Integrations",
      url: "#",
      icon: Zap,
      badge: "Syncing",
      badgeVariant: "outline" as const,
    },
    {
      name: "Security",
      url: "#",
      icon: Shield,
      badge: "Active",
      badgeVariant: "default" as const,
    },
    {
      name: "Database",
      url: "#",
      icon: Database,
    },
    {
      name: "API Gateway",
      url: "#",
      icon: Globe,
      badge: "2",
      badgeVariant: "secondary" as const,
    },
    {
      name: "Monitoring",
      url: "#",
      icon: Activity,
      badge: "Warning",
      badgeVariant: "destructive" as const,
    },
  ],
};

export function AppSidebar({ ...props }: React.ComponentProps<typeof SidebarContent>) {
  return (
    <>
      <SidebarHeader>
        <TeamSwitcher teams={data.teams} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
        <NavProjects projects={data.projects} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
      <SidebarRail />
    </>
  );
}