import type { DocumentStatus } from '../lib/types'
import { Badge } from './ui/Badge'

interface StatusBadgeProps {
  status: DocumentStatus
}

export function StatusBadge({ status }: StatusBadgeProps) {
  switch (status) {
    case 'ready':
      return <Badge variant="success">Ready</Badge>
    case 'needs_review':
      return <Badge variant="warning">Needs review</Badge>
    case 'approved':
      return <Badge variant="success">Approved</Badge>
    case 'rejected':
      return <Badge variant="error">Rejected</Badge>
    case 'failed':
      return <Badge variant="error">Failed</Badge>
    case 'processing':
    default:
      return <Badge variant="info">Processing</Badge>
  }
}
