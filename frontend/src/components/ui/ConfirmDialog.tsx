import { Button } from './Button'
import { Dialog } from './Dialog'

interface ConfirmDialogProps {
  open: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  onConfirm: () => void
  onClose: () => void
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onClose,
}: ConfirmDialogProps) {
  return (
    <Dialog open={open} onClose={onClose}>
      <h2 className="text-lg font-semibold text-zinc-950">{title}</h2>
      <p className="mt-2 text-sm text-zinc-600">{message}</p>
      <div className="mt-6 flex justify-end gap-3">
        <Button variant="outline" onClick={onClose}>
          {cancelText}
        </Button>
        <Button
          variant="danger"
          onClick={() => {
            onConfirm()
            onClose()
          }}
        >
          {confirmText}
        </Button>
      </div>
    </Dialog>
  )
}
