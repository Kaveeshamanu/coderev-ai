import { useState } from 'react'
import WorkspaceLayout from '../components/WorkspaceLayout'
import CodeEditor from '../components/CodeEditor'
import { implementComment } from '../api'
import { useHistory } from '../context/HistoryContext'
import {
  MessageSquareCode, Loader2, Info,
  Sparkles, RotateCcw, SlidersHorizontal,
  TrendingUp, Star, Copy, Check, MessageSquare,
  Code2, AlertCircle,
} from 'lucide-react'

const BEAM_OPTIONS = [1, 3, 5, 10]

const CODE_PLACEHOLDER = `public void processData(List data) {
    for (int i = 0; i < data.size(); i++) {
        Object item = data.get(i);
        System.out.println(item);
    }
}`

const COMMENT_SUGGESTIONS = [
  'Use enhanced for-loop instead of indexed loop',
  'Add null check for the data parameter',
  'Replace System.out.println with a logger',
  'Use generics instead of raw type',
]


function ImplementationCard({ impl, isSelected, onSelect }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(impl.code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div
      onClick={() => onSelect(impl)}
      className={`rounded-xl border transition-all duration-200 cursor-pointer overflow-hidden ${
        isSelected
          ? 'border-blue-500/50 bg-blue-500/5 ring-1 ring-blue-500/30'
          : 'border-white/10 hover:border-white/20 hover:bg-surface-200'
      }`}
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-dark-200/70">
        <div className="flex items-center gap-3">
          <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
            impl.rank === 1 ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' : 'bg-white/10 text-gray-400'
          }`}>
            {impl.rank === 1 ? <Star size={12} fill="currentColor" /> : impl.rank}
          </div>
          <span className="text-sm font-medium text-white">Implementation #{impl.rank}</span>
          {impl.rank === 1 && <span className="badge-blue text-[10px]">Best Match</span>}
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <TrendingUp size={13} className="text-green-400" />
            <span className="text-xs text-green-400 font-medium">{(impl.score * 100).toFixed(0)}% confidence</span>
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

      <div className="flex items-center gap-2 px-4 py-2 border-b border-white/5">
        {impl.tags.map(tag => (
          <span key={tag} className="badge-blue text-[10px]">{tag}</span>
        ))}
      </div>

      <pre className="p-4 font-mono text-sm text-gray-300 leading-6 overflow-auto bg-dark-200/50 max-h-48">
        {impl.code}
      </pre>

      <div className="flex items-start gap-2 px-4 py-3 border-t border-white/5 bg-dark-300/30">
        <Info size={14} className="text-blue-400 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-gray-400 leading-relaxed">{impl.explanation}</p>
      </div>
    </div>
  )
}

export default function ReviewerWorkspace() {
  const { addEntry, extractMethodName, formatDate } = useHistory()
  const [code, setCode] = useState('')
  const [comment, setComment] = useState('')
  const [beams, setBeams] = useState(3)
  const [loading, setLoading] = useState(false)
  const [implementations, setImplementations] = useState([])
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState('')
  const [showSettings, setShowSettings] = useState(false)

  const handleImplement = async () => {
    if (!code.trim()) { setError('Please paste a Java method.'); return }
    if (!comment.trim()) { setError('Please enter a reviewer comment.'); return }
    setError('')
    setLoading(true)
    setImplementations([])
    setSelected(null)
    try {
      const data = await implementComment(code, comment, beams)
      setImplementations(data.implementations)
      setSelected(data.implementations[0] ?? null)
      if (data.implementations.length > 0) {
        const top = data.implementations[0]
        addEntry({
          id: Date.now(),
          mode: 'reviewer',
          method: extractMethodName(code),
          date: formatDate(Date.now()),
          beams,
          topScore: Math.round(top.score * 100),
          status: 'completed',
          comment,
          tags: top.tags ?? [],
        })
      }
    } catch (err) {
      setError(err.message || 'Failed to generate implementations. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setCode('')
    setComment('')
    setImplementations([])
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
                <MessageSquareCode size={17} className="text-blue-400" />
              </div>
              <h1 className="text-2xl font-bold text-white">Reviewer Workspace</h1>
              <span className="badge-blue ml-1">Dual-Encoder Model</span>
            </div>
            <p className="text-sm text-gray-400 max-w-xl leading-relaxed">
              Provide a Java method and a natural language reviewer comment.
              The dual-encoder model will automatically generate code that implements the suggestion.
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
            <div>
              <label className="block text-xs text-gray-500 mb-3">Beam Size (number of implementations)</label>
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
        )}

        {/* Inputs row */}
        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* Code input */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                <Code2 size={14} className="text-blue-400" />
                Java Method (Code Under Review)
              </h2>
              <button onClick={handleReset} className="btn-ghost text-xs gap-1.5">
                <RotateCcw size={12} /> Reset
              </button>
            </div>
            <CodeEditor
              value={code}
              onChange={setCode}
              label="OriginalMethod.java"
              placeholder={CODE_PLACEHOLDER}
              height="300px"
            />
          </div>

          {/* Comment input */}
          <div className="space-y-4">
            <h2 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
              <MessageSquare size={14} className="text-blue-400" />
              Reviewer Comment
            </h2>
            <div className="flex flex-col" style={{ height: '300px' }}>
              <div className="flex items-center justify-between px-4 py-3 bg-dark-200 border border-white/10 rounded-t-lg border-b-0">
                <span className="text-xs text-gray-500 font-mono">review-comment.txt</span>
                <span className="badge-blue text-[10px]">natural language</span>
              </div>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="e.g. Use enhanced for-loop instead of indexed loop and add null check for data parameter"
                className="flex-1 input-field rounded-t-none resize-none font-sans text-sm leading-relaxed"
                style={{ borderRadius: '0 0 0.5rem 0.5rem' }}
              />
            </div>

          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 mb-6 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            <AlertCircle size={15} /> {error}
          </div>
        )}

        {/* Run button */}
        <button
          onClick={handleImplement}
          disabled={loading || !code.trim() || !comment.trim()}
          className="btn-primary w-full justify-center py-4 text-base rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <><Loader2 size={18} className="animate-spin" /> Implementing comment…</>
          ) : (
            <><Sparkles size={18} /> Implement Review Comment ({beams} beam{beams > 1 ? 's' : ''})</>
          )}
        </button>

        {/* Quick comment suggestions — below button */}
        <div className="mt-4 mb-8">
          <p className="text-xs text-gray-600 mb-3">Quick suggestions:</p>
          <div className="flex flex-wrap gap-2">
            {COMMENT_SUGGESTIONS.map(s => (
              <button
                key={s}
                onClick={() => setComment(s)}
                className="text-xs px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 text-blue-300 rounded-lg hover:bg-blue-500/20 transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Output */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-300">
              Generated Implementations
              {implementations.length > 0 && (
                <span className="ml-2 badge-green">{implementations.length} result{implementations.length > 1 ? 's' : ''}</span>
              )}
            </h2>
          </div>

          {loading && (
            <div className="flex flex-col items-center justify-center h-56 gap-4">
              <div className="relative">
                <div className="w-14 h-14 rounded-full border-4 border-blue-500/30 border-t-blue-500 animate-spin" />
                <MessageSquareCode size={20} className="text-blue-400 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
              </div>
              <div className="text-center">
                <p className="text-sm text-white font-medium">Implementing your comment…</p>
                <p className="text-xs text-gray-500 mt-1">Dual-encoder model processing code + comment</p>
              </div>
            </div>
          )}

          {!loading && implementations.length === 0 && (
            <div className="flex flex-col items-center justify-center h-56 gap-4 border-2 border-dashed border-white/10 rounded-xl p-8">
              <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center">
                <MessageSquareCode size={22} className="text-gray-600" />
              </div>
              <p className="text-sm text-gray-500 text-center max-w-xs leading-relaxed">
                Fill in the code and reviewer comment above, then click <strong className="text-gray-400">Implement Review Comment</strong>.
              </p>
            </div>
          )}

          {!loading && implementations.length > 0 && (
            <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-5">
              {implementations.map((impl) => (
                <ImplementationCard
                  key={impl.rank}
                  impl={impl}
                  isSelected={selected?.rank === impl.rank}
                  onSelect={setSelected}
                />
              ))}
            </div>
          )}
        </div>

        {/* Side-by-side comparison */}
        {selected && (
          <div className="mt-10 card">
            <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
              <Code2 size={14} className="text-blue-400" />
              Side-by-Side Comparison — Implementation #{selected.rank}
            </h3>
            <p className="text-xs text-gray-500 mb-5">
              Comment applied: <em className="text-blue-300">"{comment}"</em>
            </p>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider">Original Code</p>
                <pre className="code-block p-4 text-red-300/80 max-h-64 overflow-auto">
                  {code || '// (empty)'}
                </pre>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-2 font-medium uppercase tracking-wider">AI Implementation</p>
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
