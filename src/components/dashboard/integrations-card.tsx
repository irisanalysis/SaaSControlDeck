import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const integrations = [
  { name: 'Slack', description: 'Team communication', status: 'connected' },
  { name: 'Google Drive', description: 'File storage', status: 'syncing' },
  { name: 'Jira', description: 'Project management', status: 'disconnected' },
  { name: 'GitHub', description: 'Code hosting', status: 'connected' },
];

const StatusIndicator = ({ status }: { status: string }) => {
  const baseClasses = "flex items-center gap-2 text-sm capitalize";
  const dotClasses = "h-2 w-2 rounded-full";

  if (status === 'connected') {
    return <div className={baseClasses}><span className={`${dotClasses} bg-green-500`}></span>{status}</div>;
  }
  if (status === 'syncing') {
    return <div className={baseClasses}><span className={`${dotClasses} bg-yellow-500 animate-pulse`}></span>{status}</div>;
  }
  return <div className={baseClasses}><span className={`${dotClasses} bg-gray-400`}></span>{status}</div>;
};

const IntegrationsCard = () => {
  const iconSvgs: { [key: string]: React.ReactNode } = {
    Slack: <svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" className="h-8 w-8"><title>Slack</title><path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52h2.522a2.527 2.527 0 0 1 2.521 2.52v6.313A2.527 2.527 0 0 1 11.356 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.835 5.042a2.528 2.528 0 0 1 2.521-2.52A2.528 2.528 0 0 1 13.878 5.042a2.527 2.527 0 0 1-2.522 2.52H8.835v-2.52zM8.835 6.313a2.527 2.527 0 0 1-2.52 2.521v2.522a2.527 2.527 0 0 1-2.521 2.52H0a2.527 2.527 0 0 1-2.52-2.521V8.835A2.527 2.527 0 0 1 0 6.313h8.835zM18.956 8.835a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.835a2.528 2.528 0 0 1-2.522 2.52h-2.522V8.835zM17.687 8.835a2.528 2.528 0 0 1-2.523 2.52h-2.52a2.528 2.528 0 0 1-2.523-2.52V2.522A2.528 2.528 0 0 1 12.642 0a2.528 2.528 0 0 1 2.523 2.522v6.313zM15.165 18.956a2.528 2.528 0 0 1-2.52 2.522A2.528 2.528 0 0 1 10.122 18.956a2.528 2.528 0 0 1 2.523-2.52h2.52v2.52zM15.165 17.687a2.528 2.528 0 0 1 2.52-2.523h2.522a2.528 2.528 0 0 1 2.52 2.523v2.52a2.528 2.528 0 0 1-2.52 2.522H15.165v-2.52z" fill="currentColor"/></svg>,
    'Google Drive': <svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" className="h-8 w-8"><title>Google Drive</title><path d="M14.909 15.111 8.636 4.637l-6.273 10.474h12.546zM16.364 16.526h7.527L17.618 8.013l-7.527 12.54h6.273zM7.227 16.526 3.136 24h15.455l4.09-6.818H7.227z" fill="currentColor"/></svg>,
    Jira: <svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" className="h-8 w-8"><title>Jira</title><path d="M22.182.237 12.27 10.15l-9.91-9.913C1.65-.575 0 1.063 0 1.83v20.34C0 23.376 1.48 24 2.11 24c.63 0 2.113-1.218 2.113-1.218l9.823-9.824 9.912 9.912c.712.71 2.35.238 2.35.238s.944-.71.944-1.577V1.83c0-1.22-.856-1.92-1.57-1.592Z" fill="currentColor"/></svg>,
    GitHub: <svg role="img" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" className="h-8 w-8"><title>GitHub</title><path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297 24 5.67 18.63 0 12 .297z" fill="currentColor"/></svg>,
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Integrations</CardTitle>
        <CardDescription>Connect and manage third-party applications.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {integrations.map((integration) => (
            <Card key={integration.name} className="flex items-center p-4 gap-4">
              <div className="text-muted-foreground">{iconSvgs[integration.name]}</div>
              <div className="flex-1 space-y-1">
                <p className="font-semibold">{integration.name}</p>
                <p className="text-sm text-muted-foreground">{integration.description}</p>
                <StatusIndicator status={integration.status} />
              </div>
              <Button variant="outline" size="sm">Manage</Button>
            </Card>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default IntegrationsCard;
