import { useState } from 'react'
import { Copy, Check, Maximize2 } from 'lucide-react'

export default function CodeEditor({
  value = '',
  onChange,
  placeholder = '// Paste your Java method here...',
  readOnly = false,
  label,
  language = 'java',
  height = '280px',
  showLineNumbers = true,
}) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    if (!value) return
    await navigator.clipboard.writeText(value)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const lines = value.split('\n')

  return (
    <div className="flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-dark-200 border-b border-white/10 rounded-t-lg">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <span className="w-3 h-3 rounded-full bg-red-500/70" />
            <span className="w-3 h-3 rounded-full bg-yellow-500/70" />
            <span className="w-3 h-3 rounded-full bg-green-500/70" />
          </div>
          {label && <span className="text-xs text-gray-500 ml-2 font-mono">{label}</span>}
        </div>
        <div className="flex items-center gap-1">
          <span className="badge-blue text-xs">{language}</span>
          <button
            onClick={handleCopy}
            className="btn-ghost text-xs py-1 px-2"
            title="Copy code"
          >
            {copied ? <Check size={13} className="text-green-400" /> : <Copy size={13} />}
          </button>
        </div>
      </div>

      {/* Editor area */}
      <div
        className="relative flex bg-dark-200 rounded-b-lg overflow-hidden border border-white/10 border-t-0"
        style={{ height }}
      >
        {/* Line numbers */}
        {showLineNumbers && (
          <div className="select-none py-4 px-3 text-right border-r border-white/10 text-gray-600 font-mono text-sm leading-6 min-w-[48px]">
            {(value || '\n').split('\n').map((_, i) => (
              <div key={i}>{i + 1}</div>
            ))}
          </div>
        )}

        {/* Textarea */}
        {readOnly ? (
          <pre className="flex-1 py-4 px-4 font-mono text-sm text-gray-300 leading-6 overflow-auto whitespace-pre">
            {value || <span className="text-gray-600">{placeholder}</span>}
          </pre>
        ) : (
          <textarea
            value={value}
            onChange={(e) => onChange?.(e.target.value)}
            placeholder={placeholder}
            spellCheck={false}
            className="flex-1 py-4 px-4 bg-transparent font-mono text-sm text-gray-300 leading-6 resize-none outline-none placeholder-gray-600 overflow-auto"
            style={{ height: '100%' }}
          />
        )}
      </div>
    </div>
  )
}
