import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import {
  Code2, MessageSquareCode, Zap, Shield, BarChart3,
  ArrowRight, Github, Star, ChevronRight, Layers, Brain,
  CheckCircle2, Users, Sparkles,
} from 'lucide-react'

const features = [
  {
    icon: Code2,
    color: 'blue',
    title: 'Contributor Mode',
    desc: 'Submit your Java method and receive automated improvement suggestions without needing a human reviewer.',
    badge: 'Single-Encoder Model',
  },
  {
    icon: MessageSquareCode,
    color: 'purple',
    title: 'Reviewer Mode',
    desc: 'Paste a reviewer comment alongside the code and get an automatically implemented version in seconds.',
    badge: 'Dual-Encoder Model',
  },
  {
    icon: BarChart3,
    color: 'green',
    title: 'Multi-Beam Suggestions',
    desc: 'Get up to 10 ranked candidate solutions using beam search, giving you options rather than a single prescription.',
    badge: 'Beam Search',
  },
  {
    icon: Zap,
    color: 'orange',
    title: 'Instant Feedback',
    desc: 'Predictions generated in 5–10 seconds so you can iterate quickly without breaking your flow.',
    badge: '< 10s',
  },
  {
    icon: Shield,
    color: 'blue',
    title: 'Method-Level Analysis',
    desc: 'Focused, manageable recommendations at the individual method level — not overwhelming file-level dumps.',
    badge: 'Java',
  },
  {
    icon: Brain,
    color: 'purple',
    title: 'Transformer Architecture',
    desc: 'Trained on thousands of real GitHub and Gerrit code reviews using state-of-the-art NMT techniques.',
    badge: 'Deep Learning',
  },
]

const steps = [
  { step: '01', title: 'Paste Your Method', desc: 'Copy your Java method into the editor. The system abstracts identifiers automatically.' },
  { step: '02', title: 'Choose Your Mode', desc: 'Select Contributor Mode for auto-review, or Reviewer Mode to implement a specific comment.' },
  { step: '03', title: 'Get Suggestions', desc: 'Receive ranked candidate suggestions with highlighted diffs in under 10 seconds.' },
  { step: '04', title: 'Apply & Iterate', desc: 'Copy your preferred suggestion, apply it, and continue building with confidence.' },
]

const metrics = [
  { value: '≥45%', label: 'Contributor accuracy', sub: 'perfect predictions' },
  { value: '≥40%', label: 'Reviewer accuracy', sub: 'perfect predictions' },
  { value: '<10s', label: 'Inference time', sub: 'per prediction' },
  { value: '0.85+', label: 'BLEU-4 score', sub: 'translation quality' },
]

const sampleCode = `public int calculateSum(int[] arr) {
  int sum = 0;
  for (int i : arr) {
    sum = sum + i;
  }
  return sum;
}`

