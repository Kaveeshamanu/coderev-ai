import { Link } from 'react-router-dom'
import WorkspaceLayout from '../components/WorkspaceLayout'
import { useAuth } from '../context/AuthContext'
import { useHistory } from '../context/HistoryContext'
import {
  Code2, MessageSquareCode, History, ArrowRight,
  Zap, TrendingUp, Clock, CheckCircle2, Sparkles,
  ChevronRight, FileCode2,
} from 'lucide-react'

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins} min ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} hr${hrs > 1 ? 's' : ''} ago`
  const days = Math.floor(hrs / 24)
  if (days === 1) return 'Yesterday'
  return `${days} days ago`
}

export default function Dashboard() {
  const { user } = useAuth()
  const { history } = useHistory()
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  const now = Date.now()
  const oneWeekAgo = now - 7 * 24 * 60 * 60 * 1000
  const thisWeek = history.filter(h => new Date(h.date).getTime() >= oneWeekAgo).length
  const avgScore = history.length
    ? Math.round(history.reduce((a, h) => a + h.topScore, 0) / history.length)
    : 0

  const quickStats = [
    { label: 'Total Reviews', value: String(history.length), icon: FileCode2, color: 'blue' },
    { label: 'Avg Confidence', value: history.length ? `${avgScore}%` : '—', icon: Zap, color: 'orange' },
    { label: 'Contributor', value: String(history.filter(h => h.mode === 'contributor').length), icon: CheckCircle2, color: 'green' },
    { label: 'This Week', value: String(thisWeek), icon: TrendingUp, color: 'purple' },
  ]

  const recentActivity = history.slice(0, 4)

  return (
    <WorkspaceLayout>
      <div className="p-8 max-w-5xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-3">
            <Sparkles size={13} />
            <span>Neural Machine Translation for Java Code Reviews</span>
          </div>
          <h1 className="text-3xl font-bold text-white mb-1">
            {greeting}, {user?.name?.split(' ')[0]} 👋
          </h1>
          <p className="text-gray-400">Choose a workspace to get started or continue where you left off.</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {quickStats.map((s) => {
            const colorMap = {
              blue: 'from-blue-500/10 to-transparent text-blue-400 border-blue-500/20',
              orange: 'from-orange-500/10 to-transparent text-orange-400 border-orange-500/20',
              green: 'from-green-500/10 to-transparent text-green-400 border-green-500/20',
              purple: 'from-purple-500/10 to-transparent text-purple-400 border-purple-500/20',
            }
            const cls = colorMap[s.color]
            return (
              <div key={s.label} className={`card bg-gradient-to-br ${cls} border`}>
                <div className="flex items-start justify-between mb-3">
                  <s.icon size={18} className={cls.split(' ').at(-1)} />
                </div>
                <p className="text-2xl font-bold text-white mb-0.5">{s.value}</p>
                <p className="text-xs text-gray-500">{s.label}</p>
              </div>
            )
          })}
        </div>

        {/* Workspace cards */}
        <div className="grid md:grid-cols-2 gap-5 mb-8">
          {/* Contributor Mode */}
          <Link to="/workspace/contributor" className="group card border-blue-500/20 hover:border-blue-400/40 hover:bg-surface-200 transition-all duration-200 cursor-pointer">
            <div className="flex items-start justify-between mb-5">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/30 to-blue-600/10 border border-blue-500/30 flex items-center justify-center">
                <Code2 size={22} className="text-blue-400" />
              </div>
              <span className="badge-blue">Single-Encoder</span>
            </div>
            <h2 className="text-lg font-semibold text-white mb-2">Contributor Mode</h2>
            <p className="text-sm text-gray-400 mb-5 leading-relaxed">
              Paste a Java method and let the AI suggest improvements automatically — no reviewer comment needed.
            </p>
            <ul className="space-y-2 mb-6">
              {['Automatic improvement detection', 'Up to 10 ranked suggestions', 'Side-by-side diff view', 'Copy suggestion instantly'].map(f => (
                <li key={f} className="flex items-center gap-2 text-xs text-gray-400">
                  <CheckCircle2 size={13} className="text-blue-400" />
                  {f}
                </li>
              ))}
            </ul>
            <div className="flex items-center gap-2 text-blue-400 text-sm font-medium group-hover:gap-3 transition-all">
              Open Contributor Workspace <ArrowRight size={15} />
            </div>
          </Link>

          {/* Reviewer Mode */}
          <Link to="/workspace/reviewer" className="group card border-purple-500/20 hover:border-purple-400/40 hover:bg-surface-200 transition-all duration-200 cursor-pointer">
            <div className="flex items-start justify-between mb-5">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500/30 to-purple-600/10 border border-purple-500/30 flex items-center justify-center">
                <MessageSquareCode size={22} className="text-purple-400" />
              </div>
              <span className="badge-purple">Dual-Encoder</span>
            </div>
            <h2 className="text-lg font-semibold text-white mb-2">Reviewer Mode</h2>
            <p className="text-sm text-gray-400 mb-5 leading-relaxed">
              Provide both a Java method and a natural language reviewer comment to generate an automatic implementation.
            </p>
            <ul className="space-y-2 mb-6">
              {['Natural language comment input', 'Comment-driven code generation', 'Multiple implementation options', 'BLEU-4 & accuracy metrics'].map(f => (
                <li key={f} className="flex items-center gap-2 text-xs text-gray-400">
                  <CheckCircle2 size={13} className="text-purple-400" />
                  {f}
                </li>
              ))}
            </ul>
            <div className="flex items-center gap-2 text-purple-400 text-sm font-medium group-hover:gap-3 transition-all">
              Open Reviewer Workspace <ArrowRight size={15} />
            </div>
          </Link>
        </div>

        {/* Recent Activity */}
        <div className="card">
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-semibold text-white flex items-center gap-2">
              <History size={17} className="text-gray-400" />
              Recent Activity
            </h2>
            <Link to="/history" className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1">
              View all <ChevronRight size={13} />
            </Link>
          </div>

          {recentActivity.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-6">No reviews yet. Run one to see activity here.</p>
          ) : (
            <div className="space-y-3">
              {recentActivity.map((item) => (
                <div key={item.id} className="flex items-center gap-4 p-3 bg-dark-300/50 rounded-lg hover:bg-dark-300 transition-colors">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    item.mode === 'contributor' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'
                  }`}>
                    {item.mode === 'contributor' ? <Code2 size={14} /> : <MessageSquareCode size={14} />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white font-mono truncate">{item.method}</p>
                    <p className="text-xs text-gray-500 capitalize">{item.mode} mode · {item.beams} beam{item.beams > 1 ? 's' : ''}</p>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <span className="badge-green text-[10px]">
                      <CheckCircle2 size={10} /> Done
                    </span>
                    <span className="text-xs text-gray-600 flex items-center gap-1">
                      <Clock size={11} /> {timeAgo(item.date)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </WorkspaceLayout>
  )
}
