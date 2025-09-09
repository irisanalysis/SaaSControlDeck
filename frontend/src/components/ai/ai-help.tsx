"use client";

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Lightbulb, Sparkles } from 'lucide-react';
import { AiContextualHelpOutput } from '@/ai/flows/ai-contextual-help';
import { Skeleton } from '@/components/ui/skeleton';

const AiHelp = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AiContextualHelpOutput | null>(null);
  const [error, setError] = useState<string | null>(null);

  const getHelp = async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetch('/api/ai-help', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userActivity: 'Viewing main dashboard',
          workflowContext: 'General overview of account status and activities',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to get AI help');
      }

      const result = await response.json();
      setResult(result);
    } catch (e) {
      setError('Failed to get help from AI. Please try again.');
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleOpenChange = (open: boolean) => {
    setIsOpen(open);
    if(open && !result && !isLoading) {
        getHelp();
    }
  }

  return (
    <>      <Button
        className="fixed bottom-6 right-6 h-16 w-16 rounded-full shadow-2xl bg-gradient-to-br from-orange-500 to-pink-500 hover:from-orange-600 hover:to-pink-600 hover:scale-110 transition-all duration-300 group border-2 border-white/20"
        style={{ boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25), 0 0 30px rgba(251, 146, 60, 0.25)' }}
        onClick={() => handleOpenChange(true)}
        aria-label="Open AI Help"
      >
        <div className="relative">
          <Lightbulb className="h-6 w-6 text-white group-hover:rotate-12 transition-transform duration-300" />
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full animate-pulse border border-white"></div>
        </div>
      </Button>
      <Dialog open={isOpen} onOpenChange={handleOpenChange}>
        <DialogContent className="sm:max-w-[500px] bg-gradient-to-br from-white via-orange-50/30 to-pink-50/30 border border-orange-100/50">
          <DialogHeader className="space-y-4">
            <DialogTitle className="flex items-center gap-3 text-xl">
              <div className="p-2 rounded-lg bg-gradient-to-br from-orange-100 to-pink-100">
                <Sparkles className="h-6 w-6 text-orange-600" />
              </div>
              <span className="gradient-text">AI Assistant</span>
              <div className="ml-auto flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                <span className="text-sm font-medium text-green-600">Online</span>
              </div>
            </DialogTitle>
            <DialogDescription className="text-base text-muted-foreground">
              Your intelligent workspace companion is ready to help with contextual insights, 
              recommendations, and guidance tailored to your current activity.
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-6 space-y-6">
            {isLoading && (
              <div className="space-y-4">
                <div className="flex items-center gap-3 p-4 rounded-lg bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-100">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <div className="w-4 h-4 rounded-full bg-blue-500 animate-spin"></div>
                  </div>
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-full" />
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                    <Skeleton className="h-4 w-1/3" />
                  </div>
                  <Skeleton className="h-4 w-5/6 ml-4" />
                  <Skeleton className="h-4 w-4/5 ml-4" />
                  <Skeleton className="h-4 w-3/5 ml-4" />
                </div>
              </div>
            )}
            
            {error && (
              <div className="p-4 rounded-lg bg-gradient-to-r from-red-50 to-rose-50 border border-red-100">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
                    <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
                    </svg>
                  </div>
                  <div>
                    <div className="font-semibold text-red-800">Unable to Connect</div>
                    <div className="text-sm text-red-600">{error}</div>
                  </div>
                </div>
              </div>
            )}
            
            {result && (
              <div className="space-y-6">
                {/* AI Response */}
                <div className="p-4 rounded-lg bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-100">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                      <Sparkles className="w-4 h-4 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-blue-800 mb-2">Contextual Insights</h3>
                      <p className="text-sm text-blue-700 leading-relaxed">{result.helpText}</p>
                    </div>
                  </div>
                </div>
                
                {/* Recommendations */}
                <div className="p-4 rounded-lg bg-gradient-to-r from-orange-50 to-pink-50 border border-orange-100">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center flex-shrink-0">
                      <svg className="w-4 h-4 text-orange-600" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-orange-800 mb-3">Smart Recommendations</h3>
                      <ul className="space-y-2">
                        {result.recommendations.map((rec, index) => (
                          <li key={index} className="flex items-start gap-2 text-sm text-orange-700">
                            <div className="w-1.5 h-1.5 rounded-full bg-orange-500 mt-2 flex-shrink-0"></div>
                            <span className="leading-relaxed">{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
                
                {/* Quick Actions */}
                <div className="grid grid-cols-2 gap-3">
                  <Button variant="outline" className="btn-glass h-auto p-3">
                    <div className="text-center">
                      <div className="text-sm font-medium">Get More Help</div>
                      <div className="text-xs text-muted-foreground">Detailed guidance</div>
                    </div>
                  </Button>
                  <Button className="btn-gradient h-auto p-3">
                    <div className="text-center">
                      <div className="text-sm font-medium text-white">Take Action</div>
                      <div className="text-xs text-white/80">Apply suggestions</div>
                    </div>
                  </Button>
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default AiHelp;
