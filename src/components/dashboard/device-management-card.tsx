import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Smartphone, Monitor, Tablet } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

const devices = [
  { type: 'Desktop', icon: <Monitor className="h-5 w-5"/>, location: 'New York, USA', lastActivity: '2 minutes ago', current: true },
  { type: 'Mobile', icon: <Smartphone className="h-5 w-5"/>, location: 'London, UK', lastActivity: '1 hour ago', current: false },
  { type: 'Tablet', icon: <Tablet className="h-5 w-5"/>, location: 'Tokyo, Japan', lastActivity: '5 hours ago', current: false },
];

const DeviceManagementCard = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Device Management</CardTitle>
        <CardDescription>Manage your active sessions across all devices.</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Device</TableHead>
              <TableHead className="hidden sm:table-cell">Location</TableHead>
              <TableHead>Last Activity</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {devices.map((device, index) => (
              <TableRow key={index}>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {device.icon}
                    <div className="flex flex-col">
                      <span className="font-medium">{device.type}</span>
                      {device.current && <Badge variant="secondary" className="w-fit text-green-600">Current</Badge>}
                    </div>
                  </div>
                </TableCell>
                <TableCell className="hidden sm:table-cell">{device.location}</TableCell>
                <TableCell>{device.lastActivity}</TableCell>
                <TableCell className="text-right">
                  {!device.current && <Button variant="destructive" size="sm">Terminate</Button>}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};

export default DeviceManagementCard;
