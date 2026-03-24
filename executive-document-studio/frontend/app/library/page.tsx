import Link from 'next/link'
import { ArrowLeft, Files, Search } from 'lucide-react'

export default function LibraryPage() {
  return (
    <main className="min-h-screen bg-studio-950 px-6 py-12 text-white">
      <div className="mx-auto max-w-6xl rounded-[32px] border border-white/8 bg-white/[0.03] p-8 shadow-chrome">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Library</p>
            <h1 className="mt-2 text-3xl font-semibold">Source management</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
              The primary wow path lives in the main studio. This route is reserved for richer browsing, ingestion, and search workflows.
            </p>
          </div>
          <Link href="/" className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-slate-200">
            <ArrowLeft className="h-4 w-4" />
            Return to studio
          </Link>
        </div>
        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <div className="rounded-[28px] border border-white/8 bg-black/20 p-6">
            <Files className="h-5 w-5 text-accent-blue" />
            <h2 className="mt-4 text-xl font-semibold">Curated document sets</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">Pre-built collections for acquisitions, investor communications, and board review.</p>
          </div>
          <div className="rounded-[28px] border border-white/8 bg-black/20 p-6">
            <Search className="h-5 w-5 text-accent-cyan" />
            <h2 className="mt-4 text-xl font-semibold">Semantic search</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">Rapid retrieval backed by the same runtime used by the drafting workspace.</p>
          </div>
        </div>
      </div>
    </main>
  )
}
