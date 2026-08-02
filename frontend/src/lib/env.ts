const env = import.meta.env as Record<string, string | undefined>
export const apiBaseUrl = env.VITE_API_BASE_URL ?? 'http://localhost:8000'
