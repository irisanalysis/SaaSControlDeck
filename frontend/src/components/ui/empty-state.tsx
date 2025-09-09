"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
    variant?: "default" | "outline" | "celebration" | "magic";
  };
  className?: string;
  animated?: boolean;
  variant?: "default" | "playful" | "minimal";
}

export function EmptyState({
  title = "Nothing here yet",
  description = "But don't worry, great things are coming!",
  icon,
  action,
  className,
  animated = true,
  variant = "playful"
}: EmptyStateProps) {
  const [showEasterEgg, setShowEasterEgg] = React.useState(false);
  const clickCount = React.useRef(0);

  const handleTitleClick = () => {
    clickCount.current += 1;
    if (clickCount.current >= 7) {
      setShowEasterEgg(true);
      setTimeout(() => {
        setShowEasterEgg(false);
        clickCount.current = 0;
      }, 3000);
    }
  };

  const defaultIcon = (
    <div className="relative">
      <div className={cn(
        "w-24 h-24 rounded-full bg-gradient-to-br from-orange-100 to-pink-100 flex items-center justify-center mb-6",
        animated && "animate-float"
      )}>
        <div className="w-12 h-12 rounded-full bg-gradient-to-r from-orange-400 to-pink-400 flex items-center justify-center">
          <span className="text-2xl">✨</span>
        </div>
      </div>
      {animated && (
        <>
          <div className="absolute -top-2 -right-2 w-4 h-4 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '0.5s' }} />
          <div className="absolute -bottom-2 -left-2 w-3 h-3 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '1s' }} />
          <div className="absolute top-1/2 -left-4 w-2 h-2 bg-purple-400 rounded-full animate-ping" style={{ animationDelay: '1.5s' }} />
        </>
      )}
    </div>
  );

  return (
    <div className={cn(
      "flex flex-col items-center justify-center py-12 px-4 text-center",
      className
    )}>
      {/* Easter Egg Animation */}
      {showEasterEgg && (
        <div className="fixed inset-0 pointer-events-none z-50 flex items-center justify-center">
          <div className="text-8xl animate-bounce-gentle">🎉</div>
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="absolute w-3 h-3 rounded-full animate-bounce"
              style={{
                left: `${20 + i * 10}%`,
                top: `${30 + Math.sin(i) * 20}%`,
                background: ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#f0932b'][i % 5],
                animationDelay: `${i * 0.1}s`,
                animationDuration: '1s'
              }}
            />
          ))}
        </div>
      )}

      {/* Main Content */}
      <div className={cn(
        "space-y-4 max-w-md",
        variant === "playful" && "transform hover:scale-105 transition-transform duration-300"
      )}>
        {/* Icon */}
        <div className="flex justify-center">
          {icon || defaultIcon}
        </div>

        {/* Title */}
        <h3 
          className={cn(
            "text-xl font-semibold text-foreground cursor-pointer select-none transition-all duration-200",
            animated && "hover:text-orange-500 hover:scale-105"
          )}
          onClick={handleTitleClick}
        >
          {showEasterEgg ? "🎊 You found the secret! 🎊" : title}
        </h3>

        {/* Description */}
        <p className={cn(
          "text-muted-foreground",
          variant === "playful" && animated && "animate-fade-in-up"
        )} style={{ animationDelay: '0.2s' }}>
          {showEasterEgg 
            ? "Congrats! You're clearly a person who pays attention to details. That's awesome! 🌟" 
            : description
          }
        </p>

        {/* Playful Loading Dots */}
        {variant === "playful" && animated && (
          <div className="flex justify-center space-x-2 mt-6" style={{ animationDelay: '0.4s' }}>
            <div className="w-2 h-2 bg-orange-400 rounded-full animate-loading-dots" />
            <div className="w-2 h-2 bg-pink-400 rounded-full animate-loading-dots" style={{ animationDelay: '0.2s' }} />
            <div className="w-2 h-2 bg-purple-400 rounded-full animate-loading-dots" style={{ animationDelay: '0.4s' }} />
          </div>
        )}

        {/* Action Button */}
        {action && (
          <div className={cn(
            "pt-4",
            animated && "animate-fade-in-up"
          )} style={{ animationDelay: '0.6s' }}>
            <Button
              variant={action.variant || "celebration"}
              onClick={action.onClick}
              className="hover:animate-bounce-gentle"
            >
              {action.label}
            </Button>
          </div>
        )}
      </div>

      {/* Ambient Decorations for Playful Variant */}
      {variant === "playful" && animated && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-1/4 left-1/4 w-1 h-1 bg-orange-300 rounded-full animate-float" style={{ animationDelay: '2s', animationDuration: '4s' }} />
          <div className="absolute top-1/3 right-1/3 w-1 h-1 bg-pink-300 rounded-full animate-float" style={{ animationDelay: '3s', animationDuration: '5s' }} />
          <div className="absolute bottom-1/4 left-1/3 w-1 h-1 bg-purple-300 rounded-full animate-float" style={{ animationDelay: '1s', animationDuration: '6s' }} />
        </div>
      )}
    </div>
  );
}