import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Logo from './Logo'

export default function Navbar() {
  const { user, logout } = useAuth()
  const location = useLocation()

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/10 glass">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/">
          <Logo size="sm" />
        </Link>

        <div className="hidden md:flex items-center gap-1">
          <a href="#features" className="btn-ghost text-sm">Features</a>
          <a href="#how-it-works" className="btn-ghost text-sm">How It Works</a>
          <a href="#about" className="btn-ghost text-sm">About</a>
        </div>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <Link to="/dashboard" className="btn-ghost text-sm">Dashboard</Link>
              <button onClick={logout} className="btn-secondary text-sm py-2 px-4">Sign Out</button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-ghost text-sm">Log In</Link>
              <Link to="/signup" className="btn-primary text-sm py-2 px-4">Get Started</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
