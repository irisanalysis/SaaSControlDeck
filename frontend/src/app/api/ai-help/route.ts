import { NextRequest, NextResponse } from 'next/server';
import { aiContextualHelp, AiContextualHelpInput } from '@/ai/flows/ai-contextual-help';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json() as AiContextualHelpInput;
    
    // Validate input
    if (!body.userActivity || !body.workflowContext) {
      return NextResponse.json(
        { error: 'Missing required fields: userActivity and workflowContext' },
        { status: 400 }
      );
    }

    // Call the AI flow
    const result = await aiContextualHelp(body);
    
    return NextResponse.json(result);
  } catch (error) {
    console.error('AI Help API error:', error);
    
    // Return a more specific error response
    const errorMessage = error instanceof Error ? error.message : 'An unexpected error occurred';
    
    return NextResponse.json(
      { error: errorMessage },
      { status: 500 }
    );
  }
}