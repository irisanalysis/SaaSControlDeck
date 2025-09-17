"use client";

import { MoreHorizontal } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { SidebarProject } from "@/components/layout/sidebar-config";

export function NavProjects({ projects }: { projects: SidebarProject[] }) {
  const { isMobile } = useSidebar();

  return (
    <SidebarGroup className="group-data-[collapsible=icon]:hidden">
      <SidebarGroupLabel className="flex items-center justify-between text-xs uppercase tracking-[0.22em]">
        <span>Focus Areas</span>
        <span className="text-[10px] font-semibold text-sidebar-foreground/60">
          Updated 3m ago
        </span>
      </SidebarGroupLabel>
      <SidebarMenu className="gap-1.5">
        {projects.map((project) => (
          <SidebarMenuItem key={project.name} className="relative">
            <SidebarMenuButton
              asChild
              className="group/navproject relative w-full rounded-2xl border border-transparent px-3 py-2 transition-all duration-300 hover:border-orange-200/60 hover:bg-white/60 hover:shadow-lg dark:hover:bg-white/10"
            >
              <a href={project.href}>
                <div className="flex items-center gap-3">
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-slate-900/5 via-orange-500/10 to-pink-500/10 text-orange-600 shadow-[inset_0_0_0_1px_rgba(251,146,60,0.2)] dark:text-orange-200">
                    <project.icon className="size-4" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center gap-2 text-sm font-medium text-sidebar-foreground">
                      <span className="truncate" title={project.name}>
                        {project.name}
                      </span>
                      {project.badge && (
                        <Badge
                          variant={project.badgeVariant ?? "secondary"}
                          className={cn(
                            "h-5 rounded-full px-2 text-[10px] font-semibold uppercase tracking-wide",
                            project.badgeVariant === "outline" &&
                              "border-orange-200 text-orange-500"
                          )}
                        >
                          {project.badge}
                        </Badge>
                      )}
                    </span>
                  </span>
                </div>
              </a>
            </SidebarMenuButton>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuAction showOnHover>
                  <MoreHorizontal />
                  <span className="sr-only">More options</span>
                </SidebarMenuAction>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className="w-48 rounded-lg"
                side={isMobile ? "bottom" : "right"}
                align={isMobile ? "end" : "start"}
              >
                <DropdownMenuItem>Open workspace</DropdownMenuItem>
                <DropdownMenuItem>Share snapshot</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-destructive">
                  Disable updates
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  );
}
