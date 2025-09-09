import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function SettingsCard() {
  return (
    <Card className="card-hover shadow-soft">
      <CardHeader className="bg-gradient-to-r from-orange-50 to-pink-50 border-b">
        <CardTitle className="gradient-text text-xl">Settings & Preferences</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <Tabs defaultValue="personal" className="w-full">
          <TabsList className="grid w-full grid-cols-5 m-6 mb-0">
            <TabsTrigger value="personal" className="text-xs">Personal</TabsTrigger>
            <TabsTrigger value="security" className="text-xs">Security</TabsTrigger>
            <TabsTrigger value="team" className="text-xs">Team</TabsTrigger>
            <TabsTrigger value="billing" className="text-xs">Billing</TabsTrigger>
            <TabsTrigger value="notifications" className="text-xs">Notifications</TabsTrigger>
          </TabsList>
          <TabsContent value="personal" className="p-6">
            <div className="space-y-6">
              <div className="space-y-2">
                <h3 className="text-lg font-medium">Contact Information</h3>
                <p className="text-sm text-muted-foreground">
                  Update your contact details.
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" defaultValue="johndoe@example.com" />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="phone">Phone</Label>
                  <Input id="phone" type="tel" defaultValue="+1 (555) 123-4567" />
                </div>
              </div>
              <Separator />
              <Button className="btn-gradient">Save Changes</Button>
            </div>
          </TabsContent>
          <TabsContent value="security" className="p-6">
            <div className="space-y-6">
              <div className="space-y-2">
                <h3 className="text-lg font-medium">Password</h3>
                <p className="text-sm text-muted-foreground">
                  Change your password.
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                    <Label htmlFor="current-password">Current Password</Label>
                    <Input id="current-password" type="password" />
                </div>
                <div className="space-y-1.5">
                    <Label htmlFor="new-password">New Password</Label>
                    <Input id="new-password" type="password" />
                </div>
              </div>
              <Separator />
              <div className="space-y-4">
                <h3 className="text-lg font-medium">Two-Factor Authentication</h3>
                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div>
                    <h4 className="font-medium">Enable 2FA</h4>
                    <p className="text-sm text-muted-foreground">
                      Add an extra layer of security to your account.
                    </p>
                  </div>
                  <Switch />
                </div>
              </div>
              <Separator />
              <Button className="btn-gradient">Update Security</Button>
            </div>
          </TabsContent>
          <TabsContent value="team" className="p-6">
            <div className="space-y-6">
              <div className="space-y-2">
                <h3 className="text-lg font-medium">Team Management</h3>
                <p className="text-sm text-muted-foreground">
                  Manage your team settings and permissions.
                </p>
              </div>
              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div>
                    <h4 className="font-medium">Team Collaboration</h4>
                    <p className="text-sm text-muted-foreground">
                      Allow team members to collaborate on projects.
                    </p>
                  </div>
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div>
                    <h4 className="font-medium">Auto-approve Invitations</h4>
                    <p className="text-sm text-muted-foreground">
                      Automatically approve team invitations.
                    </p>
                  </div>
                  <Switch />
                </div>
              </div>
              <Separator />
              <Button className="btn-gradient">Update Team Settings</Button>
            </div>
          </TabsContent>
          <TabsContent value="billing" className="p-6">
            <div className="space-y-6">
              <div className="space-y-2">
                <h3 className="text-lg font-medium">Billing Information</h3>
                <p className="text-sm text-muted-foreground">
                  Manage your subscription and billing details.
                </p>
              </div>
              <div className="rounded-lg border p-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h4 className="font-medium">Current Plan: Enterprise</h4>
                    <p className="text-sm text-muted-foreground">$99/month - Next billing: Jan 15, 2024</p>
                  </div>
                  <Button variant="outline">Change Plan</Button>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Users</span>
                    <span>15/25</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Storage</span>
                    <span>128GB/500GB</span>
                  </div>
                </div>
              </div>
              <Separator />
              <Button className="btn-gradient">Manage Billing</Button>
            </div>
          </TabsContent>
          <TabsContent value="notifications" className="p-6">
            <div className="space-y-6">
                <div>
                    <h3 className="text-lg font-medium">Email Notifications</h3>
                    <p className="text-sm text-muted-foreground">
                        Manage your email notification preferences.
                    </p>
                </div>
                <div className="space-y-4">
                    <div className="flex items-start gap-2">
                        <Checkbox id="marketing" defaultChecked />
                        <div className="grid gap-1.5 leading-none">
                            <label htmlFor="marketing" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                Marketing emails
                            </label>
                            <p className="text-sm text-muted-foreground">
                                Receive emails about new products, features, and promotions.
                            </p>
                        </div>
                    </div>
                    <div className="flex items-start gap-2">
                        <Checkbox id="updates" defaultChecked />
                        <div className="grid gap-1.5 leading-none">
                            <label htmlFor="updates" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                Product updates
                            </label>
                            <p className="text-sm text-muted-foreground">
                                Receive emails about new features and improvements.
                            </p>
                        </div>
                    </div>
                    <div className="flex items-start gap-2">
                        <Checkbox id="security" />
                        <div className="grid gap-1.5 leading-none">
                            <label htmlFor="security" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                Security alerts
                            </label>
                            <p className="text-sm text-muted-foreground">
                                Receive emails about security-related events.
                            </p>
                        </div>
                    </div>
                </div>
                <Separator />
                <Button className="btn-gradient">Save Notification Preferences</Button>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}