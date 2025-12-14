'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState } from 'react'
import './globals.css'
import Link from 'next/link'
import { Film, Home, Settings, ListVideo, FileText } from 'lucide-react'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background font-sans antialiased">
        <QueryClientProvider client={queryClient}>
          <div className="flex h-screen">
            {/* Sidebar */}
            <aside className="w-64 border-r bg-muted/40">
              <div className="flex h-16 items-center border-b px-6">
                <Film className="mr-2 h-6 w-6" />
                <h1 className="text-xl font-bold">VeoFlow Studio</h1>
              </div>
              <nav className="p-4 space-y-2">
                <Link
                  href="/"
                  className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent"
                >
                  <Home className="h-4 w-4" />
                  Projects
                </Link>
                <Link
                  href="/queue"
                  className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent"
                >
                  <ListVideo className="h-4 w-4" />
                  Render Queue
                </Link>
                <Link
                  href="/settings"
                  className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent"
                >
                  <Settings className="h-4 w-4" />
                  Settings
                </Link>
                <Link
                  href="/logs"
                  className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium hover:bg-accent"
                >
                  <FileText className="h-4 w-4" />
                  Logs
                </Link>
              </nav>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto">
              {children}
            </main>
          </div>
        </QueryClientProvider>
      </body>
    </html>
  )
}
