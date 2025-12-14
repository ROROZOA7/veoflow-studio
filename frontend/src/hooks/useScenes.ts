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
    onSuccess: (newScene) => {
      queryClient.invalidateQueries({ queryKey: ['scenes', newScene.project_id] })
      useSceneStore.getState().addScene(newScene)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      api.scenes.update(id, data),
    onSuccess: (updatedScene, variables) => {
      queryClient.invalidateQueries({ queryKey: ['scenes', updatedScene.project_id] })
      queryClient.invalidateQueries({ queryKey: ['scene', variables.id] })
      useSceneStore.getState().updateScene(variables.id, updatedScene)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.scenes.delete(id),
    onSuccess: (_, id) => {
      const scene = useSceneStore.getState().getScene(id)
      if (scene) {
        queryClient.invalidateQueries({ queryKey: ['scenes', scene.project_id] })
        useSceneStore.getState().deleteScene(id)
      }
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

  return {
    scenes: query.data || scenes.filter((s) => s.project_id === projectId || !projectId),
    isLoading: query.isLoading,
    error: query.error,
    createScene: createMutation.mutate,
    updateScene: updateMutation.mutate,
    deleteScene: deleteMutation.mutate,
    renderScene: renderMutation.mutate,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isRendering: renderMutation.isPending,
  }
}

