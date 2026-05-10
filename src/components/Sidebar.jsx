import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Logo from './Logo'
import {
  LayoutDashboard,
  Code2,
  MessageSquareCode,
  History,
  Settings,
  LogOut,
  ChevronRight,
} from 'lucide-react'

const navItems = [
  {
    section: 'Workspace',
    items: [
      { label: 'Dashboard', icon: LayoutDashboard, to: '/dashboard' },
      { label: 'Contributor Mode', icon: Code2, to: '/workspace/contributor' },
      { label: 'Reviewer Mode', icon: MessageSquareCode, to: '/workspace/reviewer' },
    ],
  },
  {
    section: 'History',
    items: [
      { label: 'Review History', icon: History, to: '/history' },
    ],
  },
]

export default function Sidebar() {
  const location = useLocation()
  const { user, logout } = useAuth()

  const isActive = (to) => location.pathname === to

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-dark-200 border-r border-white/10 flex flex-col z-40">
      {/* Logo */}
      <div className="h-16 flex items-center px-5 border-b border-white/10">
        <Logo size="sm" />
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-6">
        {navItems.map((group) => (
          <div key={group.section}>
            <p className="section-label">{group.section}</p>
            <div className="space-y-0.5">
              {group.items.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className={isActive(item.to) ? 'sidebar-item-active' : 'sidebar-item'}
                >
                  <item.icon size={17} />
                  <span className="text-sm font-medium">{item.label}</span>
                  {isActive(item.to) && (
                    <ChevronRight size={14} className="ml-auto text-blue-400" />
                  )}
                </Link>
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* User */}
      <div className="border-t border-white/10 p-3 space-y-0.5">
        <button className="sidebar-item w-full">
          <Settings size={17} />
          <span className="text-sm font-medium">Settings</span>
        </button>
        <button onClick={logout} className="sidebar-item w-full text-red-400 hover:text-red-300 hover:bg-red-500/10">
          <LogOut size={17} />
          <span className="text-sm font-medium">Sign Out</span>
        </button>
        <div className="flex items-center gap-3 px-3 pt-3 mt-1 border-t border-white/10">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-sm font-bold">
            {user?.name?.[0]?.toUpperCase() ?? 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.name}</p>
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
          </div>
        </div>
      </div>
    </aside>
  )
}
