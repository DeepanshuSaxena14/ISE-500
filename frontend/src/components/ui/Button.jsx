import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export const Button = React.forwardRef(({ className, variant = 'primary', size = 'md', ...props }, ref) => {
  const variants = {
    primary: 'bg-brand-primary text-black hover:bg-brand-primary/90 shadow-[0_0_10px_rgba(20,184,166,0.2)]',
    secondary: 'bg-brand-card text-white hover:bg-white/10 border border-brand-border',
    outline: 'bg-transparent border border-brand-primary text-brand-primary hover:bg-brand-primary/10',
    danger: 'bg-brand-alert text-white hover:bg-brand-alert/90',
    ghost: 'bg-transparent hover:bg-white/5 text-brand-muted hover:text-white',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      ref={ref}
      className={cn(
        'inline-flex items-center justify-center rounded-lg font-medium transition-all focus:outline-none focus:ring-2 focus:ring-brand-primary/50 disabled:opacity-50 disabled:pointer-events-none active:scale-95',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  );
});

Button.displayName = 'Button';
