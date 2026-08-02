interface DocumentPreviewProps {
  src: string
  filename: string
  contentType: string
}

export function DocumentPreview({ src, filename, contentType }: DocumentPreviewProps) {
  const isPdf = contentType === 'application/pdf' || filename.toLowerCase().endsWith('.pdf')

  if (isPdf) {
    return (
      <div className="h-[600px] w-full overflow-hidden rounded-xl border border-zinc-200 bg-zinc-900 shadow-xs">
        <iframe src={src} title={filename} className="h-full w-full border-none" />
      </div>
    )
  }

  return (
    <div className="flex min-h-[500px] w-full items-center justify-center overflow-hidden rounded-xl border border-zinc-200 bg-zinc-100 p-4 shadow-xs">
      <img src={src} alt={filename} className="max-h-[600px] w-auto max-w-full rounded-lg object-contain" />
    </div>
  )
}
