export type DocumentType =
  | 'annual_report'
  | 'acquisition_case_study'
  | 'strategic_plan'
  | 'market_analysis'
  | 'esg_report'
  | 'board_presentation'
  | 'other'

export interface StudioDocument {
  id: string
  title: string
  type: DocumentType
  tags: string[]
  date?: string | null
  summary?: string | null
  content?: string | null
}

export interface TemplateSection {
  id: string
  title: string
  instructions?: string | null
}

export interface StudioTemplate {
  id: string
  name: string
  description?: string | null
  sections: TemplateSection[]
}

export interface Citation {
  section: string
  document_id: string
  chunk_id: string
  snippet?: string | null
}

export interface SearchResult {
  chunk_id: string
  document_id: string
  document_title: string
  text: string
  score: number
  metadata: Record<string, unknown>
}

export interface StreamEvent {
  type: 'status' | 'citations' | 'content' | 'done' | 'error'
  message?: string
  citations?: Citation[]
  section?: string
  text?: string
  draft_id?: string
}
