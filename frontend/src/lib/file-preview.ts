export interface FilePreview {
  result: Promise<string>
  abort: () => void
}

export function createFilePreview(file: File): FilePreview {
  const url = URL.createObjectURL(file)
  let active = true

  const promise = Promise.resolve(url)

  return {
    result: promise,
    abort: () => {
      if (!active) return
      active = false
      URL.revokeObjectURL(url)
    },
  }
}
