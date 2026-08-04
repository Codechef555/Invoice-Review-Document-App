import { type FormEvent, useState } from 'react'
import { verifyPassword } from '../lib/api'
import { Button } from './ui/Button'
import { Card } from './ui/Card'

interface PasswordGateProps {
  onSuccess: () => void
}

export function PasswordGate({ onSuccess }: PasswordGateProps) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!password) return

    setLoading(true)
    setError(null)
    try {
      await verifyPassword(password)
      onSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid passcode')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 px-4">
      <Card className="w-full max-w-md p-8 shadow-lg">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-zinc-900 text-lg font-bold text-white">
            N
          </div>
          <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
            Northstar Facilities B.V.
          </p>
          <h1 className="mt-1 text-2xl font-bold text-zinc-900">Protected Workspace</h1>
          <p className="mt-2 text-sm text-zinc-600">
            Enter the access passcode to open the Invoice Review application.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="passcode" className="block text-xs font-medium text-zinc-700">
              Passcode
            </label>
            <input
              id="passcode"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter passcode"
              className="mt-1 block w-full rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900 shadow-sm focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900"
              autoFocus
            />
          </div>

          {error && (
            <div className="rounded-md bg-red-50 p-3 text-xs font-medium text-red-700">
              {error}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Verifying...' : 'Unlock Application'}
          </Button>
        </form>
      </Card>
    </div>
  )
}
