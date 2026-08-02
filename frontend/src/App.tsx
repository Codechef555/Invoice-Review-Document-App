import { useCallback, useEffect, useState } from 'react'
import { DocumentInbox } from './components/DocumentInbox'
import { DocumentReview } from './components/DocumentReview'
import { ProcessingStep } from './components/ProcessingStep'
import { UploadStep } from './components/UploadStep'
import { WelcomePortal } from './components/WelcomePortal'
import { Button } from './components/ui/Button'
import { Card } from './components/ui/Card'
import { deleteDocument, listDocuments, listGlAccounts, uploadDocument } from './lib/api'
import type { Document, GlAccount } from './lib/types'

type View = 'welcome' | 'upload' | 'processing' | 'result' | 'history'

interface AppHeaderProps {
  onHome: () => void
  onNew: () => void
  onHistory: () => void
}

function AppHeader({ onHome, onNew, onHistory }: AppHeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-zinc-200 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <button
          type="button"
          onClick={onHome}
          className="flex cursor-pointer items-center gap-2 text-left"
        >
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-zinc-900 text-xs font-bold text-white">
            N
          </span>
          <div>
            <p className="text-xs font-medium text-zinc-500">Northstar Facilities B.V.</p>
            <p className="text-sm font-semibold text-zinc-900">Document Review</p>
          </div>
        </button>
        <nav className="flex items-center gap-3">
          <Button onClick={onHistory} variant="ghost" size="sm">
            History
          </Button>
          <Button onClick={onNew} size="sm">
            New review
          </Button>
        </nav>
      </div>
    </header>
  )
}

function App() {
  const [view, setView] = useState<View>('welcome')
  const [file, setFile] = useState<File | null>(null)
  const [selected, setSelected] = useState<Document | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [accounts, setAccounts] = useState<GlAccount[]>([])
  const [accountsLoading, setAccountsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [historyLoading, setHistoryLoading] = useState(false)

  const refreshAccounts = useCallback(async () => {
    setAccountsLoading(true)
    try {
      setAccounts(await listGlAccounts())
    } catch {
      setAccounts([])
    } finally {
      setAccountsLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    void listGlAccounts()
      .then((loaded) => {
        if (active) setAccounts(loaded)
      })
      .catch(() => {
        if (active) setAccounts([])
      })
      .finally(() => {
        if (active) setAccountsLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  function startReview() {
    setFile(null)
    setSelected(null)
    setError(null)
    setView('upload')
  }

  async function openHistory() {
    setView('history')
    setError(null)
    setHistoryLoading(true)
    try {
      setDocuments(await listDocuments())
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not load review history.')
    } finally {
      setHistoryLoading(false)
    }
  }

  async function processDocument() {
    if (!file) return
    setError(null)
    setView('processing')
    try {
      const processed = await uploadDocument(file)
      setSelected(processed)
      setDocuments((current) => [processed, ...current.filter((item) => item.id !== processed.id)])
      if (!accountsLoading && accounts.length === 0) void refreshAccounts()
      setView('result')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not process the document.')
      setView('upload')
    }
  }

  function handleChanged(changed: Document) {
    setSelected(changed)
    setDocuments((current) =>
      current.map((item) => (item.id === changed.id ? changed : item)),
    )
  }

  function showDocument(next: Document) {
    setSelected(next)
    setView('result')
  }

  async function removeHistoryDocument(next: Document) {
    setError(null)
    try {
      await deleteDocument(next.id)
      setDocuments((current) => current.filter((item) => item.id !== next.id))
      if (selected?.id === next.id) {
        setSelected(null)
      }
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : 'Could not delete the document.'
      setError(message)
    }
  }

  function home() {
    setError(null)
    setView('welcome')
  }

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-950">
      {view !== 'welcome' && (
        <AppHeader
          onHome={home}
          onNew={startReview}
          onHistory={() => void openHistory()}
        />
      )}

      {view === 'welcome' && (
        <WelcomePortal onStart={startReview} onHistory={() => void openHistory()} />
      )}

      {view === 'upload' && (
        <UploadStep
          file={file}
          error={error}
          onChoose={(next) => {
            setFile(next)
            setError(null)
          }}
          onProcess={() => void processDocument()}
          onBack={home}
        />
      )}

      {view === 'processing' && file && <ProcessingStep filename={file.name} />}

      {view === 'result' && selected && (
        <main className="mx-auto max-w-5xl px-6 py-8">
          <div className="mb-6">
            <p className="text-sm text-zinc-500">Step 3 of 3</p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight">Review the result</h1>
            <p className="mt-1 text-sm text-zinc-600">
              Correct fields if needed, confirm the General Ledger account, then approve or reject.
            </p>
          </div>
          <DocumentReview
            key={selected.id}
            document={selected}
            accounts={accounts}
            accountsLoading={accountsLoading}
            onRetryAccounts={() => void refreshAccounts()}
            onChanged={handleChanged}
          />
        </main>
      )}

      {view === 'history' && (
        <main className="mx-auto max-w-4xl px-6 py-10">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-sm text-zinc-500">Saved locally</p>
              <h1 className="mt-1 text-2xl font-semibold tracking-tight">Review history</h1>
              <p className="mt-1 text-sm text-zinc-600">
                Open a previous invoice or receipt, or start another review.
              </p>
            </div>
            <Button onClick={startReview}>Review another</Button>
          </div>
          {error && (
            <div
              role="alert"
              className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800"
            >
              {error}
            </div>
          )}
          <Card className="mt-6 overflow-hidden">
            {historyLoading ? (
              <p className="p-12 text-center text-sm text-zinc-500">Loading review history…</p>
            ) : (
              <DocumentInbox
                documents={documents}
                onSelect={showDocument}
                onDelete={(doc) => void removeHistoryDocument(doc)}
              />
            )}
          </Card>
        </main>
      )}
    </div>
  )
}

export default App
