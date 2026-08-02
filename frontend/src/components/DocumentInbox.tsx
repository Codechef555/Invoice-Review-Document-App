import { useState } from 'react'
import type { Document } from '../lib/types'
import { StatusBadge } from './StatusBadge'
import { Button } from './ui/Button'
import { ConfirmDialog } from './ui/ConfirmDialog'

interface DocumentInboxProps {
  documents: Document[]
  onSelect: (document: Document) => void
  onDelete: (document: Document) => void
}

export function DocumentInbox({ documents, onSelect, onDelete }: DocumentInboxProps) {
  const [toDelete, setToDelete] = useState<Document | null>(null)

  if (documents.length === 0) {
    return (
      <div className="p-12 text-center text-sm text-zinc-500">
        No documents in history yet. Click &quot;Review another&quot; to upload your first document.
      </div>
    )
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-zinc-100 bg-zinc-50 font-medium text-zinc-500">
            <tr>
              <th className="px-6 py-3">Document</th>
              <th className="px-6 py-3">Supplier</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Uploaded</th>
              <th className="px-6 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {documents.map((doc) => {
              const vendor = doc.review_data?.vendor_name || '—'
              const dateStr = new Date(doc.created_at).toLocaleDateString()

              return (
                <tr key={doc.id} className="hover:bg-zinc-50">
                  <td className="px-6 py-4 font-medium text-zinc-900">{doc.original_filename}</td>
                  <td className="px-6 py-4 text-zinc-600">{vendor}</td>
                  <td className="px-6 py-4">
                    <StatusBadge status={doc.status} />
                  </td>
                  <td className="px-6 py-4 text-zinc-500">{dateStr}</td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-2">
                      <Button size="sm" variant="outline" onClick={() => onSelect(doc)}>
                        View
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setToDelete(doc)}>
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <ConfirmDialog
        open={Boolean(toDelete)}
        title="Delete document"
        message={`Are you sure you want to delete "${toDelete?.original_filename}"? This action cannot be undone.`}
        confirmText="Delete"
        onConfirm={() => {
          if (toDelete) onDelete(toDelete)
        }}
        onClose={() => setToDelete(null)}
      />
    </>
  )
}
