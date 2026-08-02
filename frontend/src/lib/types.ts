export type DocumentStatus =
  | 'processing'
  | 'ready'
  | 'needs_review'
  | 'approved'
  | 'rejected'
  | 'failed'

export type IssueSeverity = 'error' | 'warning'
export type DocumentType = 'invoice' | 'receipt'

export interface ReviewLineItem {
  description: string | null
  quantity: number | string | null
  unit_price: number | string | null
  amount: number | string | null
}

export interface ReviewData {
  document_type: DocumentType
  expense_category?: string | null
  vendor_name: string | null
  vendor_vat_id: string | null
  customer_name: string | null
  customer_vat_id: string | null
  invoice_number: string | null
  purchase_order: string | null
  invoice_date: string | null
  due_date: string | null
  currency: string | null
  subtotal: number | string | null
  total_tax: number | string | null
  invoice_total: number | string | null
  amount_due?: number | string | null
  line_items: ReviewLineItem[]
  field_confidence?: Record<string, number>
}

export interface ValidationIssue {
  code: string
  field: string | null
  severity: IssueSeverity
  message: string
}

export interface GlAccount {
  code: string
  name: string
  description: string
}

export interface AccountingSuggestion {
  gl_account_code: string
  category: string
  rationale: string
  confidence: number
}

export interface AccountingCoding {
  suggestion: AccountingSuggestion | null
  selected_gl_account_code: string | null
  overridden: boolean
  error_message: string | null
}

export interface Document {
  id: string
  original_filename: string
  content_type: string
  status: DocumentStatus
  classification: Record<string, unknown> | null
  extraction: Record<string, unknown> | null
  validation: Record<string, unknown> | null
  gl_suggestion: Record<string, unknown> | null
  review_data: ReviewData | null
  accounting_coding: AccountingCoding | null
  issues: ValidationIssue[]
  supplier_action_required: boolean
  error_message: string | null
  created_at: string
  updated_at: string
}
