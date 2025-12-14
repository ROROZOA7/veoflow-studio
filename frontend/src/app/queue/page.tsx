'use client'

import { useQueueStats } from '@/hooks/useRender'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, ListVideo, CheckCircle2, Clock } from 'lucide-react'

export default function QueuePage() {
  const { stats, isLoading } = useQueueStats()

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <ListVideo className="h-8 w-8" />
          Render Queue
        </h1>
        <p className="text-muted-foreground mt-2">
          Monitor active render tasks and queue statistics
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Tasks</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.active || 0}</div>
            <p className="text-xs text-muted-foreground">Currently processing</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scheduled</CardTitle>
            <ListVideo className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.scheduled || 0}</div>
            <p className="text-xs text-muted-foreground">Waiting in queue</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Reserved</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.reserved || 0}</div>
            <p className="text-xs text-muted-foreground">Reserved by workers</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Workers</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.workers || 0}</div>
            <p className="text-xs text-muted-foreground">Active workers</p>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Queue Information</CardTitle>
          <CardDescription>
            Real-time status of the render queue and workers
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Queue Status:</span>
              <span className="font-medium">
                {stats && (stats.active > 0 || stats.scheduled > 0) ? 'Active' : 'Idle'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total Tasks:</span>
              <span className="font-medium">
                {(stats?.active || 0) + (stats?.scheduled || 0) + (stats?.reserved || 0)}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

