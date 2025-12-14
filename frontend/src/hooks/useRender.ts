import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useRenderTask(taskId: string | null) {
  const query = useQuery({
    queryKey: ['render', taskId],
    queryFn: async () => {
      if (!taskId) return null
      return await api.render.getTaskStatus(taskId)
    },
    enabled: !!taskId,
    refetchInterval: (query) => {
      // Poll every 2 seconds if task is still pending/processing
      const data = query.state.data as any
      if (data?.status === 'PENDING' || data?.status === 'STARTED') {
        return 2000
      }
      return false
    },
  })

  return {
    task: query.data,
    isLoading: query.isLoading,
    error: query.error,
    status: query.data?.status,
    isComplete: query.data?.status === 'SUCCESS',
    isFailed: query.data?.status === 'FAILURE',
  }
}

export function useQueueStats() {
  const query = useQuery({
    queryKey: ['queue', 'stats'],
    queryFn: () => api.queue.stats(),
    refetchInterval: 5000, // Poll every 5 seconds
  })

  return {
    stats: query.data,
    isLoading: query.isLoading,
    error: query.error,
  }
}

