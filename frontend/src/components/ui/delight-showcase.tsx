"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Loading, LoadingOverlay } from "@/components/ui/loading";
import { EmptyState } from "@/components/ui/empty-state";
import { Badge } from "@/components/ui/badge";
import { 
  Sparkles, 
  Heart, 
  Star, 
  Zap, 
  Gift,
  Rocket,
  Trophy,
  Crown
} from "lucide-react";
import { createCelebrationToast } from "@/components/ui/toast";

export function DelightShowcase() {
  const [showLoading, setShowLoading] = React.useState(false);
  const [celebrating, setCelebrating] = React.useState(false);
  const { createConfetti } = createCelebrationToast();

  const triggerCelebration = () => {
    setCelebrating(true);
    createConfetti();
    setTimeout(() => setCelebrating(false), 2000);
  };

  const showcaseItems = [
    {
      title: "Interactive Buttons",
      description: "Buttons with delightful hover states and press effects",
      component: (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <Button variant="celebration">🎉 Celebrate</Button>
            <Button variant="magic">✨ Magic</Button>
            <Button variant="success">💚 Success</Button>
            <Button variant="playful">🎨 Playful</Button>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="bounce" className="hover:animate-bounce-gentle">Bounce</Button>
            <Button variant="wiggle" className="hover:animate-wiggle">Wiggle</Button>
            <Button variant="float" className="hover:animate-float">Float</Button>
          </div>
        </div>
      )
    },
    {
      title: "Loading States",
      description: "Engaging loading animations that make waiting fun",
      component: (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <Loading variant="dots" size="md" text="Loading dots..." />
            </div>
            <div className="text-center">
              <Loading variant="wave" size="md" text="Wave animation..." />
            </div>
          </div>
          <Button 
            variant="outline" 
            onClick={() => setShowLoading(true)}
            className="w-full"
          >
            Show Overlay Loading
          </Button>
          <LoadingOverlay 
            isVisible={showLoading}
            variant="gradient"
            text="Creating something amazing..."
          />
          {showLoading && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm">
              <Card className="p-6">
                <Loading variant="gradient" size="lg" text="Loading in style..." />
                <Button 
                  variant="outline" 
                  onClick={() => setShowLoading(false)}
                  className="mt-4 w-full"
                >
                  Close
                </Button>
              </Card>
            </div>
          )}
        </div>
      )
    },
    {
      title: "Skeleton Variants",
      description: "Animated placeholder content that feels alive",
      component: (
        <div className="space-y-4">
          <Skeleton variant="shimmer" className="h-4 w-full" />
          <Skeleton variant="wave" className="h-4 w-3/4" />
          <Skeleton avatar />
          <Skeleton lines={3} variant="shimmer" />
        </div>
      )
    },
    {
      title: "Animated Badges",
      description: "Status indicators with personality",
      component: (
        <div className="flex flex-wrap gap-2">
          <Badge className="bg-green-100 text-green-800 animate-pulse">🟢 Online</Badge>
          <Badge className="bg-orange-100 text-orange-800 hover:animate-bounce">⚡ Processing</Badge>
          <Badge className="bg-blue-100 text-blue-800 hover:animate-wiggle">🔄 Syncing</Badge>
          <Badge className="bg-purple-100 text-purple-800 animate-glow">✨ Premium</Badge>
          <Badge className="bg-pink-100 text-pink-800 hover:animate-heartbeat">💝 Special</Badge>
        </div>
      )
    },
    {
      title: "Celebration Triggers",
      description: "Interactive elements that reward user engagement",
      component: (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Card className={`p-4 cursor-pointer transition-all duration-300 hover:scale-105 ${celebrating ? 'success-celebration active' : ''}`} onClick={triggerCelebration}>
              <div className="text-center">
                <Trophy className="w-8 h-8 mx-auto mb-2 text-yellow-500" />
                <p className="text-sm font-medium">Click for Confetti!</p>
              </div>
            </Card>
            <Card className="p-4 hover:animate-float">
              <div className="text-center">
                <Rocket className="w-8 h-8 mx-auto mb-2 text-blue-500 hover:animate-bounce" />
                <p className="text-sm font-medium">Hover to Float</p>
              </div>
            </Card>
          </div>
          <div className="text-center">
            <Button 
              variant="magic" 
              onClick={triggerCelebration}
              className="relative overflow-hidden"
            >
              <Crown className="w-4 h-4 mr-2" />
              Trigger Magic!
            </Button>
          </div>
        </div>
      )
    },
    {
      title: "Micro-Interactions",
      description: "Subtle animations that enhance user experience",
      component: (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-2">
            <div className="h-12 w-12 bg-gradient-to-r from-orange-400 to-pink-400 rounded-full hover:animate-bounce cursor-pointer flex items-center justify-center">
              ⚡
            </div>
            <div className="h-12 w-12 bg-gradient-to-r from-green-400 to-blue-400 rounded-full hover:animate-wiggle cursor-pointer flex items-center justify-center">
              🎯
            </div>
            <div className="h-12 w-12 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full hover:animate-float cursor-pointer flex items-center justify-center">
              ✨
            </div>
          </div>
          <div className="text-xs text-center text-muted-foreground">
            Hover over the circles above for different animations
          </div>
        </div>
      )
    }
  ];

  return (
    <div className="space-y-8 p-6">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold gradient-text mb-4">
          ✨ Delight Showcase ✨
        </h1>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          A collection of micro-interactions and animations designed to bring joy 
          and personality to your SaaS platform. Each element is crafted to create 
          memorable moments that users will love.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {showcaseItems.map((item, index) => (
          <Card key={index} className="card-hover shadow-soft">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Sparkles className="w-5 h-5 text-orange-500" />
                {item.title}
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                {item.description}
              </p>
            </CardHeader>
            <CardContent>
              {item.component}
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="mt-8 bg-gradient-to-r from-orange-50 via-pink-50 to-rose-50 border-orange-200">
        <CardHeader>
          <CardTitle className="gradient-text flex items-center gap-2">
            <Gift className="w-5 h-5" />
            Easter Eggs & Hidden Features
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            <div className="flex items-start gap-3">
              <span className="text-orange-500">🎮</span>
              <div>
                <strong>Konami Code:</strong> Try the classic up-up-down-down-left-right-left-right-B-A sequence on the main dashboard
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-pink-500">👆</span>
              <div>
                <strong>Click Counter:</strong> Click the main title multiple times for a surprise
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-purple-500">🎯</span>
              <div>
                <strong>Lucky Clicks:</strong> Some numbers have a 10% chance of triggering confetti when clicked
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="text-green-500">🎨</span>
              <div>
                <strong>Drag & Drop Fun:</strong> Try dragging files onto upload areas for delightful feedback
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}