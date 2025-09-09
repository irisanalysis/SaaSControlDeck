"use client";

import React from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Check, X, Clock, UserPlus, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { createCelebrationToast } from "@/components/ui/toast";

type Approval = {
  id: string;
  name: string;
  role: string;
  avatar: string;
  fallback: string;
  requestType: 'access' | 'role_change' | 'new_user';
  department: string;
  requestDate: string;
  priority: 'low' | 'medium' | 'high';
};

const approvals: Approval[] = [
  {
    id: "1",
    name: "Michael Scott",
    role: "Regional Manager",
    avatar: "https://picsum.photos/id/1011/40/40",
    fallback: "MS",
    requestType: "role_change",
    department: "Sales",
    requestDate: "2 hours ago",
    priority: "high"
  },
  {
    id: "2",
    name: "Dwight Schrute",
    role: "Senior Salesman",
    avatar: "https://picsum.photos/id/1012/40/40",
    fallback: "DS",
    requestType: "access",
    department: "Sales",
    requestDate: "1 day ago",
    priority: "medium"
  },
  {
    id: "3",
    name: "Pam Beesly",
    role: "Office Administrator",
    avatar: "https://picsum.photos/id/1013/40/40",
    fallback: "PB",
    requestType: "new_user",
    department: "Administration",
    requestDate: "3 days ago",
    priority: "low"
  },
];

export default function PendingApprovalsCard() {
  const [processingStates, setProcessingStates] = React.useState<{ [key: string]: 'idle' | 'approving' | 'denying' | 'approved' | 'denied' }>({});
  const [celebrationStates, setCelebrationStates] = React.useState<{ [key: string]: boolean }>({});
  const { createConfetti } = createCelebrationToast();
  
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 hover:bg-red-150 animate-pulse';
      case 'medium': return 'bg-yellow-100 text-yellow-800 hover:bg-yellow-150';
      case 'low': return 'bg-green-100 text-green-800 hover:bg-green-150';
      default: return 'bg-gray-100 text-gray-800 hover:bg-gray-150';
    }
  };

  const getRequestTypeLabel = (type: string) => {
    switch (type) {
      case 'access': return 'Access Request';
      case 'role_change': return 'Role Change';
      case 'new_user': return 'New User';
      default: return 'Request';
    }
  };
  
  const handleApproval = async (approvalId: string, action: 'approve' | 'deny') => {
    const processingState = action === 'approve' ? 'approving' : 'denying';
    const completedState = action === 'approve' ? 'approved' : 'denied';
    
    // Set processing state
    setProcessingStates(prev => ({ ...prev, [approvalId]: processingState }));
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Set completed state
    setProcessingStates(prev => ({ ...prev, [approvalId]: completedState }));
    
    if (action === 'approve') {
      // Trigger celebration
      setCelebrationStates(prev => ({ ...prev, [approvalId]: true }));
      createConfetti();
      
      // Reset celebration after animation
      setTimeout(() => {
        setCelebrationStates(prev => ({ ...prev, [approvalId]: false }));
      }, 2000);
    }
    
    // Remove from list after celebration
    setTimeout(() => {
      setProcessingStates(prev => {
        const newState = { ...prev };
        delete newState[approvalId];
        return newState;
      });
    }, action === 'approve' ? 3000 : 2000);
  };

  return (
    <Card className="card-hover shadow-soft">
      <CardHeader className="bg-gradient-to-r from-orange-50 to-pink-50 border-b">
        <CardTitle className="gradient-text text-xl flex items-center gap-2">
          <UserPlus className="w-5 h-5" />
          Pending Approvals
        </CardTitle>
        <CardDescription className="text-muted-foreground/80">
          Review and approve pending user requests and access changes
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {approvals.map((approval, index) => (
            <div key={approval.id} className={`transition-all duration-300 ${
              processingStates[approval.id] === 'approved' ? 'animate-fade-out' : ''
            } ${
              processingStates[approval.id] === 'denied' ? 'opacity-50 animate-slide-out' : ''
            }`}>
              <div className={`p-4 rounded-lg border transition-all duration-300 ${
                celebrationStates[approval.id] 
                  ? 'bg-gradient-to-r from-green-50 via-emerald-50 to-green-50 border-green-200 shadow-lg animate-bounce-gentle'
                  : processingStates[approval.id] === 'approving'
                  ? 'bg-gradient-to-r from-orange-50 via-yellow-50 to-orange-50 border-orange-200 animate-pulse'
                  : processingStates[approval.id] === 'denying'
                  ? 'bg-gradient-to-r from-red-50 to-pink-50 border-red-200'
                  : 'bg-gradient-to-r from-white to-gray-50/30 hover:from-gray-50 hover:to-gray-100/50 hover:shadow-lg hover:-translate-y-1'
              }`}>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <Avatar className="w-12 h-12">
                      <AvatarImage
                        src={approval.avatar}
                        data-ai-hint={
                          approval.name.includes("Scott")
                            ? "man face"
                            : approval.name.includes("Schrute")
                            ? "person face"
                            : "woman face"
                        }
                      />
                      <AvatarFallback className="font-semibold">{approval.fallback}</AvatarFallback>
                    </Avatar>
                    <div className="space-y-2">
                      <div>
                        <p className="font-semibold text-foreground">{approval.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {approval.role} • {approval.department}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className={getPriorityColor(approval.priority)}>
                          {approval.priority.toUpperCase()} PRIORITY
                        </Badge>
                        <Badge variant="outline">
                          {getRequestTypeLabel(approval.requestType)}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Clock className="w-3 h-3" />
                        Requested {approval.requestDate}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant={processingStates[approval.id] === 'denying' ? 'loading' : 'outline'}
                      size="sm" 
                      className="h-9 w-20 text-xs hover:bg-red-50 hover:text-red-600 hover:border-red-200 hover:animate-wiggle"
                      onClick={() => handleApproval(approval.id, 'deny')}
                      disabled={!!processingStates[approval.id]}
                    >
                      {processingStates[approval.id] === 'denying' ? (
                        'Processing...'
                      ) : processingStates[approval.id] === 'denied' ? (
                        <>✓ Denied</>
                      ) : (
                        <>
                          <X className="h-3 w-3 mr-1" />
                          Deny
                        </>
                      )}
                    </Button>
                    <Button 
                      variant={processingStates[approval.id] === 'approving' ? 'loading' : 'celebration'}
                      size="sm" 
                      className={`h-9 w-20 text-xs transition-all duration-300 ${
                        celebrationStates[approval.id] ? 'success-celebration active' : ''
                      } ${
                        processingStates[approval.id] === 'approved' ? 'bg-green-500 hover:bg-green-600' : ''
                      }`}
                      onClick={() => handleApproval(approval.id, 'approve')}
                      disabled={!!processingStates[approval.id]}
                    >
                      {processingStates[approval.id] === 'approving' ? (
                        'Processing...'
                      ) : processingStates[approval.id] === 'approved' ? (
                        <>
                          <Sparkles className="h-3 w-3 mr-1" />
                          Approved!
                        </>
                      ) : (
                        <>
                          <Check className="h-3 w-3 mr-1" />
                          Approve
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
              {index < approvals.length - 1 && <div className="my-2" />}
            </div>
          ))}
        </div>
        <div className="pt-4 border-t mt-6">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {approvals.length} pending requests
            </p>
            <Button variant="outline" size="sm">View All Requests</Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}