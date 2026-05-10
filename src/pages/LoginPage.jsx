import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Logo from '../components/Logo'
import { Eye, EyeOff, ArrowRight, Loader2, Code2, MessageSquareCode, BarChart3 } from 'lucide-react'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login, loading } = useAuth()
  const [form, setForm] = useState({ email: '', password: '' })
  const [showPw, setShowPw] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e) => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!form.email || !form.password) {
      setError('Please enter your email and password.')
      return
    }
    const result = await login(form.email, form.password)
    if (result.success) {
      navigate('/dashboard')
    } else {
      setError(result.error || 'Invalid credentials. Please try again.')
    }
  }

  return (
    <div className="min-h-screen bg-dark-300 flex">
      {/* Left decorative panel */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-5/12 relative overflow-hidden bg-gradient-to-br from-dark-200 to-dark-300 border-r border-white/10 flex-col justify-center items-center p-12">
        {/* Background decoration */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-blue-600/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-48 h-48 bg-purple-600/10 rounded-full blur-3xl" />
        </div>

        <div className="relative w-full max-w-sm">
          <div className="mb-12">
            <Logo size="md" />
          </div>

          <h2 className="text-3xl font-bold text-white mb-4 leading-tight">
            Welcome back to<br />your workspace
          </h2>
          <p className="text-gray-400 mb-10 leading-relaxed text-sm">
            Submit Java methods, get instant AI-powered suggestions, and improve your code review workflow.
          </p>

          {/* Feature cards */}
          <div className="space-y-3">
            {[
              { icon: Code2, color: 'blue', title: 'Contributor Mode', desc: 'Auto-suggest improvements' },
              { icon: MessageSquareCode, color: 'purple', title: 'Reviewer Mode', desc: 'Implement review comments' },
              { icon: BarChart3, color: 'green', title: 'Multi-Beam Output', desc: 'Up to 10 ranked suggestions' },
            ].map((item) => {
              const colorMap = {
                blue: 'bg-blue-500/20 text-blue-400',
                purple: 'bg-purple-500/20 text-purple-400',
                green: 'bg-green-500/20 text-green-400',
              }
              return (
                <div key={item.title} className="flex items-center gap-4 p-4 bg-white/5 rounded-xl border border-white/10">
                  <div className={`w-9 h-9 rounded-lg ${colorMap[item.color]} flex items-center justify-center flex-shrink-0`}>
                    <item.icon size={17} />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">{item.title}</p>
                    <p className="text-xs text-gray-500">{item.desc}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md">
          <div className="lg:hidden mb-8">
            <Logo size="md" />
          </div>

          <h1 className="text-2xl font-bold text-white mb-2">Sign in to your account</h1>
          <p className="text-gray-400 mb-8 text-sm">
            Don't have an account?{' '}
            <Link to="/signup" className="text-blue-400 hover:text-blue-300 font-medium">Create one free</Link>
          </p>

          {error && (
            <div className="mb-5 px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Email Address</label>
              <input
                name="email"
                type="email"
                autoComplete="email"
                value={form.email}
                onChange={handleChange}
                placeholder="you@example.com"
                className="input-field"
                autoFocus
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-sm font-medium text-gray-300">Password</label>
                <button type="button" className="text-xs text-blue-400 hover:text-blue-300">
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <input
                  name="password"
                  type={showPw ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={form.password}
                  onChange={handleChange}
                  placeholder="Your password"
                  className="input-field pr-11"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(s => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showPw ? <EyeOff size={17} /> : <Eye size={17} />}
                </button>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <input
                id="remember"
                type="checkbox"
                className="w-4 h-4 rounded accent-blue-500"
              />
              <label htmlFor="remember" className="text-sm text-gray-400">Remember me for 30 days</label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center text-base py-3 mt-2 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? (
                <><Loader2 size={18} className="animate-spin" /> Signing in…</>
              ) : (
                <>Sign In <ArrowRight size={18} /></>
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-white/10 text-center">
            <p className="text-xs text-gray-600">
              For demo purposes, any email and password (8+ chars) will work.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
