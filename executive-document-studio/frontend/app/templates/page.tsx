import Link from 'next/link'
import { ArrowLeft, BookOpen, Sparkles } from 'lucide-react'

export default function TemplatesPage() {
  return (
    <main className="min-h-screen bg-studio-950 px-6 py-12 text-white">
      <div className="mx-auto max-w-6xl rounded-[32px] border border-white/8 bg-white/[0.03] p-8 shadow-chrome">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Templates</p>
            <h1 className="mt-2 text-3xl font-semibold">Executive formats</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
              This route holds the reusable output structures. The flagship board memo experience is already integrated into the main drafting canvas.
            </p>
          </div>
          <Link href="/" className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-slate-200">
            <ArrowLeft className="h-4 w-4" />
            Return to studio
          </Link>
        </div>
        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <div className="rounded-[28px] border border-white/8 bg-black/20 p-6">
            <BookOpen className="h-5 w-5 text-accent-blue" />
            <h2 className="mt-4 text-xl font-semibold">Board memo</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">Executive summary, background, analysis, recommendation, and risk assessment.</p>
          </div>
          <div className="rounded-[28px] border border-white/8 bg-black/20 p-6">
            <Sparkles className="h-5 w-5 text-accent-violet" />
            <h2 className="mt-4 text-xl font-semibold">Strategic brief</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">Condensed leadership format for quick alignment and follow-up action.</p>
          </div>
        </div>
      </div>
    </main>
  )
}
