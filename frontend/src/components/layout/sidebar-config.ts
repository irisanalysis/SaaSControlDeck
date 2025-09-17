import {
  Activity,
  AudioWaveform,
  BarChart2,
  Bell,
  BookOpen,
  Bot,
  Briefcase,
  Command,
  CreditCard,
  Database,
  FileText,
  Frame,
  GalleryVerticalEnd,
  Globe,
  LayoutDashboard,
  Map,
  PieChart,
  Settings2,
  Shield,
  Sparkles,
  SquareTerminal,
  Users,
  Zap,
} from "lucide-react";

export type SidebarNavItem = {
  title: string;
  href: string;
  icon?: React.ComponentType<{ className?: string }>;
  badge?: string;
  badgeTone?: "neutral" | "success" | "warning" | "destructive";
  description?: string;
  aiHint?: string;
  items?: Array<{
    title: string;
    href: string;
    badge?: string;
    badgeTone?: SidebarNavItem["badgeTone"];
  }>;
};

export type SidebarTeam = {
  name: string;
  plan: string;
  logo: React.ComponentType<{ className?: string }>;
};

export type SidebarProject = {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  badgeVariant?: "default" | "secondary" | "destructive" | "outline";
};

export type SidebarMetric = {
  label: string;
  value: string;
  trend: "up" | "down" | "steady";
  delta: string;
};

export type SidebarAiShortcut = {
  label: string;
  description: string;
  prompt: string;
};

export type SidebarConfig = {
  user: {
    name: string;
    email: string;
    avatar: string;
  };
  teams: SidebarTeam[];
  primaryNav: SidebarNavItem[];
  workspaces: SidebarProject[];
  metrics: SidebarMetric[];
  aiShortcuts: SidebarAiShortcut[];
};

export const defaultSidebarConfig: SidebarConfig = {
  user: {
    name: "Sarah Johnson",
    email: "sarah@acme.com",
    avatar: "/avatars/sarah.jpg",
  },
  teams: [
    {
      name: "Acme Inc",
      plan: "Enterprise",
      logo: GalleryVerticalEnd,
    },
    {
      name: "Acme Corp.",
      plan: "Startup",
      logo: AudioWaveform,
    },
    {
      name: "Evil Corp.",
      plan: "Free",
      logo: Command,
    },
  ],
  primaryNav: [
    {
      title: "Dashboard",
      href: "/",
      icon: LayoutDashboard,
      badge: "Live",
      badgeTone: "success",
      description: "Realtime status across your SaaS footprint.",
    },
    {
      title: "Analytics",
      href: "/analytics",
      icon: BarChart2,
      description: "Insights into product, finance, and operations.",
      items: [
        { title: "Overview", href: "/analytics" },
        { title: "Traffic", href: "/analytics/traffic" },
        { title: "User Journey", href: "/analytics/journey" },
        { title: "Conversion", href: "/analytics/conversion", badge: "AI" },
      ],
    },
    {
      title: "Automation",
      href: "/automation",
      icon: Bot,
      badge: "New",
      badgeTone: "neutral",
      description: "Workflow bots and approvals automation.",
      items: [
        { title: "Playbooks", href: "/automation" },
        { title: "Approvals", href: "/automation/approvals", badge: "6" },
        { title: "Broadcasts", href: "/automation/broadcasts" },
      ],
    },
    {
      title: "Security",
      href: "/security",
      icon: Shield,
      description: "Access control, policies, and compliance posture.",
      badge: "2",
      badgeTone: "warning",
      items: [
        { title: "Posture", href: "/security" },
        { title: "Policies", href: "/security/policies" },
        { title: "Audit Trail", href: "/security/audit" },
      ],
    },
    {
      title: "Billing",
      href: "/billing",
      icon: CreditCard,
      description: "Revenue, invoices, and upcoming renewals.",
    },
    {
      title: "Integrations",
      href: "/integrations",
      icon: Zap,
      description: "API gateway, webhooks, and partner ecosystem.",
      items: [
        { title: "Marketplace", href: "/integrations" },
        { title: "API Tokens", href: "/integrations/tokens", badge: "Rotate" },
        { title: "Webhooks", href: "/integrations/webhooks" },
      ],
    },
    {
      title: "Knowledge Base",
      href: "/knowledge",
      icon: BookOpen,
      description: "Guides, runbooks, and best practices.",
    },
    {
      title: "Settings",
      href: "/settings",
      icon: Settings2,
      description: "Global preferences and administrative tools.",
      items: [
        { title: "Workspace", href: "/settings" },
        { title: "Members", href: "/settings/members" },
        { title: "Connected Apps", href: "/settings/integrations" },
      ],
    },
  ],
  workspaces: [
    {
      name: "Realtime Ops",
      href: "/projects/ops",
      icon: Activity,
      badge: "Monitoring",
      badgeVariant: "outline",
    },
    {
      name: "Intelligence",
      href: "/projects/ai",
      icon: Sparkles,
      badge: "Syncing",
      badgeVariant: "secondary",
    },
    {
      name: "Finance",
      href: "/projects/finance",
      icon: Briefcase,
      badge: "Active",
      badgeVariant: "default",
    },
    {
      name: "Data Mesh",
      href: "/projects/data",
      icon: Database,
    },
    {
      name: "Field Ops",
      href: "/projects/field",
      icon: Map,
      badge: "Beta",
      badgeVariant: "destructive",
    },
  ],
  metrics: [
    { label: "Active Users", value: "12.4k", trend: "up", delta: "+8.1%" },
    { label: "Automation Runs", value: "318", trend: "steady", delta: "+0.4%" },
    { label: "Incidents", value: "0", trend: "down", delta: "-2" },
  ],
  aiShortcuts: [
    {
      label: "Ask AI for health summary",
      description: "Generate a realtime status digest for leadership.",
      prompt: "Summarize platform uptime, error budget, and any anomalies in the last 24h.",
    },
    {
      label: "Compliance assistant",
      description: "Identify policies that require review this week.",
      prompt: "List outstanding compliance documents and owners due within 7 days.",
    },
    {
      label: "Growth insights",
      description: "Forecast this month’s churn risk and revenue opportunities.",
      prompt: "Analyze billing data for churn risk and upsell prospects with supporting metrics.",
    },
  ],
};
