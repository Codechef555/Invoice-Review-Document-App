import { PROCESSING_STEPS } from '../lib/processing-progress'
import { Card, CardContent, CardHeader } from './ui/Card'

interface ProcessingStepProps {
  filename: string
}

export function ProcessingStep({ filename }: ProcessingStepProps) {
  return (
    <main className="mx-auto flex min-h-[calc(100vh-80px)] max-w-2xl items-center px-6 py-12">
      <Card className="w-full">
        <CardHeader className="border-b border-zinc-100 p-8">
          <p className="text-sm font-medium text-zinc-500">Step 2 of 3</p>
          <h1 className="pt-1 text-2xl font-semibold tracking-tight text-zinc-950">
            Running review pipeline
          </h1>
          <p className="break-all pt-1 text-sm text-zinc-600">Analyzing {filename}…</p>
        </CardHeader>
        <CardContent className="p-8">
          <ol className="space-y-6">
            {PROCESSING_STEPS.map((step, index) => (
              <li key={step.id} className="flex gap-4">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-zinc-900 text-xs font-semibold text-white">
                  {index + 1}
                </span>
                <div>
                  <p className="text-sm font-medium text-zinc-900">{step.label}</p>
                  <p className="mt-0.5 text-sm text-zinc-500">{step.detail}</p>
                </div>
              </li>
            ))}
          </ol>
        </CardContent>
      </Card>
    </main>
  )
}
