import React from 'react';
import { cn } from './Button';

export const Badge = ({ className, variant = 'neutral', ...props }) => {
  const variants = {
    primary: 'bg-brand-primary/10 text-brand-primary border-brand-primary/40',
    success: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/40',
    warning: 'bg-amber-500/10 text-amber-500 border-amber-500/40',
    danger: 'bg-brand-alert/10 text-brand-alert border-brand-alert/40',
    neutral: 'bg-white/10 text-brand-muted border-white/20',
  };

  return (
    <div
      className={cn(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors',
        variants[variant],
        className
      )}
      {...props}
    />
  );
};
