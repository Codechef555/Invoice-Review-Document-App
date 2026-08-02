export interface ProgressStep {
  id: string
  label: string
  detail: string
}

export const PROCESSING_STEPS: ProgressStep[] = [
  {
    id: 'classify',
    label: 'Classifying document type',
    detail: 'Determining if document is an invoice, receipt, or unsupported format.',
  },
  {
    id: 'extract',
    label: 'Extracting fields with Document Intelligence',
    detail: 'Analyzing vendor details, VAT IDs, dates, line items, and totals.',
  },
  {
    id: 'validate',
    label: 'Running business & EU VAT rules',
    detail: 'Validating VAT checksums, dates order, totals reconciliation, and duplicate invoice keys.',
  },
  {
    id: 'categorize',
    label: 'Suggesting General Ledger account',
    detail: 'Using Azure OpenAI structured output to match catalog GL accounts.',
  },
]
