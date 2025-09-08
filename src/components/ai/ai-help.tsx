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
import { aiContextualHelp, AiContextualHelpOutput } from '@/ai/flows/ai-contextual-help';
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
      const response = await aiContextualHelp({
        userActivity: 'Viewing main dashboard',
        workflowContext: 'General overview of account status and activities',
      });
      setResult(response);
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
    <>
      <Button
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg"
        onClick={() => handleOpenChange(true)}
        aria-label="Open AI Help"
      >
        <Lightbulb className="h-6 w-6" />
      </Button>
      <Dialog open={isOpen} onOpenChange={handleOpenChange}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                AI Contextual Help
            </DialogTitle>
            <DialogDescription>
              Get context-sensitive assistance and recommendations.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            {isLoading && (
              <div className="space-y-4">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-1/2" />
                <div className="pt-4 space-y-2">
                    <Skeleton className="h-4 w-1/3" />
                    <Skeleton className="h-4 w-5/6" />
                    <Skeleton className="h-4 w-5/6" />
                </div>
              </div>
            )}
            {error && <p className="text-destructive">{error}</p>}
            {result && (
              <div className="space-y-4">
                <div>
                    <h3 className="font-semibold text-foreground mb-2">Help</h3>
                    <p className="text-sm text-muted-foreground">{result.helpText}</p>
                </div>
                <div>
                    <h3 className="font-semibold text-foreground mb-2">Recommendations</h3>
                    <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                        {result.recommendations.map((rec, index) => (
                            <li key={index}>{rec}</li>
                        ))}
                    </ul>
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
