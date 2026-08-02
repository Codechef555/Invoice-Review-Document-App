import type { HTMLAttributes, ReactNode } from 'react'

export function Card({
  className = '',
  children,
  ...props
}: HTMLAttributes<HTMLDivElement> & { children: ReactNode }) {
  return (
    <div
      className={`rounded-xl border border-zinc-200 bg-white shadow-xs ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({
  className = '',
  children,
  ...props
}: HTMLAttributes<HTMLDivElement> & { children: ReactNode }) {
  return (
    <div className={`p-6 ${className}`} {...props}>
      {children}
    </div>
  )
}

export function CardContent({
  className = '',
  children,
  ...props
}: HTMLAttributes<HTMLDivElement> & { children: ReactNode }) {
  return (
    <div className={`p-6 pt-0 ${className}`} {...props}>
      {children}
    </div>
  )
}
