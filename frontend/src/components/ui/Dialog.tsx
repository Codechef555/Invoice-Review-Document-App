import type { ReactNode } from 'react'

interface DialogProps {
  open: boolean
  onClose: () => void
  children: ReactNode
}

export function Dialog({ open, onClose, children }: DialogProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        tabIndex={-1}
        role="presentation"
        className="fixed inset-0 bg-zinc-950/40 backdrop-blur-xs transition-opacity"
        onClick={onClose}
        onKeyDown={(e) => {
          if (e.key === 'Escape') onClose()
        }}
      />
      <div className="relative z-10 w-full max-w-lg rounded-xl border border-zinc-200 bg-white p-6 shadow-xl">
        {children}
      </div>
    </div>
  )
}
