import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Zap, 
  MessageSquare, 
  Bell, 
  FileText, 
  Settings,
  Truck
} from 'lucide-react';
import { cn } from './ui/Button';

const navItems = [
  { icon: LayoutDashboard, label: 'Fleet Dashboard', path: '/' },
  { icon: Zap, label: 'Smart Dispatch', path: '/dispatch' },
  { icon: MessageSquare, label: 'AI Assistant', path: '/chat' },
  { icon: Bell, label: 'Alerts', path: '/alerts' },
  { icon: FileText, label: 'Briefings', path: '/briefings' },
  { icon: Settings, label: 'Settings', path: '/settings' },
];

export function Sidebar() {
  return (
    <aside className="w-64 bg-brand-bg border-r border-brand-border flex flex-col h-full">
      <div className="p-6 flex items-center gap-3">
        <div className="w-7 h-7 bg-brand-primary rounded flex items-center justify-center flex-shrink-0">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <rect x="1" y="1" width="5" height="5" rx="1.2" fill="white"/>
            <rect x="8" y="1" width="5" height="5" rx="1.2" fill="white" fillOpacity=".55"/>
            <rect x="1" y="8" width="5" height="5" rx="1.2" fill="white" fillOpacity=".55"/>
            <rect x="8" y="8" width="5" height="5" rx="1.2" fill="white" fillOpacity=".25"/>
          </svg>
        </div>
        <div>
          <div className="text-[13px] font-bold tracking-widest text-white">DISPATCHIQ</div>
          <div className="text-[9px] text-brand-muted uppercase tracking-wider -mt-0.5">Fleet Ops</div>
        </div>
      </div>

      <nav className="flex-1 px-4 py-2 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => cn(
              'flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 group text-[13px]',
              isActive 
                ? 'bg-brand-primary/10 text-brand-primary font-bold' 
                : 'text-brand-muted hover:text-white hover:bg-white/5'
            )}
          >
            <item.icon className={cn(
              "w-4 h-4 transition-colors",
              "group-hover:text-brand-primary"
            )} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-brand-border">
        <div className="flex items-center gap-3 px-3 py-3 rounded-xl bg-white/[0.03] border border-white/[0.05]">
          <div className="w-8 h-8 rounded-lg bg-teal-500/20 text-teal-400 flex items-center justify-center font-bold text-xs">
            OP
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[11px] font-bold text-white truncate uppercase tracking-tight">Ops Manager</p>
            <p className="text-[9px] text-brand-muted truncate uppercase tracking-wider font-semibold">Fleet Alpha-1</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
