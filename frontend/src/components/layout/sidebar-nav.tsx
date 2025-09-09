"use client";

import {
    ChevronRight,
    LayoutDashboard,
    FileText,
    BarChart2,
    Briefcase,
  } from 'lucide-react'
  import { usePathname } from 'next/navigation'
  import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from '../ui/sidebar';
  import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../ui/collapsible';
  import { cn } from '@/lib/utils';
  
  export default function SidebarNav() {
    const pathname = usePathname();
  
    const isActive = (path: string) => {
      return pathname === path;
    }
  
    return (
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton href="/dashboard" active={isActive('/dashboard')}>
            <LayoutDashboard className="h-4 w-4" />
            Dashboard
          </SidebarMenuButton>
        </SidebarMenuItem>
        <SidebarMenuItem>
            <Collapsible>
                <CollapsibleTrigger asChild>
                    <SidebarMenuButton variant="ghost" className="w-full justify-start gap-2">
                        <FileText className="h-4 w-4" />
                        Documents
                        <ChevronRight className="ml-auto h-4 w-4 transition-transform duration-200 [&[data-state=open]]:rotate-90" />
                    </SidebarMenuButton>
                </CollapsibleTrigger>
                <CollapsibleContent>
                    <SidebarMenuButton href="#" variant="ghost" className="w-full justify-start gap-2 ml-6">
                        All Documents
                    </SidebarMenuButton>
                    <SidebarMenuButton href="#" variant="ghost" className="w-full justify-start gap-2 ml-6">
                        Templates
                    </SidebarMenuButton>
                    <SidebarMenuButton href="#" variant="ghost" className="w-full justify-start gap-2 ml-6">
                        Shared with me
                    </SidebarMenuButton>
                </CollapsibleContent>
            </Collapsible>
        </SidebarMenuItem>
        <SidebarMenuItem>
            <Collapsible>
                <CollapsibleTrigger asChild>
                    <SidebarMenuButton variant="ghost" className="w-full justify-start gap-2">
                        <BarChart2 className="h-4 w-4" />
                        Analytics
                        <ChevronRight className="ml-auto h-4 w-4 transition-transform duration-200 [&[data-state=open]]:rotate-90" />
                    </SidebarMenuButton>
                </CollapsibleTrigger>
                <CollapsibleContent>
                    <SidebarMenuButton href="#" variant="ghost" className="w-full justify-start gap-2 ml-6">
                        Usage
                    </SidebarMenuButton>
                    <SidebarMenuButton href="#" variant="ghost" className="w-full justify-start gap-2 ml-6">
                        Engagement
                    </SidebarMenuButton>
                    <SidebarMenuButton href="#" variant="ghost" className="w-full justify-start gap-2 ml-6">
                        Reports
                    </SidebarMenuButton>
                </CollapsibleContent>
            </Collapsible>
        </SidebarMenuItem>
        <SidebarMenuItem>
            <Collapsible>
                <CollapsibleTrigger asChild>
                    <SidebarMenuButton variant="ghost" className="w-full justify-start gap-2">
                        <Briefcase className="h-4 w-4" />
                        Accounting
                        <ChevronRight className="ml-auto h-4 w-4 transition-transform duration-200 [&[data-state=open]]:rotate-90" />
                    </SidebarMenuButton>
                </CollapsibleTrigger>
                <CollapsibleContent>
                    <SidebarMenuButton href="#" variant="ghost" className="w-full justify-start gap-2 ml-6">
                        Invoices
                    </SidebarMenuButton>
                    <SidebarMenuButton href="#" variant="ghost" className="w-full justify-start gap-2 ml-6">
                        Billing
                    </SidebarMenuButton>
                    <SidebarMenuButton href="#" variant="ghost" className="w-full justify-start gap-2 ml-6">
                        Subscriptions
                    </SidebarMenuButton>
                </CollapsibleContent>
            </Collapsible>
        </SidebarMenuItem>
      </SidebarMenu>
    );
  }