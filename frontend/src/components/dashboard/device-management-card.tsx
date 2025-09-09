import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { Laptop, Smartphone, Tablet, MoreHorizontal, Shield, MapPin, Clock, AlertTriangle, Eye } from 'lucide-react';
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const deviceIcons = {
  desktop: <Laptop className="w-6 h-6" />,
  mobile: <Smartphone className="w-6 h-6" />,
  tablet: <Tablet className="w-6 h-6" />,
};

type Device = {
  id: string;
  type: keyof typeof deviceIcons;
  location: string;
  lastActive: string;
  isCurrent: boolean;
  browser?: string;
  ip?: string;
  trusted?: boolean;
};

const devices: Device[] = [
  { id: '1', type: 'desktop', location: 'New York, US', lastActive: '2 hours ago', isCurrent: true, browser: 'Chrome 120', ip: '192.168.1.100', trusted: true },
  { id: '2', type: 'mobile', location: 'London, UK', lastActive: '1 day ago', isCurrent: false, browser: 'Safari Mobile', ip: '10.0.0.45', trusted: true },
  { id: '3', type: 'tablet', location: 'Tokyo, JP', lastActive: '3 days ago', isCurrent: false, browser: 'Firefox 118', ip: '203.0.113.1', trusted: false },
  { id: '4', type: 'desktop', location: 'Sydney, AU', lastActive: '1 week ago', isCurrent: false, browser: 'Edge 119', ip: '198.51.100.12', trusted: true },
];

export default function DeviceManagementCard() {
  return (
    <Card className="card-hover shadow-soft">
      <CardHeader className="bg-gradient-to-r from-red-50 to-orange-50 border-b">
        <CardTitle className="gradient-text text-xl flex items-center gap-2">
          <Shield className="w-5 h-5" />
          Device & Security Management
        </CardTitle>
        <CardDescription className="text-muted-foreground/80">
          Monitor active sessions and manage device access to your account
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {devices.map((device) => (
            <div key={device.id} className="p-4 rounded-lg border bg-gradient-to-r from-white to-gray-50/30 hover:from-gray-50 hover:to-gray-100/50 transition-all duration-200">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-lg ${device.isCurrent ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                    {deviceIcons[device.type]}
                  </div>
                  <div className="space-y-1">
                    <div className="font-semibold flex items-center gap-2">
                      {device.type.charAt(0).toUpperCase() + device.type.slice(1)}
                      {device.isCurrent && (
                        <Badge variant="default" className="bg-green-100 text-green-800 hover:bg-green-100">
                          Current Session
                        </Badge>
                      )}
                      {!device.trusted && (
                        <Badge variant="destructive" className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">
                          <AlertTriangle className="w-3 h-3 mr-1" />
                          Unverified
                        </Badge>
                      )}
                    </div>
                    <div className="text-sm text-muted-foreground space-y-1">
                      <div className="flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        {device.location}
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        Last active {device.lastActive}
                      </div>
                      {device.browser && (
                        <div className="flex items-center gap-1">
                          <Eye className="w-3 h-3" />
                          {device.browser} • {device.ip}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem className="flex items-center gap-2">
                      <Eye className="w-4 h-4" />
                      View Details
                    </DropdownMenuItem>
                    {!device.trusted && (
                      <DropdownMenuItem className="flex items-center gap-2">
                        <Shield className="w-4 h-4" />
                        Mark as Trusted
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuSeparator />
                    <DropdownMenuItem className="text-red-600 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4" />
                      Terminate Session
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          ))}
        </div>
        <Separator className="my-6" />
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            {devices.filter(d => d.trusted).length} of {devices.length} devices are trusted
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">Security Settings</Button>
            <Button className="btn-gradient" size="sm">Revoke All Sessions</Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
