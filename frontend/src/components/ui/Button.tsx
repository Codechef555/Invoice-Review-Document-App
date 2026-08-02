import type { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  children: ReactNode
}

export function Button({
  variant = 'primary',
  size = 'md',
  className = '',
  children,
  ...props
}: ButtonProps) {
  const baseStyles =
    'inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-950 disabled:pointer-events-none disabled:opacity-50 cursor-pointer rounded-lg'

  const variants = {
    primary: 'bg-zinc-900 text-white hover:bg-zinc-800 active:bg-zinc-950',
    secondary: 'bg-zinc-100 text-zinc-900 hover:bg-zinc-200 active:bg-zinc-300',
    outline: 'border border-zinc-300 bg-white text-zinc-900 hover:bg-zinc-50 active:bg-zinc-100',
    ghost: 'text-zinc-700 hover:bg-zinc-100 hover:text-zinc-900',
    danger: 'bg-red-600 text-white hover:bg-red-700 active:bg-red-800',
  }

  const sizes = {
    sm: 'h-8 px-3 text-xs',
    md: 'h-10 px-4 text-sm',
    lg: 'h-12 px-6 text-base',
  }

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
