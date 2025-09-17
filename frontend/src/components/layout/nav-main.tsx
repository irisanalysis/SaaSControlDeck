"use client";

import { useMemo } from "react";
import { usePathname } from "next/navigation";
import { ChevronRight, Sparkles } from "lucide-react";

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";
import type { SidebarNavItem } from "@/components/layout/sidebar-config";

const toneToBadge = {
  neutral: "bg-slate-100 text-slate-700 border border-slate-200/60 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700/60",
  success: "bg-emerald-100 text-emerald-700 border border-emerald-200/60 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-700/60",
  warning: "bg-amber-100 text-amber-700 border border-amber-200/60 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-700/60",
  destructive: "bg-rose-100 text-rose-700 border border-rose-200/60 dark:bg-rose-900/30 dark:text-rose-300 dark:border-rose-700/60",
} as const;

const iconRing = {
  base: "relative flex size-10 shrink-0 items-center justify-center rounded-xl transition-all duration-300 ease-out",
  default: "bg-gradient-to-br from-slate-100 via-white to-slate-50 text-slate-600 shadow-sm border border-slate-200/50 dark:from-slate-800 dark:via-slate-800 dark:to-slate-900 dark:text-slate-400 dark:border-slate-700/50",
  hover: "group-hover/navbutton:bg-gradient-to-br group-hover/navbutton:from-orange-100 group-hover/navbutton:via-orange-50 group-hover/navbutton:to-pink-50 group-hover/navbutton:text-orange-600 group-hover/navbutton:shadow-md group-hover/navbutton:border-orange-200/60 group-hover/navbutton:scale-105",
  active: "group-data-[active=true]/navbutton:bg-gradient-to-br group-data-[active=true]/navbutton:from-orange-500/20 group-data-[active=true]/navbutton:via-orange-400/15 group-data-[active=true]/navbutton:to-pink-400/15 group-data-[active=true]/navbutton:text-orange-700 group-data-[active=true]/navbutton:shadow-lg group-data-[active=true]/navbutton:border-orange-300/70 group-data-[active=true]/navbutton:scale-105",
  darkHover: "dark:group-hover/navbutton:bg-gradient-to-br dark:group-hover/navbutton:from-orange-900/30 dark:group-hover/navbutton:via-orange-800/20 dark:group-hover/navbutton:to-pink-800/20 dark:group-hover/navbutton:text-orange-400 dark:group-hover/navbutton:border-orange-700/60",
  darkActive: "dark:group-data-[active=true]/navbutton:bg-gradient-to-br dark:group-data-[active=true]/navbutton:from-orange-900/40 dark:group-data-[active=true]/navbutton:via-orange-800/30 dark:group-data-[active=true]/navbutton:to-pink-800/25 dark:group-data-[active=true]/navbutton:text-orange-300 dark:group-data-[active=true]/navbutton:border-orange-600/70"
};

const menuButtonStyles = {
  base: "group/navbutton relative w-full rounded-2xl border transition-all duration-300 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500/50 focus-visible:ring-offset-2",
  default: "border-transparent bg-transparent hover:bg-white/60 hover:border-slate-200/60 hover:shadow-sm dark:hover:bg-slate-800/60 dark:hover:border-slate-700/60",
  active: "bg-gradient-to-r from-orange-500/8 via-pink-500/6 to-orange-500/4 border-orange-200/60 shadow-sm dark:from-orange-900/20 dark:via-pink-900/15 dark:to-orange-900/10 dark:border-orange-700/50",
  padding: "px-3 py-3 group-data-[collapsible=icon]:p-2.5",
  layout: "flex items-center gap-3 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:gap-0"
};

function routeMatches(pathname: string, href?: string) {
  if (!href || href === "#") return false;
  if (href === "/") {
    return pathname === "/";
  }
  return pathname.startsWith(href);
}

