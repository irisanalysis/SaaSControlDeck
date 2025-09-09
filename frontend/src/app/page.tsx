"use client";

import React from "react";

export const dynamic = 'force-dynamic';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ProfileCard from "@/components/dashboard/profile-card";
import PendingApprovalsCard from "@/components/dashboard/pending-approvals-card";
import SettingsCard from "@/components/dashboard/settings-card";
import IntegrationsCard from "@/components/dashboard/integrations-card";
import DeviceManagementCard from "@/components/dashboard/device-management-card";
import AIHelp from "@/components/ai/ai-help";
import { createCelebrationToast } from "@/components/ui/toast";

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
        {/* Enhanced Welcome Story Section */}
        <div className="bg-gradient-to-br from-orange-50 via-pink-50 to-rose-50 rounded-2xl p-8 mb-6 border border-orange-100/50 shadow-soft">
          <div className="flex items-center justify-between">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                <span className="text-sm font-medium text-green-700">System Status: All Services Online</span>
              </div>
              <h2 
                className={`text-4xl font-bold tracking-tight gradient-text cursor-pointer transition-all duration-300 ${
                  showEasterEgg ? 'animate-bounce text-transparent bg-gradient-to-r from-green-400 via-blue-500 to-purple-600 bg-clip-text' : ''
                } ${
                  clickCount > 5 ? 'animate-wiggle' : ''
                }`}
                onClick={handleLogoClick}
              >
                {showEasterEgg 
                  ? '🎉 You found the secret! 🎉' 
                  : clickCount > 5 
                  ? 'Hey there, clicky! 😄'
                  : 'Good morning, John!'
                }
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl">
                Your team has <span className="font-semibold text-orange-600">3 pending approvals</span> and 
                <span className="font-semibold text-pink-600">2 integrations</span> are syncing successfully. 
                Here's what's happening in your workspace today.
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <Button variant="outline" className="btn-glass hover:animate-float">
                🎆 Quick Tour
              </Button>
              <Button variant="magic" className="relative overflow-hidden group">
                <span className="relative z-10">Export Data</span>
                <div className="absolute inset-0 bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              </Button>
            </div>
          </div>
        </div>
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList className="grid w-full grid-cols-4 bg-gradient-to-r from-orange-50 to-pink-50 border border-orange-100/50 p-1 rounded-xl">
            <TabsTrigger 
              value="overview" 
              className="data-[state=active]:bg-white data-[state=active]:shadow-md data-[state=active]:text-orange-600 relative flex items-center gap-2"
            >
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
              Overview
            </TabsTrigger>
            <TabsTrigger 
              value="analytics" 
              className="data-[state=active]:bg-white data-[state=active]:shadow-md data-[state=active]:text-pink-600 relative flex items-center gap-2"
            >
              <div className="w-5 h-5 rounded-full bg-blue-100 text-blue-600 text-xs flex items-center justify-center font-semibold">5</div>
              Analytics
            </TabsTrigger>
            <TabsTrigger 
              value="reports" 
              className="data-[state=active]:bg-white data-[state=active]:shadow-md data-[state=active]:text-purple-600 relative flex items-center gap-2"
            >
              <div className="w-5 h-5 rounded-full bg-orange-100 text-orange-600 text-xs flex items-center justify-center font-semibold">3</div>
              Reports
            </TabsTrigger>
            <TabsTrigger 
              value="notifications" 
              className="data-[state=active]:bg-white data-[state=active]:shadow-md data-[state=active]:text-rose-600 relative flex items-center gap-2"
            >
              <div className="w-2 h-2 rounded-full bg-red-500"></div>
              Notifications
            </TabsTrigger>
          </TabsList>
          <TabsContent value="overview" className="space-y-4">
            {/* Key Performance Story Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card className="card-premium group">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Total Revenue
                  </CardTitle>
                  <div className="p-2 rounded-lg bg-gradient-to-br from-green-100 to-emerald-100 group-hover:from-green-200 group-hover:to-emerald-200 transition-all duration-300">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      className="h-4 w-4 text-green-600"
                    >
                      <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                    </svg>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-foreground">$45,231.89</div>
                  <div className="flex items-center gap-2 mt-2">
                    <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-green-100 text-green-700">
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd"/>
                      </svg>
                      <span className="text-xs font-medium">+20.1%</span>
                    </div>
                    <span className="text-xs text-muted-foreground">from last month</span>
                  </div>
                  <div className="mt-3 w-full bg-gray-200 rounded-full h-1.5">
                    <div className="bg-gradient-to-r from-green-400 to-emerald-500 h-1.5 rounded-full animate-pulse" style={{width: '75%'}}></div>
                  </div>
                </CardContent>
              </Card>
              
              <Card className="card-premium group">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Active Subscriptions
                  </CardTitle>
                  <div className="p-2 rounded-lg bg-gradient-to-br from-blue-100 to-cyan-100 group-hover:from-blue-200 group-hover:to-cyan-200 transition-all duration-300">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      className="h-4 w-4 text-blue-600"
                    >
                      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                      <circle cx="9" cy="7" r="4" />
                      <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
                    </svg>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-foreground">2,350</div>
                  <div className="flex items-center gap-2 mt-2">
                    <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-blue-100 text-blue-700">
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd"/>
                      </svg>
                      <span className="text-xs font-medium">+180.1%</span>
                    </div>
                    <span className="text-xs text-muted-foreground">growth this month</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Your subscription growth is <span className="font-medium text-blue-600">exceptional</span>
                  </p>
                </CardContent>
              </Card>
              
              <Card className="card-premium group">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Sales Performance
                  </CardTitle>
                  <div className="p-2 rounded-lg bg-gradient-to-br from-orange-100 to-pink-100 group-hover:from-orange-200 group-hover:to-pink-200 transition-all duration-300">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      className="h-4 w-4 text-orange-600"
                    >
                      <rect width="20" height="14" x="2" y="5" rx="2" />
                      <path d="M2 10h20" />
                    </svg>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-foreground">12,234</div>
                  <div className="flex items-center gap-2 mt-2">
                    <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-orange-100 text-orange-700">
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd"/>
                      </svg>
                      <span className="text-xs font-medium">+19%</span>
                    </div>
                    <span className="text-xs text-muted-foreground">quarterly target</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    On track to <span className="font-medium text-orange-600">exceed Q4 goals</span>
                  </p>
                </CardContent>
              </Card>
              
              <Card className="card-premium group">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    Active Users Now
                  </CardTitle>
                  <div className="p-2 rounded-lg bg-gradient-to-br from-purple-100 to-indigo-100 group-hover:from-purple-200 group-hover:to-indigo-200 transition-all duration-300">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      className="h-4 w-4 text-purple-600"
                    >
                      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                    </svg>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-foreground flex items-center gap-2">
                    <span className="tabular-nums hover:animate-bounce cursor-pointer" 
                          onClick={() => Math.random() > 0.9 && createConfetti()}
                          title="Feeling lucky? Click me! 🎲">573</span>
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse hover:animate-bounce cursor-pointer" 
                         title="Live users indicator - click for a surprise! 🎉"></div>
                  </div>
                  <div className="flex items-center gap-2 mt-2">
                    <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-green-100 text-green-700">
                      <span className="text-xs font-medium">+201</span>
                    </div>
                    <span className="text-xs text-muted-foreground">since last hour</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    <span className="font-medium text-purple-600">Peak engagement</span> period
                  </p>
                </CardContent>
              </Card>
            </div>
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
            <div className="grid gap-6">
              {/* Analytics Story Header */}
              <Card className="card-premium">
                <CardHeader className="bg-gradient-to-r from-blue-50 to-cyan-50 border-b">
                  <CardTitle className="text-2xl gradient-text flex items-center gap-3">
                    <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>
                    </svg>
                    Performance Analytics
                  </CardTitle>
                  <CardDescription className="text-base">
                    Deep insights into your platform's performance trends and user behavior patterns.
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-8">
                  <div className="grid md:grid-cols-3 gap-6">
                    <div className="text-center p-6 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100">
                      <div className="text-3xl font-bold text-blue-600 mb-2">94.2%</div>
                      <div className="text-sm text-blue-700 font-medium">User Satisfaction</div>
                      <div className="text-xs text-muted-foreground mt-1">↑ 2.1% from last quarter</div>
                    </div>
                    <div className="text-center p-6 rounded-xl bg-gradient-to-br from-green-50 to-green-100">
                      <div className="text-3xl font-bold text-green-600 mb-2">99.97%</div>
                      <div className="text-sm text-green-700 font-medium">Uptime Reliability</div>
                      <div className="text-xs text-muted-foreground mt-1">Industry leading</div>
                    </div>
                    <div className="text-center p-6 rounded-xl bg-gradient-to-br from-purple-50 to-purple-100">
                      <div className="text-3xl font-bold text-purple-600 mb-2">127ms</div>
                      <div className="text-sm text-purple-700 font-medium">Avg Response Time</div>
                      <div className="text-xs text-muted-foreground mt-1">↓ 15ms improvement</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              {/* Weekly Insights */}
              <div className="grid md:grid-cols-2 gap-6">
                <Card className="card-premium">
                  <CardHeader>
                    <CardTitle className="gradient-text flex items-center gap-2">
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V4a2 2 0 00-2-2H6zm1 2a1 1 0 000 2h6a1 1 0 100-2H7zm6 7a1 1 0 011 1v3a1 1 0 11-2 0v-3a1 1 0 011-1zm-3 3a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zm-4 1a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zm6-6a1 1 0 011 1v1a1 1 0 11-2 0V8a1 1 0 011-1zm-3 1a1 1 0 011 1v3a1 1 0 11-2 0V8a1 1 0 011-1zm-4 3a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1z" clipRule="evenodd"/>
                      </svg>
                      This Week's Growth Story
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between py-2">
                        <span className="text-sm text-muted-foreground">New User Signups</span>
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-green-400 to-green-600 rounded-full" style={{width: '78%'}}></div>
                          </div>
                          <span className="text-sm font-semibold text-green-600">+347</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between py-2">
                        <span className="text-sm text-muted-foreground">Feature Adoptions</span>
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full" style={{width: '65%'}}></div>
                          </div>
                          <span className="text-sm font-semibold text-blue-600">+89</span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between py-2">
                        <span className="text-sm text-muted-foreground">Support Tickets</span>
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-orange-400 to-orange-600 rounded-full" style={{width: '23%'}}></div>
                          </div>
                          <span className="text-sm font-semibold text-orange-600">-12</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                
                <Card className="card-premium">
                  <CardHeader>
                    <CardTitle className="gradient-text flex items-center gap-2">
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                      </svg>
                      Success Metrics
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="p-4 rounded-lg bg-gradient-to-r from-green-50 to-emerald-50 border border-green-100">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                            <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                            </svg>
                          </div>
                          <div>
                            <div className="font-semibold text-green-800">Goal Achievement</div>
                            <div className="text-sm text-green-600">Exceeded monthly targets by 23%</div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="p-4 rounded-lg bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-100">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                            <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z"/>
                            </svg>
                          </div>
                          <div>
                            <div className="font-semibold text-blue-800">Team Performance</div>
                            <div className="text-sm text-blue-600">All teams meeting productivity KPIs</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="reports" className="space-y-6">
            <Card className="card-premium">
              <CardHeader className="bg-gradient-to-r from-purple-50 to-indigo-50 border-b">
                <CardTitle className="text-2xl gradient-text flex items-center gap-3">
                  <svg className="w-6 h-6 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V4a2 2 0 00-2-2H6zm1 2a1 1 0 000 2h6a1 1 0 100-2H7zm6 7a1 1 0 011 1v3a1 1 0 11-2 0v-3a1 1 0 011-1zm-3 3a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zm-4 1a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1z" clipRule="evenodd"/>
                  </svg>
                  Intelligent Reports
                </CardTitle>
                <CardDescription className="text-base">
                  AI-powered insights and automated reporting for strategic decision making.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-8">
                <div className="grid md:grid-cols-2 gap-8">
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-foreground mb-4">Recent Reports</h3>
                    <div className="space-y-3">
                      {[
                        { title: "Monthly Performance Summary", status: "Ready", date: "Dec 8, 2024", color: "green" },
                        { title: "User Engagement Analysis", status: "Processing", date: "Dec 7, 2024", color: "blue" },
                        { title: "Revenue Forecast Q1 2025", status: "Scheduled", date: "Dec 15, 2024", color: "orange" }
                      ].map((report, index) => (
                        <div key={index} className="p-4 rounded-lg border bg-gradient-to-r from-white to-gray-50/30 hover:from-gray-50 hover:to-gray-100/50 transition-all duration-200">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="font-semibold text-foreground">{report.title}</div>
                              <div className="text-sm text-muted-foreground">{report.date}</div>
                            </div>
                            <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                              report.color === 'green' ? 'bg-green-100 text-green-700' :
                              report.color === 'blue' ? 'bg-blue-100 text-blue-700' :
                              'bg-orange-100 text-orange-700'
                            }`}>
                              {report.status}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-foreground mb-4">Quick Actions</h3>
                    <div className="grid gap-3">
                      <Button className="justify-start h-auto p-4 btn-gradient">
                        <div className="text-left">
                          <div className="font-semibold">Generate Custom Report</div>
                          <div className="text-sm opacity-90">Create tailored analytics reports</div>
                        </div>
                      </Button>
                      <Button variant="outline" className="justify-start h-auto p-4 btn-glass">
                        <div className="text-left">
                          <div className="font-semibold">Schedule Automation</div>
                          <div className="text-sm text-muted-foreground">Set up recurring reports</div>
                        </div>
                      </Button>
                      <Button variant="outline" className="justify-start h-auto p-4 btn-subtle">
                        <div className="text-left">
                          <div className="font-semibold">Export Data</div>
                          <div className="text-sm text-muted-foreground">Download raw data files</div>
                        </div>
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          <TabsContent value="notifications" className="space-y-6">
            <Card className="card-premium">
              <CardHeader className="bg-gradient-to-r from-rose-50 to-pink-50 border-b">
                <CardTitle className="text-2xl gradient-text flex items-center gap-3">
                  <svg className="w-6 h-6 text-rose-600" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z"/>
                  </svg>
                  Notification Center
                </CardTitle>
                <CardDescription className="text-base">
                  Stay informed with real-time updates and important system notifications.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-8">
                <div className="space-y-4">
                  {[
                    {
                      title: "System Update Complete",
                      description: "All services have been successfully updated to version 2.4.1",
                      time: "2 minutes ago",
                      type: "success",
                      icon: "check"
                    },
                    {
                      title: "New Team Member Joined",
                      description: "Sarah Wilson has been added to the Engineering team",
                      time: "1 hour ago",
                      type: "info",
                      icon: "user"
                    },
                    {
                      title: "Monthly Report Ready",
                      description: "Your November performance report is ready for review",
                      time: "3 hours ago",
                      type: "info",
                      icon: "document"
                    },
                    {
                      title: "Security Scan Completed",
                      description: "Weekly security scan found no vulnerabilities",
                      time: "1 day ago",
                      type: "success",
                      icon: "shield"
                    }
                  ].map((notification, index) => (
                    <div key={index} className="p-4 rounded-lg border bg-gradient-to-r from-white to-gray-50/30 hover:from-gray-50 hover:to-gray-100/50 transition-all duration-200">
                      <div className="flex items-start gap-4">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          notification.type === 'success' ? 'bg-green-100' :
                          notification.type === 'warning' ? 'bg-orange-100' :
                          'bg-blue-100'
                        }`}>
                          {notification.icon === 'check' && (
                            <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                            </svg>
                          )}
                          {notification.icon === 'user' && (
                            <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd"/>
                            </svg>
                          )}
                          {notification.icon === 'document' && (
                            <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd"/>
                            </svg>
                          )}
                          {notification.icon === 'shield' && (
                            <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                            </svg>
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="font-semibold text-foreground">{notification.title}</div>
                          <div className="text-sm text-muted-foreground mt-1">{notification.description}</div>
                          <div className="text-xs text-muted-foreground mt-2">{notification.time}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="pt-6 border-t mt-8">
                  <div className="flex items-center justify-between">
                    <Button variant="outline" className="btn-subtle">
                      Mark All as Read
                    </Button>
                    <Button className="btn-gradient">
                      Notification Settings
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
      <AIHelp />
    </>
  );
}