const sampleSuggestion = `public int calculateSum(int[] arr) {
  return Arrays.stream(arr).sum();
}`

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-dark-300">
      <Navbar />

      {/* Hero */}
      <section className="relative pt-32 pb-24 overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-gradient-radial from-blue-600/10 via-purple-600/5 to-transparent rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-7xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-blue-500/10 border border-blue-500/30 rounded-full text-blue-400 text-sm mb-8 animate-fade-in">
            <Sparkles size={14} />
            Deep Learning-Based Code Review for Java
          </div>

          <h1 className="text-5xl md:text-7xl font-bold text-white leading-tight mb-6 animate-slide-up">
            Smarter code reviews,
            <br />
            <span className="text-gradient">powered by AI</span>
          </h1>

          <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed animate-slide-up">
            CodeRev AI uses Transformer-based deep learning to automatically suggest code improvements
            and implement reviewer comments — trained on thousands of real-world Java code reviews.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-slide-up">
            <Link to="/signup" className="btn-primary text-base px-7 py-3 glow-blue">
              Start Reviewing Free
              <ArrowRight size={18} />
            </Link>
            <Link to="/login" className="btn-secondary text-base px-7 py-3">
              Sign In
            </Link>
          </div>

          {/* Code preview */}
          <div className="mt-20 max-w-4xl mx-auto animate-fade-in">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
              {/* Input */}
              <div className="rounded-xl overflow-hidden border border-white/10 shadow-2xl">
                <div className="flex items-center gap-2 px-4 py-3 bg-dark-200 border-b border-white/10">
                  <div className="flex gap-1.5">
                    <span className="w-3 h-3 rounded-full bg-red-500/70" />
                    <span className="w-3 h-3 rounded-full bg-yellow-500/70" />
                    <span className="w-3 h-3 rounded-full bg-green-500/70" />
                  </div>
                  <span className="text-xs text-gray-500 font-mono ml-2">Original.java</span>
                  <span className="ml-auto badge-orange">Input</span>
                </div>
                <pre className="p-5 bg-dark-200 font-mono text-sm text-gray-300 leading-6 overflow-auto">
                  {sampleCode}
                </pre>
              </div>

              {/* Output */}
              <div className="rounded-xl overflow-hidden border border-blue-500/30 shadow-2xl shadow-blue-500/10">
                <div className="flex items-center gap-2 px-4 py-3 bg-dark-200 border-b border-blue-500/20">
                  <div className="flex gap-1.5">
                    <span className="w-3 h-3 rounded-full bg-red-500/70" />
                    <span className="w-3 h-3 rounded-full bg-yellow-500/70" />
                    <span className="w-3 h-3 rounded-full bg-green-500/70" />
                  </div>
                  <span className="text-xs text-gray-500 font-mono ml-2">Suggested.java</span>
                  <span className="ml-auto badge-green">AI Suggestion</span>
                </div>
                <pre className="p-5 bg-dark-200 font-mono text-sm text-green-300 leading-6 overflow-auto">
                  {sampleSuggestion}
                </pre>
              </div>
            </div>
            <p className="text-xs text-gray-600 mt-3 text-center">
              AI detects opportunity to replace manual loop with streams — instantly.
            </p>
          </div>
        </div>
      </section>

      {/* Metrics */}
      <section className="py-12 border-y border-white/10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {metrics.map((m) => (
              <div key={m.label} className="text-center">
                <p className="text-3xl md:text-4xl font-bold text-gradient mb-1">{m.value}</p>
                <p className="text-sm font-medium text-white">{m.label}</p>
                <p className="text-xs text-gray-500">{m.sub}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Everything you need for better code reviews
            </h2>
            <p className="text-gray-400 max-w-xl mx-auto">
              Two AI models trained on real-world code review data, wrapped in an intuitive interface.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {features.map((f) => {
              const colorMap = {
                blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/20 text-blue-400',
                purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/20 text-purple-400',
                green: 'from-green-500/20 to-green-600/10 border-green-500/20 text-green-400',
                orange: 'from-orange-500/20 to-orange-600/10 border-orange-500/20 text-orange-400',
              }
              const cls = colorMap[f.color]
              return (
                <div key={f.title} className="card-hover group">
                  <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${cls} border flex items-center justify-center mb-4`}>
                    <f.icon size={20} className={cls.split(' ').at(-1)} />
                  </div>
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-white">{f.title}</h3>
                    <span className="badge-blue text-[10px] ml-2 mt-0.5">{f.badge}</span>
                  </div>
                  <p className="text-sm text-gray-400 leading-relaxed">{f.desc}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-24 bg-dark-200/50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">How it works</h2>
            <p className="text-gray-400 max-w-xl mx-auto">From code paste to AI suggestion in four simple steps.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {steps.map((s, i) => (
              <div key={s.step} className="relative card">
                <span className="text-6xl font-black text-white/5 absolute top-4 right-4 leading-none">{s.step}</span>
                <div className="w-10 h-10 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 font-bold text-sm mb-4">
                  {s.step}
                </div>
                <h3 className="font-semibold text-white mb-2">{s.title}</h3>
                <p className="text-sm text-gray-400 leading-relaxed">{s.desc}</p>
                {i < steps.length - 1 && (
                  <div className="hidden lg:block absolute -right-3 top-1/2 -translate-y-1/2 z-10">
                    <ChevronRight size={20} className="text-gray-600" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* About / Research */}
      <section id="about" className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <span className="badge-purple mb-4 inline-flex">Final Year Research Project</span>
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-6 leading-tight">
                Built on state-of-the-art<br />Transformer research
              </h2>
              <p className="text-gray-400 mb-6 leading-relaxed">
                This system is the result of a BSc Software Engineering final year project at
                Plymouth University, exploring how Neural Machine Translation techniques can
                automate routine aspects of code review.
              </p>
              <ul className="space-y-3">
                {[
                  'Two Transformer models (single-encoder & dual-encoder)',
                  'Trained on GitHub and Gerrit Java code reviews',
                  'Method-level code abstraction and normalization',
                  'BLEU-4, Levenshtein & exact-match evaluation',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm text-gray-300">
                    <CheckCircle2 size={16} className="text-green-400 mt-0.5 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-4">
              <div className="card border-blue-500/20">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                    <Code2 size={18} className="text-blue-400" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-white mb-1">Model 1 — Contributor Side</h4>
                    <p className="text-sm text-gray-400">Single-encoder architecture that suggests improvements to submitted code without any reviewer input.</p>
                  </div>
                </div>
              </div>
              <div className="card border-purple-500/20">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                    <MessageSquareCode size={18} className="text-purple-400" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-white mb-1">Model 2 — Reviewer Side</h4>
                    <p className="text-sm text-gray-400">Dual-encoder architecture that takes a natural language review comment and automatically implements it.</p>
                  </div>
                </div>
              </div>
              <div className="card border-green-500/20">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-xl bg-green-500/20 flex items-center justify-center flex-shrink-0">
                    <Layers size={18} className="text-green-400" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-white mb-1">Real-World Training Data</h4>
                    <p className="text-sm text-gray-400">Models trained on curated Java method-level triplets: original code, reviewer comment, and revised code.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 bg-dark-200/50">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <div className="card border-blue-500/20 py-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Ready to streamline your code reviews?
            </h2>
            <p className="text-gray-400 mb-8">
              Sign up free and start getting AI-powered suggestions for your Java methods today.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/signup" className="btn-primary text-base px-8 py-3 glow-blue">
                Get Started Free
                <ArrowRight size={18} />
              </Link>
              <Link to="/login" className="btn-ghost text-base px-6 py-3">
                Already have an account?
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-8">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-gray-600">
            © 2024 CodeRev AI — Final Year Project · BSc Software Engineering · Plymouth University
          </p>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span>PUSL3190 Computing Project</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
