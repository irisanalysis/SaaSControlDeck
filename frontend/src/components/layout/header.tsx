"use client";

import { Search, Bell, User, ChevronDown, PanelLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { SidebarTrigger, useSidebar } from '@/components/ui/sidebar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { cn } from '@/lib/utils';

const Header = () => {
  const { open, toggleSidebar } = useSidebar();

  const notifications = [
    {
      id: 1,
      title: "Approval request requires review",
      description: "John Doe submitted a request for your approval.",
      time: "2 min ago",
      type: "approval"
    },
    {
      id: 2,
      title: "Integration synchronization completed",
      description: "Your Slack integration has been successfully updated.",
      time: "1 hr ago",
      type: "integration"
    },
    {
      id: 3,
      title: "Team member successfully onboarded",
      description: "Sarah Wilson has been added to your workspace.",
      time: "3 hr ago",
      type: "team"
    }
  ];

  return (
    <>
      {/* 浮动侧栏切换按钮 - 仅在侧栏隐藏时显示 */}
      {!open && (
        <Button
          onClick={toggleSidebar}
          className={cn(
            "fixed left-4 top-1/2 z-50 -translate-y-1/2 h-12 w-12 rounded-2xl p-0",
            "bg-gradient-to-br from-orange-500 via-pink-500 to-rose-500 text-white shadow-2xl",
            "hover:from-orange-600 hover:via-pink-600 hover:to-rose-600",
            "hover:scale-110 transition-all duration-300 ease-out",
            "border border-white/20 backdrop-blur-sm",
            "group flex items-center justify-center"
          )}
          title="打开侧栏"
        >
          <PanelLeft className="h-5 w-5 transition-transform group-hover:scale-110" />
          <span className="sr-only">打开侧栏</span>
        </Button>
      )}

      <header className="sticky top-0 z-30 flex h-20 items-center gap-4 border-b bg-gradient-to-r from-orange-400 via-pink-400 to-rose-400 px-4 shadow-lg sm:px-6">
        <SidebarTrigger className="text-white hover:text-white hover:bg-white/20 data-[state=open]:bg-transparent transition-all duration-200" />
      
      {/* Welcome Message & Search */}
      <div className="flex-1 flex flex-col gap-1">
        <div className="text-white/90 text-sm font-medium">
          Good morning, John
        </div>
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
          <Input
            type="search"
            placeholder="Search anything..."
            className="w-full rounded-lg bg-white/95 pl-10 border-white/20 focus:bg-white focus:ring-2 focus:ring-white/30 transition-all duration-200"
          />
        </div>
      </div>
      
      <div className="flex items-center gap-3">
        {/* Enhanced Notifications */}
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="ghost" size="icon" className="relative text-white hover:text-white hover:bg-white/20 transition-all duration-200">
              <Bell className="h-5 w-5" />
              <span className="absolute -top-1 -right-1 flex h-5 w-5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-5 w-5 bg-red-500 text-white text-xs items-center justify-center font-medium">
                  {notifications.length}
                </span>
              </span>
              <span className="sr-only">Toggle notifications</span>
            </Button>
          </PopoverTrigger>
          <PopoverContent align="end" className="w-96 p-0">
            <div className="p-4 border-b">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-lg">Notifications</h3>
                <span className="text-sm text-muted-foreground">
                  {notifications.length} new
                </span>
              </div>
            </div>
            <div className="max-h-80 overflow-y-auto">
              {notifications.map((notification, index) => (
                <div key={notification.id} className={`p-4 hover:bg-accent cursor-pointer transition-colors ${
                  index !== notifications.length - 1 ? 'border-b' : ''
                }`}>
                  <div className="flex items-start gap-3">
                    <div className={`w-2 h-2 rounded-full mt-2 ${
                      notification.type === 'approval' ? 'bg-orange-500' :
                      notification.type === 'integration' ? 'bg-green-500' :
                      notification.type === 'team' ? 'bg-blue-500' : 'bg-gray-500'
                    }`} />
                    <div className="flex-1 space-y-1">
                      <p className="font-medium text-sm">{notification.title}</p>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {notification.description}
                      </p>
                      <p className="text-xs text-muted-foreground">{notification.time}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="p-3 border-t">
              <Button variant="ghost" className="w-full text-sm">
                View all notifications
              </Button>
            </div>
          </PopoverContent>
        </Popover>

        {/* Enhanced User Profile */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-auto p-2 rounded-lg text-white hover:bg-white/20 transition-all duration-200">
              <div className="flex items-center gap-3">
                <Avatar className="h-10 w-10 border-2 border-white/30">
                  <AvatarImage src="https://picsum.photos/100/100" data-ai-hint="person face" alt="John Doe" />
                  <AvatarFallback className="bg-white/20 text-white font-semibold">
                    JD
                  </AvatarFallback>
                </Avatar>
                <div className="hidden md:block text-left">
                  <div className="text-sm font-medium">John Doe</div>
                  <div className="text-xs text-white/70">Product Manager</div>
                </div>
                <ChevronDown className="h-4 w-4 text-white/70" />
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64">
            <DropdownMenuLabel className="pb-2">
              <div className="flex items-center gap-3">
                <Avatar className="h-12 w-12">
                  <AvatarImage src="https://picsum.photos/100/100" data-ai-hint="person face" alt="John Doe" />
                  <AvatarFallback>JD</AvatarFallback>
                </Avatar>
                <div>
                  <div className="font-medium">John Doe</div>
                  <div className="text-sm text-muted-foreground">john.doe@company.com</div>
                  <div className="text-xs text-muted-foreground">Product Manager</div>
                </div>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="cursor-pointer">
              <User className="mr-2 h-4 w-4" />
              Profile Settings
            </DropdownMenuItem>
            <DropdownMenuItem className="cursor-pointer">
              Billing & Usage
            </DropdownMenuItem>
            <DropdownMenuItem className="cursor-pointer">
              Team Settings
            </DropdownMenuItem>
            <DropdownMenuItem className="cursor-pointer">
              Preferences
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="cursor-pointer text-red-600">
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
    </>
  );
};

export default Header;
