import React, { useState, useEffect } from 'react';
import { ShieldAlert, Info, AlertTriangle, CheckCircle2, MoreVertical } from 'lucide-react';
import { alertService } from '../api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    alertService.getAlerts().then(data => {
      setAlerts(data);
      setLoading(false);
    });
  }, []);

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return <ShieldAlert className="text-brand-alert" />;
      case 'high': return <AlertTriangle className="text-amber-500" />;
      case 'medium': return <Info className="text-blue-400" />;
      default: return <CheckCircle2 className="text-emerald-500" />;
    }
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'critical': return <Badge variant="danger" className="uppercase font-black animate-pulse">Critical Fail</Badge>;
      case 'high': return <Badge variant="warning" className="uppercase">High Priority</Badge>;
      case 'medium': return <Badge variant="primary" className="uppercase">Notice</Badge>;
      default: return <Badge variant="success" className="uppercase">Standard</Badge>;
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-1">System Alerts</h1>
          <p className="text-brand-muted">Real-time telematics alerts and critical notifications.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" size="sm">Filter By Severity</Button>
          <Button size="sm">Acknowledge All</Button>
        </div>
      </div>

      <div className="space-y-4">
        {loading ? (
          [1, 2, 3].map(i => <Card key={i} className="h-24 animate-pulse bg-white/5" />)
        ) : (
          alerts.map((alert) => (
            <Card key={alert.id} className="p-0 border-l-4 border-l-brand-alert overflow-hidden group">
              <div className="flex items-center p-6 gap-6">
                <div className="p-3 bg-white/5 rounded-xl group-hover:scale-110 transition-transform">
                  {getSeverityIcon(alert.severity)}
                </div>
                
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-3">
                    <h3 className="font-bold text-lg text-white">{alert.title}</h3>
                    {getSeverityBadge(alert.severity)}
                  </div>
                  <p className="text-sm text-brand-muted">{alert.description}</p>
                </div>

                <div className="text-right shrink-0">
                  <p className="text-xs text-brand-muted uppercase font-mono mb-2">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </p>
                  <div className="flex gap-2">
                    <Button variant="secondary" size="sm">Resolve</Button>
                    <Button variant="ghost" size="sm" className="px-2">
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      <Card className="p-8 bg-brand-primary/5 border-brand-primary/20 border-dashed">
        <div className="flex gap-6 items-center">
          <div className="w-12 h-12 bg-brand-primary/20 rounded-full flex items-center justify-center">
            <CheckCircle2 className="text-brand-primary w-6 h-6" />
          </div>
          <div>
            <h4 className="font-bold text-white">All other systems reporting optimal</h4>
            <p className="text-sm text-brand-muted italic">Telematics link established via satellite. Heartbeat stable.</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
