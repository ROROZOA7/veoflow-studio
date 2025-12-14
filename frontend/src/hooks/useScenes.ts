import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useSceneStore } from '@/store/sceneStore'

export function useScenes(projectId: string | null) {
  const { scenes, setScenes } = useSceneStore()
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: ['scenes', projectId],
    queryFn: async () => {
      if (!projectId) return []
      const data = await api.scenes.list(projectId)
      setScenes(data)
      return data
    },
    enabled: !!projectId,
  })

  const createMutation = useMutation({
    mutationFn: (data: { project_id: string; number: number; prompt: string; script?: string }) =>
      api.scenes.create(data),
    onSuccess: async (newScene) => {
      // Wait for refetch to complete to ensure UI updates
      await queryClient.refetchQueries({ queryKey: ['scenes', newScene.project_id] })
      useSceneStore.getState().addScene(newScene)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      api.scenes.update(id, data),
    onSuccess: async (updatedScene, variables) => {
      // Wait for refetch to complete to ensure UI updates
      await queryClient.refetchQueries({ queryKey: ['scenes', updatedScene.project_id] })
      queryClient.invalidateQueries({ queryKey: ['scene', variables.id] })
      useSceneStore.getState().updateScene(variables.id, updatedScene)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.scenes.delete(id),
    onSuccess: async (_, id) => {
      const scene = useSceneStore.getState().getScene(id)
      // Always refetch queries for this project to ensure UI updates with fresh data
      const targetProjectId = projectId || scene?.project_id
      if (targetProjectId) {
        // Wait for refetch to complete
        await queryClient.refetchQueries({ queryKey: ['scenes', targetProjectId] })
      }
      // Remove from store if present
      useSceneStore.getState().deleteScene(id)
    },
    onError: (error: any) => {
      console.error('Delete scene failed:', error)
    },
  })

  const renderMutation = useMutation({
    mutationFn: ({ sceneId, projectId }: { sceneId: string; projectId: string }) =>
      api.scenes.render(sceneId, projectId),
    onSuccess: (result, variables) => {
      console.log('Render started successfully:', result)
      queryClient.invalidateQueries({ queryKey: ['scenes', variables.projectId] })
      queryClient.invalidateQueries({ queryKey: ['render', result.task_id] })
      useSceneStore.getState().updateScene(variables.sceneId, { status: 'rendering' })
    },
    onError: (error: any) => {
      console.error('Render failed:', error)
      alert(`Failed to start render: ${error.message || 'Unknown error'}\n\nCheck the Logs page for details.`)
    },
  })

  // Always use query.data if available, fallback to filtered store scenes only if query hasn't loaded yet
  const displayScenes = query.data ?? (query.isLoading ? [] : scenes.filter((s) => s.project_id === projectId || !projectId))

  return {
    scenes: displayScenes,
    isLoading: query.isLoading,
    error: query.error,
    createScene: createMutation.mutate,
    updateScene: updateMutation.mutate,
    deleteScene: deleteMutation.mutateAsync,
    renderScene: renderMutation.mutate,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isRendering: renderMutation.isPending,
  }
}

