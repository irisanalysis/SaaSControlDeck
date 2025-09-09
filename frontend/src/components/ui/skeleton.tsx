import { cn } from "@/lib/utils"
import React from "react"

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'shimmer' | 'wave' | 'dots'
  avatar?: boolean
  lines?: number
}

function Skeleton({
  className,
  variant = 'default',
  avatar = false,
  lines,
  ...props
}: SkeletonProps) {
  const baseClasses = "rounded-md bg-muted"
  
  const variants = {
    default: "animate-pulse",
    shimmer: "loading-skeleton-animated",
    wave: "animate-shimmer bg-gradient-to-r from-muted via-muted/50 to-muted bg-[length:200%_100%]",
    dots: "animate-loading-dots"
  }
  
  if (avatar) {
    return (
      <div className={cn("flex items-center space-x-4", className)}>
        <div className={cn("h-12 w-12 rounded-full", baseClasses, variants[variant])} />
        <div className="space-y-2">
          <div className={cn("h-4 w-[250px]", baseClasses, variants[variant])} />
          <div className={cn("h-4 w-[200px]", baseClasses, variants[variant])} />
        </div>
      </div>
    )
  }
  
  if (lines) {
    return (
      <div className={cn("space-y-2", className)}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={cn(
              "h-4",
              i === lines - 1 ? "w-[80%]" : "w-full",
              baseClasses,
              variants[variant]
            )}
            style={{ animationDelay: `${i * 100}ms` }}
          />
        ))}
      </div>
    )
  }
  
  return (
    <div
      className={cn(baseClasses, variants[variant], className)}
      {...props}
    />
  )
}

// Delightful loading component for empty states
function EmptyStateSkeleton({ message = "Loading something amazing..." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="relative">
        <div className="animate-float">
          <div className="w-16 h-16 rounded-full bg-gradient-to-r from-orange-100 to-pink-100 flex items-center justify-center mb-4">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-orange-400 to-pink-400 animate-pulse" />
          </div>
        </div>
        <div className="absolute -top-2 -right-2 w-4 h-4 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '0.5s' }} />
        <div className="absolute -bottom-2 -left-2 w-3 h-3 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '1s' }} />
      </div>
      <div className="text-center space-y-2 mt-4">
        <div className="h-4 w-48 bg-muted rounded animate-shimmer mx-auto" />
        <div className="h-3 w-32 bg-muted/70 rounded animate-shimmer mx-auto" style={{ animationDelay: '0.2s' }} />
        <p className="text-sm text-muted-foreground mt-4 typing-effect" style={{ animationDelay: '1s' }}>
          {message}
        </p>
      </div>
    </div>
  )
}

export { Skeleton, EmptyStateSkeleton }
