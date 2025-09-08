
"use client";

import { usePathname } from 'next/navigation';
import {
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuBadge,
  SidebarGroup,
  SidebarGroupLabel,
} from '@/components/ui/sidebar';
import {
  LayoutDashboard,
  FileText,
  BarChart2,
  CircleDollarSign,
  Settings,
  LifeBuoy,
} from 'lucide-react';
import Link from 'next/link';

const SidebarNav = () => {
  const pathname = usePathname();
  const isActive = (path: string) => pathname === path;

  return (
    <SidebarMenu>
      <SidebarGroup>
        <SidebarGroupLabel>Main</SidebarGroupLabel>
        <SidebarMenuItem>
          <Link href="/" passHref>
            <SidebarMenuButton asChild isActive={isActive('/')} tooltip="Dashboard">
                <span>
                    <LayoutDashboard />
                    Dashboard
                </span>
            </SidebarMenuButton>
          </Link>
        </SidebarMenuItem>
        <SidebarMenuItem>
          <Link href="#" passHref>
            <SidebarMenuButton asChild isActive={isActive('/documents')} tooltip="Documents">
                <span>
                    <FileText />
                    Documents
                    <SidebarMenuBadge>12</SidebarMenuBadge>
                </span>
            </SidebarMenuButton>
          </Link>
        </SidebarMenuItem>
        <SidebarMenuItem>
          <Link href="#" passHref>
            <SidebarMenuButton asChild isActive={isActive('/analytics')} tooltip="Analytics">
                <span>
                    <BarChart2 />
                    Analytics
                </span>
            </SidebarMenuButton>
          </Link>
        </SidebarMenuItem>
        <SidebarMenuItem>
         <Link href="#" passHref>
            <SidebarMenuButton asChild isActive={isActive('/accounting')} tooltip="Accounting">
                <span>
                    <CircleDollarSign />
                    Accounting
                </span>
            </SidebarMenuButton>
          </Link>
        </SidebarMenuItem>
      </SidebarGroup>

      <SidebarGroup className="mt-auto absolute bottom-0 w-full">
        <SidebarGroupLabel>General</SidebarGroupLabel>
        <SidebarMenuItem>
          <Link href="#" passHref>
            <SidebarMenuButton asChild isActive={isActive('/settings')} tooltip="Settings">
                <span>
                    <Settings />
                    Settings
                </span>
            </SidebarMenuButton>
          </Link>
        </SidebarMenuItem>
        <SidebarMenuItem>
          <Link href="#" passHref>
            <SidebarMenuButton asChild isActive={isActive('/support')} tooltip="Support">
                <span>
                    <LifeBuoy />
                    Support
                </span>
            </SidebarMenuButton>
          </Link>
        </SidebarMenuItem>
      </SidebarGroup>
    </SidebarMenu>
  );
};

export default SidebarNav;
