import Sidebar from './Sidebar'

export default function WorkspaceLayout({ children }) {
  return (
    <div className="min-h-screen bg-dark-300 flex">
      <Sidebar />
      <main className="flex-1 ml-64 min-h-screen overflow-y-auto">
        {children}
      </main>
    </div>
  )
}
