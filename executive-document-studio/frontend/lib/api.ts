import type { SearchResult, StreamEvent, StudioDocument, StudioTemplate } from '@/lib/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Request failed with status ${response.status}`)
  }
  return response.json() as Promise<T>
}

export async function getDocuments(): Promise<StudioDocument[]> {
  const response = await fetch(`${API_BASE_URL}/api/documents`, { cache: 'no-store' })
  return parseJson<StudioDocument[]>(response)
}

export async function getTemplates(): Promise<StudioTemplate[]> {
  const response = await fetch(`${API_BASE_URL}/api/templates`, { cache: 'no-store' })
  return parseJson<StudioTemplate[]>(response)
}

export async function searchDocuments(query: string): Promise<SearchResult[]> {
  const response = await fetch(`${API_BASE_URL}/api/documents/search?q=${encodeURIComponent(query)}`, {
    cache: 'no-store',
  })
  return parseJson<SearchResult[]>(response)
}

function parseSseChunk(chunk: string): StreamEvent[] {
  return chunk
    .split('\n\n')
    .map((entry) => entry.trim())
    .filter(Boolean)
    .flatMap((entry) => {
      const dataLine = entry
        .split('\n')
        .find((line) => line.startsWith('data:'))

      if (!dataLine) return []

      try {
        return [JSON.parse(dataLine.replace(/^data:\s*/, '')) as StreamEvent]
      } catch {
        return []
      }
    })
}

export async function streamDraft(
  input: { template_id: string; doc_ids: string[]; instruction: string },
  handlers: {
    onEvent: (event: StreamEvent) => void
    onError: (message: string) => void
  },
) {
  const response = await fetch(`${API_BASE_URL}/api/drafts/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })

  if (!response.ok || !response.body) {
    handlers.onError(`Unable to start draft generation (${response.status})`)
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const segments = buffer.split('\n\n')
    buffer = segments.pop() ?? ''

    for (const segment of segments) {
      for (const event of parseSseChunk(`${segment}\n\n`)) {
        handlers.onEvent(event)
      }
    }
  }

  if (buffer.trim()) {
    for (const event of parseSseChunk(buffer)) {
      handlers.onEvent(event)
    }
  }
}
