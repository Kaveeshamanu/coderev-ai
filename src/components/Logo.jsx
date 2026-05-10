export default function Logo({ size = 'md', showText = true }) {
  const sizes = {
    sm: { icon: 28, text: 'text-base' },
    md: { icon: 36, text: 'text-xl' },
    lg: { icon: 48, text: 'text-2xl' },
  }
  const s = sizes[size]

  return (
    <div className="flex items-center gap-2.5">
      <svg width={s.icon} height={s.icon} viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="36" height="36" rx="10" fill="url(#logoGrad)" />
        <path d="M10 14l5-5 5 5" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M15 9v14" stroke="white" strokeWidth="2.2" strokeLinecap="round"/>
        <path d="M20 22l6-4-6-4" stroke="rgba(255,255,255,0.7)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
        <defs>
          <linearGradient id="logoGrad" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
            <stop stopColor="#3b82f6"/>
            <stop offset="1" stopColor="#8b5cf6"/>
          </linearGradient>
        </defs>
      </svg>
      {showText && (
        <span className={`font-bold ${s.text} text-white tracking-tight`}>
          CodeRev<span className="text-gradient"> AI</span>
        </span>
      )}
    </div>
  )
}
