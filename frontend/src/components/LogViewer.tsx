'use client'

import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { Loader2, RefreshCw, Trash2, AlertCircle, Info, XCircle, CheckCircle } from 'lucide-react'

interface LogEntry {
  timestamp: string
  level: string
  logger: string
  message: string
  extra: any
}

export function LogViewer() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [filterLevel, setFilterLevel] = useState<string>('')
  const [filterLogger, setFilterLogger] = useState<string>('')
  const logEndRef = useRef<HTMLDivElement>(null)

  const loadLogs = async () => {
    try {
      setLoading(true)
      const params: any = { limit: 200 }
      if (filterLevel) params.level = filterLevel
      if (filterLogger) params.logger_name = filterLogger
      
      const response = await api.logs.getLogs(params)
      setLogs(response.logs || [])
    } catch (error) {
      console.error('Failed to load logs:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadLogs()
    
    if (autoRefresh) {
      const interval = setInterval(loadLogs, 2000) // Refresh every 2 seconds
      return () => clearInterval(interval)
    }
  }, [autoRefresh, filterLevel, filterLogger])

  useEffect(() => {
    // Auto-scroll to bottom when new logs arrive
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  const clearLogs = async () => {
    if (!confirm('Are you sure you want to clear all logs?')) return
    
    try {
      await api.logs.clearLogs()
      setLogs([])
    } catch (error) {
      console.error('Failed to clear logs:', error)
    }
  }

  const getLevelIcon = (level: string) => {
    switch (level.toUpperCase()) {
      case 'ERROR':
      case 'CRITICAL':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'WARNING':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />
      case 'INFO':
        return <Info className="h-4 w-4 text-blue-500" />
      default:
        return <CheckCircle className="h-4 w-4 text-gray-500" />
    }
  }

  const getLevelColor = (level: string) => {
    switch (level.toUpperCase()) {
      case 'ERROR':
      case 'CRITICAL':
        return 'text-red-400 bg-red-900/20 border-red-800'
      case 'WARNING':
        return 'text-yellow-400 bg-yellow-900/20 border-yellow-800'
      case 'INFO':
        return 'text-blue-400 bg-blue-900/20 border-blue-800'
      default:
        return 'text-gray-400 bg-gray-900/20 border-gray-800'
    }
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Application Logs</CardTitle>
            <CardDescription>Real-time application logs for debugging</CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadLogs}
              disabled={loading}
            >
              {loading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4 mr-2" />
              )}
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={clearLogs}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear
            </Button>
            <Button
              variant={autoRefresh ? 'default' : 'outline'}
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              {autoRefresh ? 'Auto: ON' : 'Auto: OFF'}
            </Button>
          </div>
        </div>
        
        {/* Filters */}
        <div className="flex gap-2 mt-4">
          <select
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value)}
            className="flex h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
          >
            <option value="">All Levels</option>
            <option value="DEBUG">DEBUG</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
          <input
            type="text"
            value={filterLogger}
            onChange={(e) => setFilterLogger(e.target.value)}
            placeholder="Filter by logger name..."
            className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm"
          />
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto bg-black rounded-lg p-4 font-mono text-sm">
          {logs.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              No logs available
            </div>
          ) : (
            <div className="space-y-1">
              {logs.map((log, index) => (
                <div
                  key={index}
                  className={`p-2 rounded border-l-2 ${getLevelColor(log.level)}`}
                >
                  <div className="flex items-start gap-2">
                    {getLevelIcon(log.level)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs opacity-70">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        <span className="text-xs font-semibold opacity-90">
                          [{log.level}]
                        </span>
                        <span className="text-xs opacity-60 truncate">
                          {log.logger}
                        </span>
                      </div>
                      <div className="mt-1 break-words">
                        {log.message}
                      </div>
                      {log.extra && Object.keys(log.extra).length > 0 && (
                        <div className="mt-1 text-xs opacity-60">
                          {Object.entries(log.extra).map(([key, value]) => (
                            <span key={key} className="mr-3">
                              <strong>{key}:</strong> {String(value)}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

