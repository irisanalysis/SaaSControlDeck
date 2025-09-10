"use client";

import React from "react";

export const dynamic = 'force-dynamic';
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import ProfileCard from "../components/dashboard/profile-card";
import PendingApprovalsCard from "../components/dashboard/pending-approvals-card";
import SettingsCard from "../components/dashboard/settings-card";
import IntegrationsCard from "../components/dashboard/integrations-card";
import DeviceManagementCard from "../components/dashboard/device-management-card";
import AIHelp from "../components/ai/ai-help";
import { createCelebrationToast } from "../components/ui/toast";

export default function DashboardPage() {
  const [konami, setKonami] = React.useState<string>("");
  const [showEasterEgg, setShowEasterEgg] = React.useState(false);
  const [clickCount, setClickCount] = React.useState(0);
  const { createConfetti } = createCelebrationToast();
  
  // Konami code easter egg
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const konamiCode = "ArrowUpArrowUpArrowDownArrowDownArrowLeftArrowRightArrowLeftArrowRightKeyBKeyA";
      const newKonami = konami + e.code;
      
      if (konamiCode.startsWith(newKonami)) {
        setKonami(newKonami);
        if (newKonami === konamiCode) {
          setShowEasterEgg(true);
          createConfetti();
          setTimeout(() => setShowEasterEgg(false), 5000);
          setKonami("");
        }
      } else {
        setKonami("");
      }
    };
    
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [konami, createConfetti]);
  
  // Click counter easter egg
  const handleLogoClick = () => {
    setClickCount(prev => {
      const newCount = prev + 1;
      if (newCount === 10) {
        createConfetti();
        setTimeout(() => setClickCount(0), 3000);
      }
      return newCount;
    });
  };
  
  return (
    <>
      <div className="flex-1 space-y-4">
        {/* Simple test content */}
        <div className="bg-gradient-to-br from-orange-50 via-pink-50 to-rose-50 rounded-2xl p-8 mb-6 border border-orange-100/50 shadow-soft">
          <div className="flex items-center justify-between">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                <span className="text-sm font-medium text-green-700">System Status: All Services Online</span>
              </div>
              <h2 className="text-4xl font-bold tracking-tight gradient-text">
                Good morning, John!
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl">
                Testing relative imports deployment
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Button variant="outline" className="btn-glass hover:animate-float">
                🎆 Quick Tour
              </Button>
              <Button variant="magic" className="relative overflow-hidden group">
                <span className="relative z-10">Export Data</span>
              </Button>
            </div>
          </div>
        </div>
        
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4 bg-gradient-to-r from-orange-50 to-pink-50 border border-orange-100/50 p-1 rounded-xl">
            <TabsTrigger value="overview" className="data-[state=active]:bg-white">
              Overview
            </TabsTrigger>
            <TabsTrigger value="analytics" className="data-[state=active]:bg-white">
              Analytics
            </TabsTrigger>
            <TabsTrigger value="reports" className="data-[state=active]:bg-white">
              Reports
            </TabsTrigger>
            <TabsTrigger value="notifications" className="data-[state=active]:bg-white">
              Notifications
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-7">
              <div className="col-span-1 lg:col-span-4">
                <ProfileCard />
              </div>
              <div className="col-span-1 lg:col-span-3">
                <PendingApprovalsCard />
              </div>
              <div className="col-span-1 lg:col-span-3">
                <SettingsCard />
              </div>
              <div className="col-span-1 lg:col-span-4">
                <IntegrationsCard />
              </div>
              <div className="col-span-1 lg:col-span-7">
                <DeviceManagementCard />
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="analytics" className="space-y-6">
            <Card className="card-premium">
              <CardHeader>
                <CardTitle>Analytics Test</CardTitle>
                <CardDescription>Testing relative imports</CardDescription>
              </CardHeader>
              <CardContent>
                <p>Analytics content with relative imports</p>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="reports" className="space-y-6">
            <Card className="card-premium">
              <CardHeader>
                <CardTitle>Reports Test</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Reports content</p>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="notifications" className="space-y-6">
            <Card className="card-premium">
              <CardHeader>
                <CardTitle>Notifications Test</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Notifications content</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
      <AIHelp />
    </>
  );
}