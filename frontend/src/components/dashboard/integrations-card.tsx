import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Github, Slack, GoogleDrive, Jira } from "@/components/icons";

type Status = "connected" | "syncing" | "disconnected";

interface Integration {
  name: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  status: Status;
}

const integrations: Integration[] = [
  { name: "Slack", icon: Slack, status: "connected" },
  { name: "Google Drive", icon: GoogleDrive, status: "syncing" },
  { name: "Jira", icon: Jira, status: "disconnected" },
  { name: "GitHub", icon: Github, status: "connected" },
];

function StatusIndicator({ status }: { status: Status }) {
  const baseClasses = "w-3 h-3 rounded-full shadow-sm";
  if (status === "connected") return (
    <div className="relative">
      <div className={`${baseClasses} bg-green-500`} />
      <div className="absolute inset-0 rounded-full bg-green-400 animate-ping opacity-75" style={{animationDuration: '2s'}} />
    </div>
  );
  if (status === "syncing") return (
    <div className="relative">
      <div className={`${baseClasses} bg-yellow-500 animate-pulse`} />
      <div className="absolute inset-0 rounded-full bg-yellow-400 animate-ping opacity-75" />
    </div>
  );
  return <div className={`${baseClasses} bg-gray-400`} />;
}

export default function IntegrationsCard() {
  return (
    <Card className="card-hover shadow-soft">
      <CardHeader className="bg-gradient-to-r from-green-50 to-blue-50 border-b">
        <CardTitle className="gradient-text text-xl">Service Integrations</CardTitle>
        <CardDescription className="text-muted-foreground/80">Manage your connected third-party services and data sync</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {integrations.map((integration) => (
            <div key={integration.name} className="flex items-center justify-between p-4 rounded-lg border bg-gradient-to-r from-white to-gray-50/50 hover:from-gray-50 hover:to-gray-100/50 transition-all duration-200">
              <div className="flex items-center gap-4">
                <div className="p-2 rounded-lg bg-white shadow-sm border">
                  <integration.icon className="w-5 h-5 text-gray-700" />
                </div>
                <div>
                  <span className="font-medium text-foreground">{integration.name}</span>
                  <div className="text-xs text-muted-foreground">
                    {integration.status === 'connected' && 'Last sync: 2 min ago'}
                    {integration.status === 'syncing' && 'Syncing data...'}
                    {integration.status === 'disconnected' && 'Not connected'}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <StatusIndicator status={integration.status} />
                  <span className={`text-sm font-medium capitalize ${
                    integration.status === 'connected' ? 'text-green-600' :
                    integration.status === 'syncing' ? 'text-yellow-600' :
                    'text-gray-500'
                  }`}>
                    {integration.status}
                  </span>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="h-8 px-3 text-xs"
                >
                  {integration.status === 'disconnected' ? 'Connect' : 'Manage'}
                </Button>
              </div>
            </div>
          ))}
        </div>
        <div className="flex gap-3 mt-6 pt-4 border-t">
          <Button className="btn-gradient flex-1">Add New Integration</Button>
          <Button variant="outline" className="flex-1">Sync All Services</Button>
        </div>
      </CardContent>
    </Card>
  );
}
