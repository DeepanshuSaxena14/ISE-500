import React from 'react';
import { Settings as SettingsIcon, Shield, Bell, Database, Cpu, Lock } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';

const SettingSection = ({ icon: Icon, title, description, children }) => (
  <div className="flex gap-8 py-8 border-b border-brand-border last:border-0">
    <div className="w-64 shrink-0">
      <div className="flex items-center gap-2 mb-1">
        <Icon className="w-4 h-4 text-brand-primary" />
        <h3 className="font-bold text-white uppercase tracking-tight">{title}</h3>
      </div>
      <p className="text-sm text-brand-muted">{description}</p>
    </div>
    <div className="flex-1 max-w-xl">
      {children}
    </div>
  </div>
);

export default function Settings() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-1">System Settings</h1>
        <p className="text-brand-muted">Configure fleet telemetry and AI optimization parameters.</p>
      </div>

      <Card className="px-8 bg-brand-bg/50 border-brand-border">
        <SettingSection 
          icon={Database} 
          title="FastAPI Integration" 
          description="Configure your backend endpoint and WebSocket bridge."
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs uppercase text-brand-muted font-bold">Base API URL</label>
                <Input defaultValue="http://localhost:8000/api/v1" />
              </div>
              <div className="space-y-2">
                <label className="text-xs uppercase text-brand-muted font-bold">WebSocket URL</label>
                <Input defaultValue="ws://localhost:8000/ws" />
              </div>
            </div>
            <Button size="sm">Update Bridge</Button>
          </div>
        </SettingSection>

        <SettingSection 
          icon={Cpu} 
          title="AI Optimization" 
          description="Adjust the threshold for dispatch recommendations."
        >
          <div className="space-y-6">
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <label className="text-xs uppercase text-brand-muted font-bold">Confidence Threshold</label>
                <Badge variant="primary">85%</Badge>
              </div>
              <div className="h-1.5 w-full bg-brand-border rounded-full overflow-hidden">
                <div className="h-full bg-brand-primary w-[85%]" />
              </div>
              <p className="text-[10px] text-brand-muted italic">
                Higher threshold results in fewer but more optimal recommendations.
              </p>
            </div>
          </div>
        </SettingSection>

        <SettingSection 
          icon={Bell} 
          title="Notifications" 
          description="Set priority levels for automated fleet alerts."
        >
          <div className="space-y-4">
            {['Critical Engine Failure', 'Route Over-capacity', 'Weather Impact'].map((id) => (
              <div key={id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-brand-border">
                 <span className="text-sm text-white font-medium">{id}</span>
                 <div className="w-10 h-5 bg-brand-primary rounded-full relative">
                   <div className="absolute right-1 top-1 w-3 h-3 bg-black rounded-full" />
                 </div>
              </div>
            ))}
          </div>
        </SettingSection>

        <SettingSection 
          icon={Shield} 
          title="Security" 
          description="Manage encryption and telematics access keys."
        >
          <Button variant="secondary" className="gap-2">
            <Lock className="w-4 h-4" />
            Rotate API Keys
          </Button>
        </SettingSection>
      </Card>

      <div className="flex justify-end gap-3 pb-8">
        <Button variant="ghost">Reset Defaults</Button>
        <Button className="px-8">Save Changes</Button>
      </div>
    </div>
  );
}
