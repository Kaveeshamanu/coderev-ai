import { useState } from 'react'
import WorkspaceLayout from '../components/WorkspaceLayout'
import { useHistory } from '../context/HistoryContext'
import {
  History, Code2, MessageSquareCode, Search,
  ChevronDown, Clock, CheckCircle2,
  Star, Eye,
} from 'lucide-react'

function ScorePill({ score }) {
  const color = score >= 90 ? 'text-green-400 bg-green-500/10 border-green-500/20'
    : score >= 70 ? 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20'
    : 'text-red-400 bg-red-500/10 border-red-500/20'
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${color}`}>
      <Star size={10} fill="currentColor" />
      {score}%
    </span>
  )
}

export default function HistoryPage() {
  const { history: ALL_HISTORY } = useHistory()
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all') // all | contributor | reviewer
  const [expanded, setExpanded] = useState(null)

  const filtered = ALL_HISTORY.filter(h => {
    if (filter !== 'all' && h.mode !== filter) return false
    if (search && !h.method.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const stats = {
    total: ALL_HISTORY.length,
    contributor: ALL_HISTORY.filter(h => h.mode === 'contributor').length,
    reviewer: ALL_HISTORY.filter(h => h.mode === 'reviewer').length,
    avgScore: Math.round(ALL_HISTORY.reduce((a, h) => a + h.topScore, 0) / ALL_HISTORY.length),
  }

  return (
    <WorkspaceLayout>
      <div className="p-8 max-w-5xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
              <History size={16} className="text-gray-400" />
            </div>
            <h1 className="text-2xl font-bold text-white">Review History</h1>
          </div>
          <p className="text-sm text-gray-400">All your past code reviews and AI suggestions.</p>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Reviews', value: stats.total, color: 'text-white' },
            { label: 'Contributor', value: stats.contributor, color: 'text-blue-400' },
            { label: 'Reviewer', value: stats.reviewer, color: 'text-purple-400' },
            { label: 'Avg Confidence', value: `${stats.avgScore}%`, color: 'text-green-400' },
          ].map(s => (
            <div key={s.label} className="card text-center">
              <p className={`text-3xl font-bold mb-1 ${s.color}`}>{s.value}</p>
              <p className="text-xs text-gray-500">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 mb-5 flex-wrap">
          <div className="relative flex-1 min-w-[200px]">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              placeholder="Search by method name…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input-field pl-9 py-2.5 text-sm"
            />
          </div>
          <div className="flex gap-2">
            {['all', 'contributor', 'reviewer'].map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-2 rounded-lg text-sm font-medium border transition-colors capitalize ${
                  filter === f
                    ? 'bg-white/10 border-white/20 text-white'
                    : 'border-white/10 text-gray-500 hover:text-white hover:border-white/20'
                }`}
              >
                {f === 'all' ? 'All' : f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="card p-0 overflow-hidden">
          {/* Header */}
          <div className="grid grid-cols-12 gap-4 px-5 py-3 border-b border-white/10 bg-dark-200/70">
            <div className="col-span-1 text-xs font-medium text-gray-500 uppercase tracking-wider">Mode</div>
            <div className="col-span-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Method</div>
            <div className="col-span-2 text-xs font-medium text-gray-500 uppercase tracking-wider">Date</div>
            <div className="col-span-2 text-xs font-medium text-gray-500 uppercase tracking-wider">Beams</div>
            <div className="col-span-2 text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</div>
            <div className="col-span-1 text-xs font-medium text-gray-500 uppercase tracking-wider"></div>
          </div>

          {ALL_HISTORY.length === 0 && (
            <div className="text-center py-16 text-gray-500 text-sm">
              No reviews yet. Run a review in the Contributor or Reviewer workspace to see your history here.
            </div>
          )}
          {ALL_HISTORY.length > 0 && filtered.length === 0 && (
            <div className="text-center py-16 text-gray-500 text-sm">No reviews match your filter.</div>
          )}

          {filtered.map((item) => (
            <div key={item.id} className="border-b border-white/5 last:border-0">
              {/* Row */}
              <div
                className="grid grid-cols-12 gap-4 px-5 py-4 hover:bg-white/5 transition-colors cursor-pointer items-center"
                onClick={() => setExpanded(expanded === item.id ? null : item.id)}
              >
                <div className="col-span-1">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    item.mode === 'contributor' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'
                  }`}>
                    {item.mode === 'contributor' ? <Code2 size={14} /> : <MessageSquareCode size={14} />}
                  </div>
                </div>
                <div className="col-span-4">
                  <p className="text-sm text-white font-mono truncate">{item.method}</p>
                  <div className="flex gap-1 mt-1">
                    {item.tags.slice(0, 2).map(t => (
                      <span key={t} className={`text-[9px] px-1.5 py-0.5 rounded-full border ${
                        item.mode === 'contributor'
                          ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                          : 'bg-purple-500/10 text-purple-400 border-purple-500/20'
                      }`}>{t}</span>
                    ))}
                  </div>
                </div>
                <div className="col-span-2">
                  <p className="text-xs text-gray-400 flex items-center gap-1">
                    <Clock size={11} />
                    {item.date.split(' ')[0]}
                  </p>
                  <p className="text-xs text-gray-600">{item.date.split(' ')[1]}</p>
                </div>
                <div className="col-span-2">
                  <span className="badge-blue text-xs">{item.beams} beam{item.beams > 1 ? 's' : ''}</span>
                </div>
                <div className="col-span-2">
                  <ScorePill score={item.topScore} />
                </div>
                <div className="col-span-1 flex items-center justify-end gap-1">
                  <ChevronDown
                    size={15}
                    className={`text-gray-500 transition-transform ${expanded === item.id ? 'rotate-180' : ''}`}
                  />
                </div>
              </div>

              {/* Expanded detail */}
              {expanded === item.id && (
                <div className="px-5 pb-4 pt-2 bg-dark-300/30 border-t border-white/5">
                  {item.comment && (
                    <div className="mb-3 p-3 bg-purple-500/5 border border-purple-500/20 rounded-lg">
                      <p className="text-xs text-gray-500 mb-1">Reviewer comment:</p>
                      <p className="text-sm text-purple-300 italic">"{item.comment}"</p>
                    </div>
                  )}
                  <div className="flex items-center gap-2">
                    <span className="badge-green text-xs flex items-center gap-1">
                      <CheckCircle2 size={11} /> Completed
                    </span>
                    <button className="btn-ghost text-xs gap-1.5 py-1">
                      <Eye size={12} /> View suggestions
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </WorkspaceLayout>
  )
}
