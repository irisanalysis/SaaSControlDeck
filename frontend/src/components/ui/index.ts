// UI Components Barrel Export
// This file provides a centralized export for all UI components
// to improve module resolution and reduce import complexity

export { Button, type ButtonProps } from './button';
export { 
  Card, 
  CardHeader, 
  CardFooter, 
  CardTitle, 
  CardDescription, 
  CardContent 
} from './card';
export { 
  Tabs, 
  TabsList, 
  TabsTrigger, 
  TabsContent 
} from './tabs';
export { 
  Avatar, 
  AvatarImage, 
  AvatarFallback 
} from './avatar';
export { Badge, type BadgeProps } from './badge';
export { Input } from './input';
export { Label } from './label';
export { 
  Select, 
  SelectValue, 
  SelectTrigger, 
  SelectContent, 
  SelectItem 
} from './select';
export { createCelebrationToast } from './toast';