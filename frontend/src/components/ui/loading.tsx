"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface LoadingProps {
  variant?: "dots" | "spinner" | "pulse" | "wave" | "bounce" | "gradient";
  size?: "sm" | "md" | "lg";
  text?: string;
  className?: string;
}

const loadingMessages = [
  "Loading awesome content...",
  "Preparing something amazing...",
  "Gathering the magic...",
  "Just a moment of awesomeness...",
  "Creating delightful experiences...",
  "Brewing something special...",
  "Sprinkling some stardust...",
  "Almost ready to wow you...",
]

export function Loading({
  variant = "dots",
  size = "md",
  text,
  className
}: LoadingProps) {
  const [currentMessage, setCurrentMessage] = React.useState(text || loadingMessages[0]);
  const [messageIndex, setMessageIndex] = React.useState(0);

  React.useEffect(() => {
    if (!text) {
      const interval = setInterval(() => {
        setMessageIndex((prev) => (prev + 1) % loadingMessages.length);
      }, 2000);
      return () => clearInterval(interval);
    }
  }, [text]);

  React.useEffect(() => {
    if (!text) {
      setCurrentMessage(loadingMessages[messageIndex]);
    }
  }, [messageIndex, text]);

  const sizeClasses = {
    sm: "w-4 h-4",
    md: "w-6 h-6",
    lg: "w-8 h-8"
  };

  const dotSizeClasses = {
    sm: "w-1.5 h-1.5",
    md: "w-2 h-2", 
    lg: "w-3 h-3"
  };

  const renderLoader = () => {
    switch (variant) {
      case "dots":
        return (
          <div className="flex items-center space-x-2">
            <div className={cn("rounded-full bg-orange-500 animate-loading-dots", dotSizeClasses[size])} />
            <div className={cn("rounded-full bg-pink-500 animate-loading-dots", dotSizeClasses[size])} style={{ animationDelay: '0.2s' }} />
            <div className={cn("rounded-full bg-purple-500 animate-loading-dots", dotSizeClasses[size])} style={{ animationDelay: '0.4s' }} />
          </div>
        );
      
      case "spinner":
        return (
          <div className={cn("animate-spin rounded-full border-2 border-orange-200 border-t-orange-500", sizeClasses[size])} />
        );
      
      case "pulse":
        return (
          <div className={cn("rounded-full bg-gradient-to-r from-orange-400 to-pink-400 animate-pulse", sizeClasses[size])} />
        );
      
      case "wave":
        return (
          <div className="flex items-end space-x-1">
            {[0, 1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className={cn("bg-gradient-to-t from-orange-400 to-pink-400 animate-bounce", 
                  size === 'sm' ? 'w-1' : size === 'md' ? 'w-1.5' : 'w-2',
                  size === 'sm' ? 'h-6' : size === 'md' ? 'h-8' : 'h-10'
                )}
                style={{ 
                  animationDelay: `${i * 0.1}s`,
                  animationDuration: '0.6s',
                  animationIterationCount: 'infinite'
                }}
              />
            ))}
          </div>
        );
      
      case "bounce":
        return (
          <div className="flex space-x-2">
            <div className={cn("rounded-full bg-orange-400 animate-bounce", dotSizeClasses[size])} />
            <div className={cn("rounded-full bg-pink-400 animate-bounce", dotSizeClasses[size])} style={{ animationDelay: '0.1s' }} />
            <div className={cn("rounded-full bg-purple-400 animate-bounce", dotSizeClasses[size])} style={{ animationDelay: '0.2s' }} />
          </div>
        );
      
      case "gradient":
        return (
          <div className={cn("rounded-full bg-gradient-to-r from-orange-400 via-pink-400 to-purple-400 animate-spin", sizeClasses[size])}>
            <div className={cn("rounded-full bg-white animate-pulse", 
              size === 'sm' ? 'w-2 h-2 m-1' : 
              size === 'md' ? 'w-3 h-3 m-1.5' : 
              'w-4 h-4 m-2'
            )} />
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className={cn("flex flex-col items-center justify-center space-y-4", className)}>
      <div className="flex items-center justify-center">
        {renderLoader()}
      </div>
      
      {(text || !text) && (
        <div className="text-center">
          <p className={cn(
            "text-muted-foreground font-medium animate-fade-in-up",
            size === 'sm' ? 'text-xs' : size === 'md' ? 'text-sm' : 'text-base'
          )}>
            {currentMessage}
          </p>
          
          {!text && (
            <div className="flex justify-center mt-2 space-x-1">
              <div className="w-1 h-1 bg-orange-300 rounded-full animate-pulse" />
              <div className="w-1 h-1 bg-pink-300 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
              <div className="w-1 h-1 bg-purple-300 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Full-screen loading overlay component
export function LoadingOverlay({ 
  isVisible, 
  variant = "dots", 
  text,
  backdrop = true 
}: {
  isVisible: boolean;
  variant?: LoadingProps["variant"];
  text?: string;
  backdrop?: boolean;
}) {
  if (!isVisible) return null;

  return (
    <div className={cn(
      "fixed inset-0 z-50 flex items-center justify-center",
      backdrop && "bg-black/20 backdrop-blur-sm"
    )}>
      <div className="bg-white rounded-xl shadow-2xl p-8 m-4 max-w-sm w-full">
        <Loading variant={variant} size="lg" text={text} />
      </div>
    </div>
  );
}

// Inline loading for buttons and smaller components
export function InlineLoading({ 
  size = "sm",
  className 
}: { 
  size?: "xs" | "sm" | "md"; 
  className?: string; 
}) {
  const sizeMap = {
    xs: "w-3 h-3",
    sm: "w-4 h-4", 
    md: "w-5 h-5"
  };

  return (
    <div className={cn("flex items-center space-x-1", className)}>
      <div className={cn("animate-spin rounded-full border border-current border-t-transparent", sizeMap[size])} />
    </div>
  );
}