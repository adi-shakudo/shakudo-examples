'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import {
  ArrowRight,
  BookOpen,
  Bot,
  CheckCircle2,
  ChevronRight,
  FileSearch,
  Files,
  FolderKanban,
  Layers3,
  Lock,
  MessageSquareText,
  ShieldCheck,
  Sparkles,
  WandSparkles,
} from 'lucide-react'

import { getDocuments, getTemplates, streamDraft } from '@/lib/api'
import type { Citation, StudioDocument, StudioTemplate } from '@/lib/types'
import { cn } from '@/lib/utils'

const defaultPrompt =
  'Draft a board memo evaluating the acquisition of a regional organic food distributor. Incorporate lessons from prior acquisitions, current market positioning, and a more conservative risk stance.'

const navItems = [
  { label: 'Studio', href: '/', icon: Layers3, active: true },
  { label: 'Library', href: '/library', icon: Files },
  { label: 'Templates', href: '/templates', icon: FolderKanban },
]

const promptPresets = [
  'Board-ready tone',
  'Conservative risk framing',
  'Acquisition precedent',
  'Investor summary',
]

export function StudioShell() {
  const [documents, setDocuments] = useState<StudioDocument[]>([])
  const [templates, setTemplates] = useState<StudioTemplate[]>([])
  const [selectedTemplateId, setSelectedTemplateId] = useState('template_board_memo')
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([])
  const [instruction, setInstruction] = useState(defaultPrompt)
  const [draftSections, setDraftSections] = useState<Record<string, string>>({})
  const [citations, setCitations] = useState<Citation[]>([])
  const [activity, setActivity] = useState<string[]>([
    'Studio ready. Curate a working set, then generate a board-ready draft.',
  ])
  const [draftId, setDraftId] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const selectedTemplate = useMemo(
    () => templates.find((template) => template.id === selectedTemplateId) ?? templates[0],
    [selectedTemplateId, templates],
  )

  const selectedDocuments = useMemo(
    () => documents.filter((document) => selectedDocIds.includes(document.id)),
    [documents, selectedDocIds],
  )

  useEffect(() => {
    async function bootstrap() {
      try {
        const [docs, templateData] = await Promise.all([getDocuments(), getTemplates()])
        setDocuments(docs)
        setTemplates(templateData)
        setSelectedDocIds(docs.slice(0, 4).map((document) => document.id))
        if (templateData[0]) setSelectedTemplateId(templateData[0].id)
      } catch (bootstrapError) {
        setError(
          bootstrapError instanceof Error
            ? bootstrapError.message
            : 'Unable to load studio resources',
        )
      }
    }

    void bootstrap()
  }, [])

  function toggleDocument(documentId: string) {
    setSelectedDocIds((current) =>
      current.includes(documentId)
        ? current.filter((id) => id !== documentId)
        : [...current, documentId],
    )
  }

  async function handleGenerate() {
    if (!selectedTemplate || selectedDocIds.length === 0 || !instruction.trim()) return

    setIsGenerating(true)
    setError(null)
    setDraftId(null)
    setDraftSections({})
    setCitations([])
    setActivity([
      'Generation run started. Live retrieval and section drafting in progress...',
    ])

    await streamDraft(
      {
        template_id: selectedTemplate.id,
        doc_ids: selectedDocIds,
        instruction,
      },
      {
        onEvent: (event) => {
          if (event.type === 'status' && event.message) {
            setActivity((current) => [...current, event.message as string])
          }

          if (event.type === 'citations' && event.citations) {
            setCitations(event.citations)
          }

          if (event.type === 'content' && event.section && event.text) {
            setDraftSections((current) => ({
              ...current,
              [event.section as string]: `${current[event.section as string] ?? ''}${event.text ?? ''}`,
            }))
          }

          if (event.type === 'done') {
            setDraftId(event.draft_id ?? null)
            setIsGenerating(false)
            setActivity((current) => [...current, 'Draft complete. Ready for review and refinement.'])
          }

          if (event.type === 'error') {
            setError(event.message ?? 'Streaming error')
            setIsGenerating(false)
          }
        },
        onError: (message) => {
          setError(message)
          setIsGenerating(false)
        },
      },
    )
  }

  return (
    <div className="min-h-screen bg-studio-950 text-white">
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-90" />
      <div className="pointer-events-none absolute inset-0 bg-grid bg-[size:48px_48px] opacity-[0.05]" />
      <div className="relative flex min-h-screen">
        <aside className="hidden w-[84px] border-r border-white/6 bg-black/20 backdrop-blur-xl xl:flex xl:flex-col xl:items-center xl:gap-5 xl:py-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 bg-white/5 shadow-panel">
            <Sparkles className="h-5 w-5 text-accent-cyan" />
          </div>
          <div className="flex flex-col gap-3">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  className={cn(
                    'group flex h-12 w-12 items-center justify-center rounded-2xl border transition',
                    item.active
                      ? 'border-accent-blue/50 bg-accent-blue/15 text-white shadow-glow'
                      : 'border-white/5 bg-white/[0.03] text-slate-400 hover:border-white/15 hover:bg-white/[0.06] hover:text-white',
                  )}
                >
                  <Icon className="h-5 w-5" />
                </Link>
              )
            })}
          </div>
          <div className="mt-auto flex flex-col gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] text-slate-300">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.03] text-slate-300">
              <Bot className="h-4 w-4" />
            </div>
          </div>
        </aside>

        <aside className="hidden w-[340px] shrink-0 border-r border-white/6 bg-studio-900/70 p-6 backdrop-blur-2xl lg:block">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Working set</p>
              <h2 className="mt-2 text-xl font-semibold text-white">Internal source stack</h2>
            </div>
            <div className="rounded-full border border-emerald-400/25 bg-emerald-400/10 px-3 py-1 text-[11px] font-medium text-emerald-200">
              100% private
            </div>
          </div>

          <div className="mb-5 rounded-3xl border border-white/10 bg-white/[0.035] p-4 shadow-panel">
            <div className="flex items-start gap-3">
              <div className="mt-1 rounded-2xl bg-accent-blue/15 p-2 text-accent-blue">
                <FileSearch className="h-4 w-4" />
              </div>
              <div>
                <p className="text-sm font-medium text-white">Semantic retrieval ready</p>
                <p className="mt-1 text-sm leading-6 text-slate-400">
                  Select the internal documents you want the backend to ground the draft on.
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            {documents.map((document) => {
              const selected = selectedDocIds.includes(document.id)
              return (
                <button
                  key={document.id}
                  type="button"
                  onClick={() => toggleDocument(document.id)}
                  className={cn(
                    'w-full rounded-[26px] border p-4 text-left transition duration-200',
                    selected
                      ? 'border-accent-blue/45 bg-accent-blue/10 shadow-glow'
                      : 'border-white/6 bg-white/[0.025] hover:border-white/15 hover:bg-white/[0.05]',
                  )}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{document.type.replaceAll('_', ' ')}</p>
                      <h3 className="mt-2 text-sm font-semibold text-white">{document.title}</h3>
                      <p className="mt-2 text-sm leading-6 text-slate-400">{document.summary}</p>
                    </div>
                    <div
                      className={cn(
                        'mt-1 h-3 w-3 rounded-full border',
                        selected ? 'border-emerald-300 bg-emerald-300' : 'border-white/25 bg-transparent',
                      )}
                    />
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {document.tags.map((tag) => (
                      <span
                        key={tag}
                        className="rounded-full border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[11px] text-slate-300"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </button>
              )
            })}
          </div>
        </aside>

        <main className="flex min-w-0 flex-1 flex-col">
          <header className="border-b border-white/6 bg-studio-900/40 px-5 py-4 backdrop-blur-xl sm:px-8">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div>
                <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-slate-500">
                  <span>George Weston Limited</span>
                  <ChevronRight className="h-3.5 w-3.5" />
                  <span>Executive Document Studio</span>
                </div>
                <h1 className="mt-3 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
                  Board memo workspace
                </h1>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400 sm:text-[15px]">
                  A premium drafting environment for live, cited, backend-powered executive communication generation.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <div className="rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-slate-300">
                  <span className="mr-2 text-slate-500">Template</span>
                  {selectedTemplate?.name ?? 'Loading...'}
                </div>
                <div className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-4 py-2 text-sm text-emerald-200">
                  <Lock className="mr-2 inline h-4 w-4" />
                  Private runtime
                </div>
                <button
                  type="button"
                  onClick={handleGenerate}
                  disabled={isGenerating || !selectedTemplate || selectedDocIds.length === 0}
                  className="inline-flex items-center gap-2 rounded-full border border-accent-blue/50 bg-accent-blue px-5 py-3 text-sm font-semibold text-white shadow-glow transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <WandSparkles className="h-4 w-4" />
                  {isGenerating ? 'Generating…' : 'Generate live draft'}
                </button>
              </div>
            </div>
          </header>

          <div className="flex min-h-0 flex-1 flex-col xl:flex-row">
            <section className="min-w-0 flex-1 border-r border-white/6 p-5 sm:p-8">
              <div className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
                <div className="rounded-[30px] border border-white/8 bg-white/[0.03] p-5 shadow-panel backdrop-blur-xl">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Prompt orchestration</p>
                      <h2 className="mt-2 text-lg font-semibold text-white">Live drafting brief</h2>
                    </div>
                    <div className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-[11px] text-slate-400">
                      {selectedDocIds.length} source docs selected
                    </div>
                  </div>

                  <div className="mt-5 rounded-[26px] border border-white/8 bg-black/20 p-3">
                    <textarea
                      value={instruction}
                      onChange={(event) => setInstruction(event.target.value)}
                      className="min-h-[160px] w-full resize-none bg-transparent px-2 py-1 text-[15px] leading-7 text-slate-100 outline-none placeholder:text-slate-500"
                      placeholder="Describe the memo you want the system to generate..."
                    />
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {promptPresets.map((preset) => (
                      <button
                        key={preset}
                        type="button"
                        onClick={() => setInstruction((current) => `${current.trim()} ${preset}.`.trim())}
                        className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-white/20 hover:bg-white/[0.08] hover:text-white"
                      >
                        + {preset}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="rounded-[30px] border border-white/8 bg-gradient-to-br from-white/[0.06] to-white/[0.02] p-5 shadow-panel">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Template gallery</p>
                  <h2 className="mt-2 text-lg font-semibold text-white">Executive output formats</h2>
                  <div className="mt-5 space-y-3">
                    {templates.map((template) => {
                      const selected = template.id === selectedTemplateId
                      return (
                        <button
                          key={template.id}
                          type="button"
                          onClick={() => setSelectedTemplateId(template.id)}
                          className={cn(
                            'w-full rounded-[24px] border p-4 text-left transition',
                            selected
                              ? 'border-accent-cyan/45 bg-accent-cyan/10 shadow-[0_0_0_1px_rgba(94,234,212,0.18)]'
                              : 'border-white/6 bg-black/10 hover:border-white/15 hover:bg-white/[0.05]',
                          )}
                        >
                          <div className="flex items-center justify-between gap-3">
                            <div>
                              <div className="flex items-center gap-2">
                                <BookOpen className="h-4 w-4 text-slate-400" />
                                <p className="text-sm font-semibold text-white">{template.name}</p>
                              </div>
                              <p className="mt-2 text-sm leading-6 text-slate-400">{template.description}</p>
                            </div>
                            {selected && <CheckCircle2 className="h-5 w-5 text-accent-cyan" />}
                          </div>
                        </button>
                      )
                    })}
                  </div>
                </div>
              </div>

              <div className="mt-5 rounded-[32px] border border-white/8 bg-studio-900/75 p-5 shadow-chrome backdrop-blur-2xl">
                <div className="flex flex-col gap-3 border-b border-white/6 pb-5 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Draft canvas</p>
                    <h2 className="mt-2 text-xl font-semibold text-white">Executive memo draft</h2>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {selectedDocuments.map((document) => (
                      <span
                        key={document.id}
                        className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-300"
                      >
                        {document.title}
                      </span>
                    ))}
                  </div>
                </div>

                {error ? (
                  <div className="mt-5 rounded-[24px] border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-100">
                    {error}
                  </div>
                ) : null}

                <div className="mt-6 grid gap-4">
                  {(selectedTemplate?.sections ?? []).map((section) => {
                    const content = draftSections[section.id] ?? ''
                    return (
                      <article
                        key={section.id}
                        className="rounded-[28px] border border-white/8 bg-white/[0.03] p-5 transition hover:border-white/15"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Section</p>
                            <h3 className="mt-1 text-lg font-semibold text-white">{section.title}</h3>
                            {section.instructions ? (
                              <p className="mt-2 text-sm text-slate-500">{section.instructions}</p>
                            ) : null}
                          </div>
                          <div className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-[11px] text-slate-400">
                            {content ? 'Grounded' : isGenerating ? 'Drafting' : 'Ready'}
                          </div>
                        </div>
                        <div className="mt-4 min-h-[120px] rounded-[24px] border border-white/6 bg-black/15 px-4 py-4 text-[15px] leading-7 text-slate-200">
                          {content ? (
                            <p className="whitespace-pre-wrap">{content}</p>
                          ) : (
                            <p className="text-slate-500">
                              {isGenerating
                                ? 'Live content is streaming into this section…'
                                : 'Generate a draft to populate this section with cited executive-ready language.'}
                            </p>
                          )}
                        </div>
                      </article>
                    )
                  })}
                </div>
              </div>
            </section>

            <aside className="w-full shrink-0 p-5 sm:p-8 xl:w-[360px]">
              <div className="space-y-5">
                <div className="rounded-[30px] border border-white/8 bg-white/[0.03] p-5 shadow-panel">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">AI runtime</p>
                      <h2 className="mt-2 text-lg font-semibold text-white">Generation activity</h2>
                    </div>
                    <div className={cn(
                      'rounded-full px-3 py-1 text-[11px] font-medium',
                      isGenerating
                        ? 'border border-accent-amber/30 bg-accent-amber/10 text-amber-100'
                        : 'border border-emerald-400/25 bg-emerald-400/10 text-emerald-100',
                    )}>
                      {isGenerating ? 'Streaming live' : 'Standing by'}
                    </div>
                  </div>

                  <div className="mt-4 space-y-3">
                    {activity.slice(-8).map((item, index) => (
                      <div key={`${item}-${index}`} className="flex gap-3 rounded-[22px] border border-white/6 bg-black/15 p-3">
                        <div className="mt-1 rounded-full bg-accent-blue/15 p-1.5 text-accent-blue">
                          <MessageSquareText className="h-3.5 w-3.5" />
                        </div>
                        <p className="text-sm leading-6 text-slate-300">{item}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-[30px] border border-white/8 bg-white/[0.03] p-5 shadow-panel">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Provenance</p>
                  <h2 className="mt-2 text-lg font-semibold text-white">Retrieved evidence</h2>
                  <div className="mt-4 space-y-3">
                    {citations.length === 0 ? (
                      <div className="rounded-[22px] border border-dashed border-white/10 bg-black/15 p-4 text-sm leading-6 text-slate-500">
                        Once generation starts, cited supporting passages will appear here.
                      </div>
                    ) : (
                      citations.slice(0, 6).map((citation, index) => (
                        <div key={`${citation.chunk_id}-${index}`} className="rounded-[22px] border border-white/6 bg-black/15 p-4">
                          <div className="flex items-center justify-between gap-3">
                            <span className="text-sm font-medium text-white">{citation.document_id}</span>
                            <span className="rounded-full border border-white/10 bg-white/[0.05] px-2.5 py-1 text-[11px] text-slate-400">
                              {citation.section}
                            </span>
                          </div>
                          <p className="mt-3 text-sm leading-6 text-slate-400">{citation.snippet}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                <div className="rounded-[30px] border border-emerald-400/18 bg-gradient-to-br from-emerald-400/12 to-cyan-400/6 p-5 shadow-panel">
                  <div className="flex items-start gap-3">
                    <div className="rounded-2xl bg-emerald-300/15 p-2 text-emerald-200">
                      <ShieldCheck className="h-5 w-5" />
                    </div>
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.22em] text-emerald-100/70">Trust surface</p>
                      <h2 className="mt-2 text-lg font-semibold text-white">Security & auditability</h2>
                      <p className="mt-3 text-sm leading-6 text-emerald-50/80">
                        Documents stay inside the private environment, citations are preserved, and each run can be audited end-to-end.
                      </p>
                    </div>
                  </div>

                  <div className="mt-5 grid gap-3">
                    {[
                      'Private corpus selection visible before every run',
                      'Live retrieval activity exposed to the operator',
                      draftId ? `Draft persisted as ${draftId}` : 'Draft persisted after generation',
                    ].map((item) => (
                      <div key={item} className="flex items-center gap-3 rounded-[20px] border border-white/10 bg-black/10 px-4 py-3 text-sm text-white/90">
                        <ArrowRight className="h-4 w-4 text-emerald-200" />
                        <span>{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </aside>
          </div>
        </main>
      </div>
    </div>
  )
}
