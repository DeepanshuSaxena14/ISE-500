import React from 'react';
import { cn } from './Button';

export const Card = React.forwardRef(({ className, hover = false, glow = false, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'rounded-xl border border-brand-border bg-brand-card text-white shadow-lg transition-all duration-300',
      hover && 'hover:scale-[1.02] hover:border-brand-primary/50 cursor-pointer',
      glow && 'border-brand-primary/30 shadow-[0_0_15px_rgba(20,184,166,0.1)]',
      className
    )}
    {...props}
  />
));
Card.displayName = 'Card';
