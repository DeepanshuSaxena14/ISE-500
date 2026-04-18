import React from 'react';
import { Search, Bell, HelpCircle } from 'lucide-react';
import { Input } from './ui/Input';
import { Button } from './ui/Button';

export function TopBar() {
  return (
    <header className="h-14 border-b border-brand-border bg-brand-bg flex items-center justify-between px-6 sticky top-0 z-10 transition-all duration-300">
      <div className="flex-1 max-w-xl">
        <div className="relative group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-brand-muted group-focus-within:text-brand-primary transition-colors" />
          <Input 
            placeholder="Global search — drivers, loads, routes..." 
            className="pl-10 py-1.5 h-9 bg-white/[0.03] border-brand-border/50 w-[320px] focus:w-[420px] focus:bg-white/[0.05] transition-all duration-300 text-[13px] rounded-lg"
          />
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" className="relative text-brand-muted hover:text-white">
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-brand-alert rounded-full animate-pulse" />
          </Button>
          <Button variant="ghost" size="sm" className="text-brand-muted hover:text-white">
            <HelpCircle className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="h-6 w-[1px] bg-brand-border" />
        
        <div className="flex items-center gap-3 pr-2">
          <div className="text-right">
            <div className="flex items-center justify-end gap-1.5">
              <span className="text-[10px] font-bold text-brand-primary tracking-tighter uppercase">Backend: Optimal</span>
              <div className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-pulse" />
            </div>
            <p className="text-[9px] text-brand-muted uppercase tracking-widest font-semibold font-mono">24ms Latency</p>
          </div>
        </div>
      </div>
    </header>
  );
}
