import { createContext, useContext, useState } from 'react'

const HistoryContext = createContext(null)

function extractMethodName(code) {
  const line = code.split('\n').find(l => l.includes('(') && l.includes(')'))
  if (!line) return 'Unknown method'
  const match = line.trim().match(/(\w+\s*\([^)]*\))/)
  return match ? match[1].trim() : line.trim().slice(0, 60)
}

function formatDate(ts) {
  const d = new Date(ts)
  const date = d.toISOString().slice(0, 10)
  const time = d.toTimeString().slice(0, 5)
  return `${date} ${time}`
}

export function HistoryProvider({ children }) {
  const [history, setHistory] = useState(() => {
    try {
      const stored = localStorage.getItem('coderev_history')
      return stored ? JSON.parse(stored) : []
    } catch {
      return []
    }
  })

  const addEntry = (entry) => {
    setHistory(prev => {
      const next = [entry, ...prev]
      localStorage.setItem('coderev_history', JSON.stringify(next))
      return next
    })
  }

  const clearHistory = () => {
    setHistory([])
    localStorage.removeItem('coderev_history')
  }

  return (
    <HistoryContext.Provider value={{ history, addEntry, clearHistory, extractMethodName, formatDate }}>
      {children}
    </HistoryContext.Provider>
  )
}

export const useHistory = () => {
  const ctx = useContext(HistoryContext)
  if (!ctx) throw new Error('useHistory must be used within HistoryProvider')
  return ctx
}