export function NavMain({ items }: { items: SidebarNavItem[] }) {
  const pathname = usePathname();

  const computedItems = useMemo(() => {
    return items.map((item) => {
      const isActive = routeMatches(pathname, item.href);
      const activeChild = item.items?.find((sub) => routeMatches(pathname, sub.href));
      return {
        ...item,
        isActive,
        hasActiveChild: Boolean(activeChild),
      };
    });
  }, [items, pathname]);

  return (
    <SidebarGroup>
      <SidebarGroupLabel className="flex items-center justify-between text-xs uppercase tracking-[0.22em] group-data-[collapsible=icon]:hidden">
        <span>Workspace</span>
        <span className="rounded-full bg-sidebar-accent/40 px-2 py-0.5 text-[10px] font-semibold text-sidebar-accent-foreground">
          Live
        </span>
      </SidebarGroupLabel>
      <SidebarMenu>
        {computedItems.map((item) => {
          const hasChildren = Boolean(item.items?.length);
          const isExpanded = item.isActive || (hasChildren && item.hasActiveChild);

          const buttonInner = (
            <div className="relative flex w-full items-center gap-3 overflow-hidden group-data-[collapsible=icon]:justify-center">
              <span className={cn(
                iconRing.base,
                iconRing.default,
                iconRing.hover,
                iconRing.active,
                iconRing.darkHover,
                iconRing.darkActive,
                "group-data-[collapsible=icon]:size-11"
              )}>
                {item.icon && <item.icon className="size-4" />}
              </span>
              <div className="min-w-0 flex-1 group-data-[collapsible=icon]:hidden">
                <div className="flex items-center gap-2.5">
                  <span className="truncate text-sm font-semibold text-slate-700 group-hover/navbutton:text-slate-800 group-data-[active=true]/navbutton:text-orange-700 dark:text-slate-300 dark:group-hover/navbutton:text-slate-200 dark:group-data-[active=true]/navbutton:text-orange-300" title={item.title}>
                    {item.title}
                  </span>
                  {item.badge && (
                    <span
                      className={cn(
                        "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
                        toneToBadge[item.badgeTone ?? "neutral"]
                      )}
                    >
                      {item.badge}
                    </span>
                  )}
                  {item.aiHint && <Sparkles className="size-4 text-purple-500" />}
                </div>
              </div>
              {hasChildren && (
                <ChevronRight className="size-4 text-slate-400 transition-all duration-200 group-hover/navbutton:text-slate-600 group-data-[active=true]/navbutton:text-orange-600 group-data-[state=open]/collapsible:rotate-90 group-data-[collapsible=icon]:hidden dark:text-slate-500 dark:group-hover/navbutton:text-slate-300 dark:group-data-[active=true]/navbutton:text-orange-400" />
              )}
            </div>
          );

          if (hasChildren) {
            return (
              <Collapsible
                key={item.title}
                asChild
                defaultOpen={isExpanded}
                className="group/collapsible"
              >
                <SidebarMenuItem>
                  <CollapsibleTrigger asChild>
                    <SidebarMenuButton
                      data-active={item.isActive || item.hasActiveChild}
                      className={cn(
                        menuButtonStyles.base,
                        menuButtonStyles.default,
                        menuButtonStyles.padding,
                        menuButtonStyles.layout,
                        (item.isActive || item.hasActiveChild) && menuButtonStyles.active
                      )}
                    >
                      {buttonInner}
                    </SidebarMenuButton>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <SidebarMenuSub className="mt-3 border-l-0 pl-4 group-data-[collapsible=icon]:hidden">
                      {item.items?.map((subItem) => {
                        const isSubActive = routeMatches(pathname, subItem.href);
                        return (
                          <SidebarMenuSubItem key={subItem.title}>
                            <SidebarMenuSubButton
                              href={subItem.href}
                              size="sm"
                              isActive={isSubActive}
                              className={cn(
                                "group/navsub relative flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 hover:bg-slate-100 hover:text-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500/50 focus-visible:ring-offset-1 dark:hover:bg-slate-800 dark:hover:text-slate-200",
                                isSubActive &&
                                  "bg-orange-500/12 text-orange-700 shadow-sm border border-orange-200/40 dark:bg-orange-900/25 dark:text-orange-300 dark:border-orange-700/40"
                              )}
                            >
                              <span className="relative">
                                {isSubActive && (
                                  <span className="absolute -left-2 top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-full bg-orange-500 dark:bg-orange-400" />
                                )}
                                {subItem.title}
                              </span>
                              {subItem.badge && (
                                <span className={cn(
                                  "ml-auto inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
                                  toneToBadge[subItem.badgeTone ?? "neutral"]
                                )}>
                                  {subItem.badge}
                                </span>
                              )}
                            </SidebarMenuSubButton>
                          </SidebarMenuSubItem>
                        );
                      })}
                    </SidebarMenuSub>
                  </CollapsibleContent>
                </SidebarMenuItem>
              </Collapsible>
            );
          }

          return (
            <SidebarMenuItem key={item.title}>
              <SidebarMenuButton
                asChild
                data-active={item.isActive}
                className={cn(
                  menuButtonStyles.base,
                  menuButtonStyles.default,
                  menuButtonStyles.padding,
                  "flex items-center",
                  item.isActive && menuButtonStyles.active
                )}
              >
                <a href={item.href} aria-current={item.isActive ? "page" : undefined}>
                  {buttonInner}
                </a>
              </SidebarMenuButton>
            </SidebarMenuItem>
          );
        })}
      </SidebarMenu>
    </SidebarGroup>
  );
}
