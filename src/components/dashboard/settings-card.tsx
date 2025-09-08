"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Globe, KeyRound, Users, CreditCard, Bell } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const SettingsCard = () => {
    const { toast } = useToast();

    const handleSaveChanges = () => {
        toast({
            title: 'Settings Saved',
            description: 'Your changes have been saved successfully.',
        });
    }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Settings</CardTitle>
        <CardDescription>Manage your account settings and preferences.</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="personal" className="w-full">
          <TabsList className="grid w-full grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-1">
            <TabsTrigger value="personal"><Globe className="mr-2 h-4 w-4"/>Personal Details</TabsTrigger>
            <TabsTrigger value="security"><KeyRound className="mr-2 h-4 w-4"/>Security</TabsTrigger>
            <TabsTrigger value="team"><Users className="mr-2 h-4 w-4"/>Team Management</TabsTrigger>
            <TabsTrigger value="billing"><CreditCard className="mr-2 h-4 w-4"/>Billing</TabsTrigger>
            <TabsTrigger value="notifications"><Bell className="mr-2 h-4 w-4"/>Notifications</TabsTrigger>
          </TabsList>
          <TabsContent value="personal" className="mt-6">
            <div className="space-y-4 max-w-md">
              <div className="space-y-1">
                <Label htmlFor="name">Name</Label>
                <Input id="name" defaultValue="Jane Doe" />
              </div>
              <div className="space-y-1">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" defaultValue="jane.doe@example.com" />
              </div>
              <Button onClick={handleSaveChanges}>Save changes</Button>
            </div>
          </TabsContent>
          <TabsContent value="security" className="mt-6">
            <div className="space-y-6 max-w-md">
                <div>
                    <h4 className="font-medium">Change Password</h4>
                    <div className="space-y-2 mt-2">
                        <div className="space-y-1">
                            <Label htmlFor="current-password">Current Password</Label>
                            <Input id="current-password" type="password" />
                        </div>
                        <div className="space-y-1">
                            <Label htmlFor="new-password">New Password</Label>
                            <Input id="new-password" type="password" />
                        </div>
                    </div>
                </div>
                 <div>
                    <h4 className="font-medium">Two-Factor Authentication</h4>
                    <div className="flex items-center space-x-2 mt-2">
                        <Switch id="2fa-switch" />
                        <Label htmlFor="2fa-switch">Enable 2FA</Label>
                    </div>
                 </div>
              <Button onClick={handleSaveChanges}>Save Security Settings</Button>
            </div>
          </TabsContent>
          <TabsContent value="team" className="mt-6">
             <p className="text-sm text-muted-foreground">Manage your team members, roles, and permissions.</p>
          </TabsContent>
          <TabsContent value="billing" className="mt-6">
             <p className="text-sm text-muted-foreground">Manage your billing information, subscription plan, and view invoices.</p>
          </TabsContent>
          <TabsContent value="notifications" className="mt-6">
             <p className="text-sm text-muted-foreground">Configure your notification preferences for email, SMS, and in-app alerts.</p>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default SettingsCard;
