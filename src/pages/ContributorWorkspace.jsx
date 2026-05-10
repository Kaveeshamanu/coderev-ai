import { useState } from 'react'
import WorkspaceLayout from '../components/WorkspaceLayout'
import CodeEditor from '../components/CodeEditor'
import { reviewCode } from '../api'
import { useHistory } from '../context/HistoryContext'
import {
  Code2, Play, Loader2, ChevronDown, Copy, Check,
  Info, Sparkles, RotateCcw, SlidersHorizontal,
  TrendingUp, Star,
} from 'lucide-react'

const BEAM_OPTIONS = [1, 3, 5, 10]

const PLACEHOLDER = `public boolean isPrime(int n) {
    if (n < 2) return false;
    for (int i = 2; i < n; i++) {
        if (n % i == 0) return false;
    }
    return true;
}`


function DiffLine({ line }) {
  if (line.startsWith('+')) return <div className="bg-green-500/10 text-green-300 px-3">{line}</div>
  if (line.startsWith('-')) return <div className="bg-red-500/10 text-red-300 px-3">{line}</div>
  return <div className="text-gray-400 px-3">{line}</div>
}

function SuggestionCard({ s, isSelected, onSelect }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(s.code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div
      onClick={() => onSelect(s)}
      className={`rounded-xl border transition-all duration-200 cursor-pointer overflow-hidden ${
        isSelected
          ? 'border-blue-500/50 bg-blue-500/5 ring-1 ring-blue-500/30'
          : 'border-white/10 hover:border-white/20 hover:bg-surface-200'
      }`}
    >
      {/* Card header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-dark-200/70">
        <div className="flex items-center gap-3">
          <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
            s.rank === 1 ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' : 'bg-white/10 text-gray-400'
          }`}>
            {s.rank === 1 ? <Star size={12} fill="currentColor" /> : s.rank}
          </div>
          <span className="text-sm font-medium text-white">Suggestion #{s.rank}</span>
          {s.rank === 1 && <span className="badge-blue text-[10px]">Top Pick</span>}
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <TrendingUp size={13} className="text-green-400" />
            <span className="text-xs text-green-400 font-medium">{(s.score * 100).toFixed(0)}% confidence</span>
          </div>
          <button
            onClick={(e) => { e.stopPropagation(); handleCopy() }}
            className="btn-ghost text-xs py-1 px-2"
          >
            {copied ? <Check size={13} className="text-green-400" /> : <Copy size={13} />}
            <span className="text-xs">{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      {/* Tags */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-white/5">
        {s.tags.map(tag => (
          <span key={tag} className="badge-blue text-[10px]">{tag}</span>
        ))}
      </div>

      {/* Code */}
      <pre className="p-4 font-mono text-sm text-gray-300 leading-6 overflow-auto bg-dark-200/50 max-h-48">
        {s.code}
      </pre>

      {/* Explanation */}
      <div className="flex items-start gap-2 px-4 py-3 border-t border-white/5 bg-dark-300/30">
        <Info size={14} className="text-blue-400 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-gray-400 leading-relaxed">{s.explanation}</p>
      </div>
    </div>
  )
}

export default function ContributorWorkspace() {
  const { addEntry, extractMethodName, formatDate } = useHistory()
  const [code, setCode] = useState('')
  const [beams, setBeams] = useState(3)
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState('')
  const [showSettings, setShowSettings] = useState(false)

  const handleReview = async () => {
    if (!code.trim()) {
      setError('Please paste a Java method before running the review.')
      return
    }
    setError('')
    setLoading(true)
    setSuggestions([])
    setSelected(null)
    try {
      const data = await reviewCode(code, beams)
      setSuggestions(data.suggestions)
      setSelected(data.suggestions[0] ?? null)
      if (data.suggestions.length > 0) {
        const top = data.suggestions[0]
        addEntry({
          id: Date.now(),
          mode: 'contributor',
          method: extractMethodName(code),
          date: formatDate(Date.now()),
          beams,
          topScore: Math.round(top.score * 100),
          status: 'completed',
          tags: top.tags ?? [],
        })
      }
    } catch (err) {
      setError(err.message || 'Failed to get suggestions. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setCode('')
    setSuggestions([])
    setSelected(null)
    setError('')
  }

  return (
    <WorkspaceLayout>
      <div className="px-4 py-8 sm:px-8 lg:px-12 max-w-screen-2xl mx-auto">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between mb-10">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-xl bg-blue-500/20 flex items-center justify-center">
                <Code2 size={17} className="text-blue-400" />
              </div>
              <h1 className="text-2xl font-bold text-white">Contributor Workspace</h1>
              <span className="badge-blue ml-1">Single-Encoder Model</span>
            </div>
            <p className="text-sm text-gray-400 max-w-xl leading-relaxed">
              Paste a Java method and let the AI automatically suggest improvements.
              No reviewer comment needed — the model learns from thousands of real code reviews.
            </p>
          </div>
          <button
            onClick={() => setShowSettings(s => !s)}
            className={`btn-ghost gap-2 text-sm self-start ${showSettings ? 'bg-white/10 text-white' : ''}`}
          >
            <SlidersHorizontal size={15} />
            Settings
          </button>
        </div>

        {/* Settings panel */}
        {showSettings && (
          <div className="card mb-8 border-white/10">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <SlidersHorizontal size={14} />
              Model Settings
            </h3>
            <div className="flex items-center gap-4 flex-wrap">
              <div>
                <label className="block text-xs text-gray-500 mb-3">Beam Size (number of suggestions)</label>
                <div className="flex gap-2">
                  {BEAM_OPTIONS.map(b => (
                    <button
                      key={b}
                      onClick={() => setBeams(b)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
                        beams === b
                          ? 'bg-blue-600 border-blue-500 text-white'
                          : 'bg-surface-100 border-white/10 text-gray-400 hover:text-white'
                      }`}
                    >
                      {b}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Input */}
        <div className="space-y-3 mb-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-300">Input — Java Method</h2>
            <button onClick={handleReset} className="btn-ghost text-xs gap-1.5">
              <RotateCcw size={12} /> Reset
            </button>
          </div>
          <CodeEditor
            value={code}
            onChange={setCode}
            label="YourMethod.java"
            placeholder={PLACEHOLDER}
            height="200px"
          />
        </div>

        {/* Button + Hint */}
        <div className="space-y-3 mb-8">
          {error && (
            <p className="text-sm text-red-400 flex items-center gap-1.5">
              <Info size={14} /> {error}
            </p>
          )}
          <button
            onClick={handleReview}
            disabled={loading || !code.trim()}
            className="btn-primary w-full justify-center py-4 text-base rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <><Loader2 size={18} className="animate-spin" /> Analysing with AI…</>
            ) : (
              <><Sparkles size={18} /> Run AI Review ({beams} beam{beams > 1 ? 's' : ''})</>
            )}
          </button>
          <div className="flex items-start gap-3 p-4 bg-blue-500/5 border border-blue-500/20 rounded-lg">
            <Info size={13} className="text-blue-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-gray-400 leading-relaxed">
              The model works best with complete Java methods (up to ~100 tokens after abstraction).
              Identifiers and literals are abstracted automatically before inference.
            </p>
          </div>
        </div>

        {/* AI Suggestions */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-300">
              AI Suggestions
              {suggestions.length > 0 && (
                <span className="ml-2 badge-green">{suggestions.length} result{suggestions.length > 1 ? 's' : ''}</span>
              )}
            </h2>
          </div>

          {loading && (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
              <div className="relative">
                <div className="w-14 h-14 rounded-full border-4 border-blue-500/30 border-t-blue-500 animate-spin" />
                <Code2 size={20} className="text-blue-400 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
              </div>
              <div className="text-center">
                <p className="text-sm text-white font-medium">Generating suggestions…</p>
                <p className="text-xs text-gray-500 mt-1">Running beam search with {beams} beam{beams > 1 ? 's' : ''}</p>
              </div>
            </div>
          )}

          {!loading && suggestions.length === 0 && (
            <div className="flex flex-col items-center justify-center h-64 gap-4 border-2 border-dashed border-white/10 rounded-xl p-8">
              <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center">
                <Sparkles size={22} className="text-gray-600" />
              </div>
              <p className="text-sm text-gray-500 text-center max-w-xs leading-relaxed">
                Paste a Java method above and click <strong className="text-gray-400">Run AI Review</strong> to see suggestions here.
              </p>
            </div>
          )}

          {!loading && suggestions.length > 0 && (
            <div className="space-y-4 max-h-[500px] overflow-y-auto pr-1">
              {suggestions.map((s) => (
                <SuggestionCard
                  key={s.rank}
                  s={s}
                  isSelected={selected?.rank === s.rank}
                  onSelect={setSelected}
                />
              ))}
            </div>
          )}
        </div>

        {/* Selected diff view */}
        {selected && (
          <div className="mt-8 card">
            <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
              <Code2 size={14} className="text-blue-400" />
              Side-by-Side Comparison — Suggestion #{selected.rank}
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider">Your Code</p>
                <pre className="code-block p-4 text-red-300/80 max-h-64 overflow-auto">
                  {code || '// (empty)'}
                </pre>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider">AI Suggestion</p>
                <pre className="code-block p-4 text-green-300 max-h-64 overflow-auto">
                  {selected.code}
                </pre>
              </div>
            </div>
          </div>
        )}
      </div>
    </WorkspaceLayout>
  )
}
