import type { ReactNode } from 'react'

interface DocumentReviewSectionProps {
  title: string
  subtitle?: string
  action?: ReactNode
  children: ReactNode
}

export function DocumentReviewSection({
  title,
  subtitle,
  action,
  children,
}: DocumentReviewSectionProps) {
  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 shadow-xs">
      <div className="flex items-start justify-between gap-4 border-b border-zinc-100 pb-4">
        <div>
          <h2 className="text-base font-semibold text-zinc-900">{title}</h2>
          {subtitle && <p className="mt-1 text-xs text-zinc-500">{subtitle}</p>}
        </div>
        {action && <div>{action}</div>}
      </div>
      <div className="pt-4">{children}</div>
    </section>
  )
}
