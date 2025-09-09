"use client";

import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 button-press",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm hover:shadow-lg hover:-translate-y-1 hover:scale-105 active:scale-95 transition-all duration-200",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90 shadow-sm hover:shadow-md hover:scale-105 active:scale-95",
        outline:
          "border border-input bg-background hover:bg-accent hover:text-accent-foreground hover:shadow-sm hover:scale-105 active:scale-95",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80 hover:shadow-sm hover:scale-105 active:scale-95",
        ghost: "hover:bg-accent hover:text-accent-foreground hover:scale-105 active:scale-95",
        link: "text-primary underline-offset-4 hover:underline hover:scale-105 active:scale-95",
        gradient: "bg-gradient-to-r from-orange-500 to-pink-500 text-white hover:from-orange-600 hover:to-pink-600 hover:-translate-y-1 hover:scale-105 active:scale-95 relative overflow-hidden shadow-lg hover:shadow-xl transition-all duration-300",
        glass: "bg-white/80 backdrop-blur-md border border-white/20 hover:bg-white/90 shadow-lg hover:scale-105 active:scale-95 transition-all duration-300",
        subtle: "bg-gradient-to-r from-primary/5 to-accent/5 border border-primary/10 hover:from-primary/10 hover:to-accent/10 hover:border-primary/20 hover:scale-105 active:scale-95",
        celebration: "bg-gradient-to-r from-green-500 to-emerald-500 text-white hover:from-green-600 hover:to-emerald-600 shadow-lg hover:shadow-xl hover:-translate-y-1 hover:scale-105 active:scale-95 relative overflow-hidden animate-bounce-gentle transition-all duration-300",
        magic: "bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 text-white hover:from-purple-600 hover:via-pink-600 hover:to-orange-600 shadow-lg hover:shadow-xl hover:-translate-y-1 hover:scale-105 active:scale-95 relative overflow-hidden animate-glow transition-all duration-300",
        success: "bg-gradient-to-r from-green-500 to-emerald-500 text-white hover:from-green-600 hover:to-emerald-600 shadow-lg hover:shadow-xl hover:-translate-y-1 hover:scale-105 active:scale-95 animate-heartbeat transition-all duration-300",
        playful: "bg-gradient-to-r from-pink-400 via-purple-400 to-indigo-400 text-white hover:from-pink-500 hover:via-purple-500 hover:to-indigo-500 shadow-lg hover:shadow-xl hover:-translate-y-2 hover:rotate-1 active:rotate-0 active:scale-95 transition-all duration-300",
        loading: "bg-muted text-muted-foreground cursor-not-allowed relative overflow-hidden",
        bounce: "hover:animate-bounce-gentle",
        wiggle: "hover:animate-wiggle",
        float: "hover:animate-float",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3 text-xs",
        lg: "h-12 rounded-lg px-8 text-base",
        xl: "h-14 rounded-lg px-10 text-lg",
        icon: "h-10 w-10",
        "icon-sm": "h-8 w-8",
        "icon-lg": "h-12 w-12",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, children, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    const [isPressed, setIsPressed] = React.useState(false)
    const [ripples, setRipples] = React.useState<Array<{ id: number; x: number; y: number }>>([])
    
    const handleMouseDown = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (variant === 'loading') return
      
      setIsPressed(true)
      
      // Create ripple effect for celebration variants
      if (variant === 'celebration' || variant === 'magic' || variant === 'success') {
        const rect = e.currentTarget.getBoundingClientRect()
        const x = e.clientX - rect.left
        const y = e.clientY - rect.top
        const newRipple = { id: Date.now(), x, y }
        
        setRipples(prev => [...prev, newRipple])
        
        setTimeout(() => {
          setRipples(prev => prev.filter(ripple => ripple.id !== newRipple.id))
        }, 800)
      }
      
      props.onMouseDown?.(e)
    }
    
    const handleMouseUp = () => {
      setIsPressed(false)
    }
    
    return (
      <Comp
        className={cn(
          buttonVariants({ variant, size, className }),
          isPressed && 'transform scale-95'
        )}
        ref={ref}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        {...props}
      >
        {variant === 'loading' && (
          <>
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
            <div className="flex items-center space-x-1 mr-2">
              <div className="w-1.5 h-1.5 bg-current rounded-full animate-loading-dots" />
              <div className="w-1.5 h-1.5 bg-current rounded-full animate-loading-dots" style={{ animationDelay: '0.2s' }} />
              <div className="w-1.5 h-1.5 bg-current rounded-full animate-loading-dots" style={{ animationDelay: '0.4s' }} />
            </div>
          </>
        )}
        
        {ripples.map(ripple => (
          <span
            key={ripple.id}
            className="absolute pointer-events-none rounded-full bg-white/30 animate-ping"
            style={{
              left: ripple.x - 10,
              top: ripple.y - 10,
              width: 20,
              height: 20,
            }}
          />
        ))}
        
        {children}
      </Comp>
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
