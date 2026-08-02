import { useState } from 'react'
import {
  decideDocument,
  documentFileUrl,
  selectGlAccount,
  updateDocument,
} from '../lib/api'
import type { Document, GlAccount, ReviewData } from '../lib/types'
import { DocumentPreview } from './DocumentPreview'
import { DocumentReviewSection } from './DocumentReviewSection'
import { StatusBadge } from './StatusBadge'
import { Badge } from './ui/Badge'
import { Button } from './ui/Button'

interface DocumentReviewProps {
  document: Document
  accounts: GlAccount[]
  accountsLoading: boolean
  onRetryAccounts: () => void
  onChanged: (updated: Document) => void
}

export function DocumentReview({
  document: doc,
  accounts,
  accountsLoading,
  onRetryAccounts,
  onChanged,
}: DocumentReviewProps) {
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [deciding, setDeciding] = useState(false)
  const [selectingGl, setSelectingGl] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const reviewData = doc.review_data || ({} as Partial<ReviewData>)

  const [formData, setFormData] = useState<Partial<ReviewData>>({
    vendor_name: reviewData.vendor_name || '',
    vendor_vat_id: reviewData.vendor_vat_id || '',
    customer_name: reviewData.customer_name || '',
    customer_vat_id: reviewData.customer_vat_id || '',
    invoice_number: reviewData.invoice_number || '',
    purchase_order: reviewData.purchase_order || '',
    invoice_date: reviewData.invoice_date || '',
    due_date: reviewData.due_date || '',
    currency: reviewData.currency || 'EUR',
    subtotal: reviewData.subtotal ?? '',
    total_tax: reviewData.total_tax ?? '',
    invoice_total: reviewData.invoice_total ?? '',
  })

  const classification = (doc.classification as {
    document_type?: string
    confidence?: number
    reasoning?: string
  } | null)

  const selectedGlCode =
    doc.accounting_coding?.selected_gl_account_code ||
    doc.accounting_coding?.suggestion?.gl_account_code ||
    ''

  const glSuggestion = doc.accounting_coding?.suggestion

  async function handleSaveEdits() {
    setSaving(true)
    setError(null)
    try {
      const updated = await updateDocument(doc.id, {
        document_type: reviewData.document_type || 'invoice',
        vendor_name: formData.vendor_name || null,
        vendor_vat_id: formData.vendor_vat_id || null,
        customer_name: formData.customer_name || null,
        customer_vat_id: formData.customer_vat_id || null,
        invoice_number: formData.invoice_number || null,
        purchase_order: formData.purchase_order || null,
        invoice_date: formData.invoice_date || null,
        due_date: formData.due_date || null,
        currency: formData.currency || 'EUR',
        subtotal: formData.subtotal !== '' ? Number(formData.subtotal) : null,
        total_tax: formData.total_tax !== '' ? Number(formData.total_tax) : null,
        invoice_total: formData.invoice_total !== '' ? Number(formData.invoice_total) : null,
        line_items: reviewData.line_items || [],
      })
      onChanged(updated)
      setEditing(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update document.')
    } finally {
      setSaving(false)
    }
  }

  async function handleSelectGl(code: string) {
    setSelectingGl(true)
    setError(null)
    try {
      const updated = await selectGlAccount(doc.id, code)
      onChanged(updated)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to select GL account.')
    } finally {
      setSelectingGl(false)
    }
  }

  async function handleDecide(decision: 'approved' | 'rejected') {
    setDeciding(true)
    setError(null)
    try {
      const updated = await decideDocument(doc.id, decision)
      onChanged(updated)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save decision.')
    } finally {
      setDeciding(false)
    }
  }

  const fileUrl = documentFileUrl(doc.id)

  return (
    <div className="space-y-6">
      {error && (
        <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

      {/* Header status bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-zinc-200 bg-white p-6 shadow-xs">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-zinc-900">{doc.original_filename}</h2>
            <StatusBadge status={doc.status} />
          </div>
          <p className="mt-1 text-xs text-zinc-500">Document ID: {doc.id}</p>
        </div>

        {doc.status !== 'approved' && doc.status !== 'rejected' && (
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => void handleDecide('rejected')}
              disabled={deciding}
            >
              Reject
            </Button>
            <Button
              onClick={() => void handleDecide('approved')}
              disabled={deciding}
            >
              Approve
            </Button>
          </div>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left Column: File Preview */}
        <div className="space-y-6">
          <DocumentReviewSection title="Original Document">
            <DocumentPreview
              src={fileUrl}
              filename={doc.original_filename}
              contentType={doc.content_type}
            />
          </DocumentReviewSection>
        </div>

        {/* Right Column: Classification, Findings, Extraction, GL */}
        <div className="space-y-6">
          {/* Classification */}
          <DocumentReviewSection title="Classification">
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <span className="font-medium text-zinc-700">Type:</span>
                <Badge variant="info">{classification?.document_type || 'invoice'}</Badge>
                {classification?.confidence && (
                  <span className="text-xs text-zinc-500">
                    ({(classification.confidence * 100).toFixed(0)}% confidence)
                  </span>
                )}
              </div>
              {classification?.reasoning && (
                <p className="text-xs text-zinc-500">{classification.reasoning}</p>
              )}
            </div>
          </DocumentReviewSection>

          {/* Validation Issues */}
          <DocumentReviewSection
            title="Validation Findings"
            subtitle={`${doc.issues.length} check(s) executed`}
          >
            {doc.issues.length === 0 ? (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800">
                All business policy and EU VAT validation checks passed cleanly.
              </div>
            ) : (
              <ul className="space-y-2">
                {doc.issues.map((issue, idx) => (
                  <li
                    key={`${issue.code}-${idx}`}
                    className={`rounded-lg border p-3 text-xs ${
                      issue.severity === 'error'
                        ? 'border-rose-200 bg-rose-50 text-rose-800'
                        : 'border-amber-200 bg-amber-50 text-amber-800'
                    }`}
                  >
                    <span className="font-semibold">[{issue.code}]</span> {issue.message}
                  </li>
                ))}
              </ul>
            )}
          </DocumentReviewSection>

          {/* Extracted Fields */}
          <DocumentReviewSection
            title="Extracted Invoice Fields"
            action={
              !editing ? (
                <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
                  Edit fields
                </Button>
              ) : (
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" onClick={() => setEditing(false)}>
                    Cancel
                  </Button>
                  <Button size="sm" onClick={() => void handleSaveEdits()} disabled={saving}>
                    Save
                  </Button>
                </div>
              )
            }
          >
            {!editing ? (
              <dl className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <dt className="font-medium text-zinc-500">Supplier Name</dt>
                  <dd className="mt-0.5 text-zinc-900">{reviewData.vendor_name || '—'}</dd>
                </div>
                <div>
                  <dt className="font-medium text-zinc-500">Supplier VAT ID</dt>
                  <dd className="mt-0.5 text-zinc-900">{reviewData.vendor_vat_id || '—'}</dd>
                </div>
                <div>
                  <dt className="font-medium text-zinc-500">Customer Name</dt>
                  <dd className="mt-0.5 text-zinc-900">{reviewData.customer_name || '—'}</dd>
                </div>
                <div>
                  <dt className="font-medium text-zinc-500">Customer VAT ID</dt>
                  <dd className="mt-0.5 text-zinc-900">{reviewData.customer_vat_id || '—'}</dd>
                </div>
                <div>
                  <dt className="font-medium text-zinc-500">Invoice Number</dt>
                  <dd className="mt-0.5 text-zinc-900">{reviewData.invoice_number || '—'}</dd>
                </div>
                <div>
                  <dt className="font-medium text-zinc-500">Purchase Order</dt>
                  <dd className="mt-0.5 text-zinc-900">{reviewData.purchase_order || '—'}</dd>
                </div>
                <div>
                  <dt className="font-medium text-zinc-500">Invoice Date</dt>
                  <dd className="mt-0.5 text-zinc-900">{reviewData.invoice_date || '—'}</dd>
                </div>
                <div>
                  <dt className="font-medium text-zinc-500">Due Date</dt>
                  <dd className="mt-0.5 text-zinc-900">{reviewData.due_date || '—'}</dd>
                </div>
                <div>
                  <dt className="font-medium text-zinc-500">Subtotal</dt>
                  <dd className="mt-0.5 text-zinc-900">
                    {reviewData.subtotal != null ? `${reviewData.currency || 'EUR'} ${reviewData.subtotal}` : '—'}
                  </dd>
                </div>
                <div>
                  <dt className="font-medium text-zinc-500">Total Tax</dt>
                  <dd className="mt-0.5 text-zinc-900">
                    {reviewData.total_tax != null ? `${reviewData.currency || 'EUR'} ${reviewData.total_tax}` : '—'}
                  </dd>
                </div>
                <div className="col-span-2 border-t border-zinc-100 pt-2">
                  <dt className="font-semibold text-zinc-700">Invoice Total</dt>
                  <dd className="mt-0.5 text-base font-bold text-zinc-950">
                    {reviewData.invoice_total != null ? `${reviewData.currency || 'EUR'} ${reviewData.invoice_total}` : '—'}
                  </dd>
                </div>
              </dl>
            ) : (
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="font-medium text-zinc-700">Supplier Name</label>
                  <input
                    type="text"
                    className="mt-1 w-full rounded-md border border-zinc-300 p-1.5"
                    value={formData.vendor_name || ''}
                    onChange={(e) => setFormData({ ...formData, vendor_name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="font-medium text-zinc-700">Supplier VAT ID</label>
                  <input
                    type="text"
                    className="mt-1 w-full rounded-md border border-zinc-300 p-1.5"
                    value={formData.vendor_vat_id || ''}
                    onChange={(e) => setFormData({ ...formData, vendor_vat_id: e.target.value })}
                  />
                </div>
                <div>
                  <label className="font-medium text-zinc-700">Customer Name</label>
                  <input
                    type="text"
                    className="mt-1 w-full rounded-md border border-zinc-300 p-1.5"
                    value={formData.customer_name || ''}
                    onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="font-medium text-zinc-700">Customer VAT ID</label>
                  <input
                    type="text"
                    className="mt-1 w-full rounded-md border border-zinc-300 p-1.5"
                    value={formData.customer_vat_id || ''}
                    onChange={(e) => setFormData({ ...formData, customer_vat_id: e.target.value })}
                  />
                </div>
                <div>
                  <label className="font-medium text-zinc-700">Invoice Number</label>
                  <input
                    type="text"
                    className="mt-1 w-full rounded-md border border-zinc-300 p-1.5"
                    value={formData.invoice_number || ''}
                    onChange={(e) => setFormData({ ...formData, invoice_number: e.target.value })}
                  />
                </div>
                <div>
                  <label className="font-medium text-zinc-700">Invoice Total</label>
                  <input
                    type="number"
                    step="0.01"
                    className="mt-1 w-full rounded-md border border-zinc-300 p-1.5"
                    value={formData.invoice_total || ''}
                    onChange={(e) => setFormData({ ...formData, invoice_total: e.target.value })}
                  />
                </div>
              </div>
            )}
          </DocumentReviewSection>

          {/* General Ledger Account Selection */}
          <DocumentReviewSection title="General Ledger (GL) Account">
            <div className="space-y-3 text-xs">
              {glSuggestion && (
                <div className="rounded-lg bg-zinc-50 p-3">
                  <p className="font-semibold text-zinc-900">
                    Suggested: [{glSuggestion.gl_account_code}] {glSuggestion.category}
                  </p>
                  <p className="mt-1 text-zinc-500">{glSuggestion.rationale}</p>
                </div>
              )}

              <div>
                <div className="flex items-center justify-between">
                  <label className="font-medium text-zinc-700">Select GL Account:</label>
                  {accounts.length === 0 && !accountsLoading && (
                    <Button variant="ghost" size="sm" onClick={onRetryAccounts}>
                      Retry loading
                    </Button>
                  )}
                </div>
                {accountsLoading ? (
                  <p className="mt-1 text-zinc-500">Loading catalog accounts…</p>
                ) : (
                  <select
                    className="mt-1.5 w-full rounded-md border border-zinc-300 bg-white p-2 text-xs"
                    value={selectedGlCode}
                    onChange={(e) => void handleSelectGl(e.target.value)}
                    disabled={selectingGl}
                  >
                    <option value="">-- Select GL Account --</option>
                    {accounts.map((acc) => (
                      <option key={acc.code} value={acc.code}>
                        [{acc.code}] {acc.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </div>
          </DocumentReviewSection>
        </div>
      </div>
    </div>
  )
}
