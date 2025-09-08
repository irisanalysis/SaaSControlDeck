'use server';
/**
 * @fileOverview An AI-powered contextual help tool that provides context-sensitive assistance and recommendations within the interface.
 *
 * - aiContextualHelp - A function that returns context-sensitive help based on user activity and workflow.
 * - AiContextualHelpInput - The input type for the aiContextualHelp function.
 * - AiContextualHelpOutput - The return type for the aiContextualHelp function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const AiContextualHelpInputSchema = z.object({
  userActivity: z
    .string()
    .describe('The current activity the user is performing.'),
  workflowContext: z
    .string()
    .describe('The current workflow context of the user.'),
});
export type AiContextualHelpInput = z.infer<typeof AiContextualHelpInputSchema>;

const AiContextualHelpOutputSchema = z.object({
  helpText: z.string().describe('The context-sensitive help text to display to the user.'),
  recommendations: z.array(z.string()).describe('A list of recommendations for the user.'),
});
export type AiContextualHelpOutput = z.infer<typeof AiContextualHelpOutputSchema>;

export async function aiContextualHelp(input: AiContextualHelpInput): Promise<AiContextualHelpOutput> {
  return aiContextualHelpFlow(input);
}

const prompt = ai.definePrompt({
  name: 'aiContextualHelpPrompt',
  input: {schema: AiContextualHelpInputSchema},
  output: {schema: AiContextualHelpOutputSchema},
  prompt: `You are an AI-powered assistant designed to provide context-sensitive help and recommendations to users of a SaaS platform.

  Based on the user's current activity and workflow context, provide helpful information and suggestions to improve their efficiency and understanding of the platform features.

  Activity: {{{userActivity}}}
  Workflow Context: {{{workflowContext}}}

  Provide help text and a list of recommendations.`,
});

const aiContextualHelpFlow = ai.defineFlow(
  {
    name: 'aiContextualHelpFlow',
    inputSchema: AiContextualHelpInputSchema,
    outputSchema: AiContextualHelpOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
