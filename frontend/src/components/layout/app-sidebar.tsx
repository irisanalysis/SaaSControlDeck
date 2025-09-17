"use client";

import * as React from "react";
import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Copy,
  Sparkles,
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
  SidebarSeparator,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import {
  defaultSidebarConfig,
  type SidebarAiShortcut,
  type SidebarConfig,
  type SidebarMetric,
} from "@/components/layout/sidebar-config";
import { cn } from "@/lib/utils";

const trendStyles = {
  up: {
    icon: ArrowUpRight,
    className: "text-emerald-500",
    bg: "bg-emerald-500/10",
  },
  down: {
    icon: ArrowDownRight,
    className: "text-rose-500",
    bg: "bg-rose-500/10",
  },
  steady: {
    icon: ArrowRight,
    className: "text-blue-500",
    bg: "bg-blue-500/10",
  },
} as const;

function MetricsPulse({ metrics }: { metrics: SidebarMetric[] }) {
  return (
    <div className="mt-4 space-y-3 rounded-2xl border border-orange-200/40 bg-white/70 p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.6)] backdrop-blur-md dark:bg-white/5 group-data-[collapsible=icon]:hidden">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.28em] text-sidebar-foreground/60">
          <span className="flex size-6 items-center justify-center rounded-full bg-orange-500/10 text-orange-600">
            <Sparkles className="size-3.5" />
          </span>
          Pulse
        </div>
        <span className="text-[10px] font-medium text-sidebar-foreground/50">
          Synced just now
        </span>
      </div>
      <div className="grid grid-cols-1 gap-3">
        {metrics.map((metric) => {
          const trend = trendStyles[metric.trend];
          const TrendIcon = trend.icon;
          return (
            <div
              key={metric.label}
              className="group/metric relative flex items-center justify-between rounded-xl border border-transparent bg-gradient-to-r from-orange-500/5 via-pink-500/5 to-orange-500/10 px-3 py-2 shadow-sm transition-all hover:border-orange-200/60 hover:shadow-lg"
            >
              <div>
                <div className="text-xs font-medium text-sidebar-foreground/60">
                  {metric.label}
                </div>
                <div className="mt-0.5 text-lg font-semibold tracking-tight text-sidebar-foreground">
                  {metric.value}
                </div>
              </div>
              <div className={cn("flex items-center gap-1 rounded-full px-2 py-1 text-[11px] font-semibold", trend.bg, trend.className)}>
                <TrendIcon className="size-3.5" />
                {metric.delta}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function AiQuickLaunch({ shortcuts, onSelect }: { shortcuts: SidebarAiShortcut[]; onSelect: (shortcut: SidebarAiShortcut) => void }) {
  return (
    <div className="mt-4 space-y-2 rounded-2xl border border-purple-200/50 bg-gradient-to-br from-purple-500/5 via-pink-500/5 to-orange-500/5 p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.4)] group-data-[collapsible=icon]:hidden">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.28em] text-purple-600">
          <Sparkles className="size-3.5" />
          AI Shortcuts
        </div>
        <span className="text-[10px] font-medium text-purple-600/70">
          Clipboard ready
        </span>
      </div>
      <div className="space-y-2">
        {shortcuts.map((shortcut) => (
          <button
            type="button"
            key={shortcut.label}
            onClick={() => onSelect(shortcut)}
            className="group/shortcut flex w-full items-start gap-3 rounded-xl border border-transparent bg-white/60 px-3 py-2 text-left text-sm shadow-sm transition-all duration-200 hover:border-purple-300/80 hover:bg-white hover:shadow-lg dark:bg-white/10"
          >
            <span className="mt-1 flex size-7 shrink-0 items-center justify-center rounded-lg bg-purple-500/15 text-purple-600">
              <Copy className="size-3" />
            </span>
            <span className="min-w-0">
              <span className="flex items-center gap-2 font-semibold text-sidebar-foreground">
                <span className="truncate" title={shortcut.label}>
                  {shortcut.label}
                </span>
              </span>
              <span className="mt-1 line-clamp-2 text-xs text-sidebar-foreground/60">
                {shortcut.description}
              </span>
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof SidebarContent>) {
  const { toast } = useToast();
  const [config] = React.useState<SidebarConfig>(defaultSidebarConfig);

  const handleShortcut = React.useCallback(
    async (shortcut: SidebarAiShortcut) => {
      try {
        if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
          await navigator.clipboard.writeText(shortcut.prompt);
          toast({
            title: "Prompt copied",
            description: `AI shortcut “${shortcut.label}” copied to clipboard.`,
            variant: "success",
          });
        }
      } catch (error) {
        console.error("Failed to copy prompt", error);
        toast({
          title: "Clipboard unavailable",
          description: "Try copying manually or check browser permissions.",
          variant: "destructive",
        });
      }
    },
    [toast]
  );

  const handleLaunchCopilot = React.useCallback(() => {
    if (typeof window === "undefined") {
      return;
    }

    const target = document.querySelector("#ai-help");
    if (target instanceof HTMLElement) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      window.location.hash = "ai-help";
    }
  }, []);

  return (
    <>
      <SidebarHeader>
        <TeamSwitcher teams={config.teams} />
      </SidebarHeader>
      <SidebarContent className="pb-16">
        <NavMain items={config.primaryNav} />
        <MetricsPulse metrics={config.metrics} />
        <AiQuickLaunch shortcuts={config.aiShortcuts} onSelect={handleShortcut} />
        <SidebarSeparator className="mt-4 group-data-[collapsible=icon]:hidden" />
        <NavProjects projects={config.workspaces} />
      </SidebarContent>
      <SidebarFooter className="space-y-3">
        <Button
          variant="magic"
          className="w-full justify-center gap-2 rounded-2xl py-5 text-sm group-data-[collapsible=icon]:hidden"
          onClick={handleLaunchCopilot}
        >
          <Sparkles className="size-4" />
          Launch AI Copilot
        </Button>
        <NavUser user={config.user} />
      </SidebarFooter>
      <SidebarRail />
    </>
  );
}
