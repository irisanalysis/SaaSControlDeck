import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Check, X } from 'lucide-react';

const approvals = [
  { name: 'Michael Scott', role: 'Regional Manager', avatar: 'https://picsum.photos/id/1011/40/40', dataAiHint: 'man face' },
  { name: 'Dwight Schrute', role: 'Salesman', avatar: 'https://picsum.photos/id/1012/40/40', dataAiHint: 'person face' },
  { name: 'Pam Beesly', role: 'Receptionist', avatar: 'https://picsum.photos/id/1013/40/40', dataAiHint: 'woman face' },
];

const PendingApprovalsCard = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Pending Approvals</CardTitle>
        <CardDescription>Review and act on pending requests.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {approvals.map((approval, index) => (
            <div key={index} className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Avatar>
                  <AvatarImage src={approval.avatar} data-ai-hint={approval.dataAiHint} />
                  <AvatarFallback>{approval.name.substring(0, 2).toUpperCase()}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium text-sm">{approval.name}</p>
                  <p className="text-xs text-muted-foreground">{approval.role}</p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="icon" className="h-8 w-8">
                  <X className="h-4 w-4" />
                   <span className="sr-only">Deny</span>
                </Button>
                <Button size="icon" className="h-8 w-8">
                  <Check className="h-4 w-4" />
                   <span className="sr-only">Approve</span>
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default PendingApprovalsCard;
