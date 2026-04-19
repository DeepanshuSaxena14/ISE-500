import React, { useState, useEffect } from 'react';
import { FileText, Calendar, Download, Share2, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { briefingService } from '../api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

export default function Briefings() {
  const [briefing, setBriefing] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    briefingService.getDailyBriefing().then(data => {
      setBriefing(data);
      setLoading(false);
    });
  }, []);

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up': return <TrendingUp className="text-emerald-500 w-4 h-4" />;
      case 'down': return <TrendingDown className="text-brand-alert w-4 h-4" />;
      default: return <Minus className="text-brand-muted w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-1">Ops Briefing</h1>
          <p className="text-brand-muted">AI-generated daily summary of fleet performance and risks.</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="gap-2">
            <Download className="w-4 h-4" />
            PDF Export
          </Button>
          <Button variant="outline" className="gap-2">
            <Share2 className="w-4 h-4" />
            Distribute
          </Button>
        </div>
      </div>

      {loading ? (
        <Card className="h-96 animate-pulse bg-white/5" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <Card className="lg:col-span-2 p-8 space-y-6">
            <div className="flex items-center gap-4 text-brand-primary">
              <Calendar className="w-6 h-6" />
              <h2 className="text-xl font-bold uppercase tracking-widest">{briefing.date}</h2>
            </div>
            
            <div className="prose prose-invert max-w-none">
              <p className="text-lg leading-relaxed text-white font-medium italic">
                "{briefing.summary}"
              </p>
            </div>

            <div className="pt-6 border-t border-brand-border space-y-4">
              <h3 className="text-sm font-semibold uppercase text-brand-muted tracking-widest">Key Insights</h3>
              <ul className="space-y-4">
                <li className="flex gap-4">
                  <div className="w-2 h-2 rounded-full bg-brand-primary mt-1.5 shrink-0" />
                  <p className="text-sm text-brand-muted">Fuel consumption optimized significantly on North Route #4 following AI adjustment.</p>
                </li>
                <li className="flex gap-4">
                  <div className="w-2 h-2 rounded-full bg-brand-primary mt-1.5 shrink-0" />
                  <p className="text-sm text-brand-muted">Upcoming weather pattern in Midwest (May 22) requires pre-emptive route re-assignment.</p>
                </li>
              </ul>
            </div>
          </Card>

          <div className="space-y-6">
            <h3 className="text-sm font-semibold uppercase text-brand-muted tracking-widest px-2">Performance KPIs</h3>
            {briefing.keyMetrics.map((metric, i) => (
              <Card key={i} className="p-6 flex justify-between items-center">
                <div>
                  <p className="text-xs text-brand-muted uppercase font-medium mb-1">{metric.label}</p>
                  <p className="text-2xl font-bold text-white">{metric.value}</p>
                </div>
                <div className="p-3 bg-white/5 rounded-xl">
                  {getTrendIcon(metric.trend)}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
