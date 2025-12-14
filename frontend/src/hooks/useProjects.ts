import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useProjectStore } from '@/store/projectStore'

export function useProjects() {
  const { projects, setProjects } = useProjectStore()
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const data = await api.projects.list()
      setProjects(data)
      return data
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      api.projects.create(data),
    onSuccess: (newProject) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      useProjectStore.getState().addProject(newProject)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      api.projects.update(id, data),
    onSuccess: (updatedProject, variables) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['project', variables.id] })
      useProjectStore.getState().updateProject(variables.id, updatedProject)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.projects.delete(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      useProjectStore.getState().deleteProject(id)
    },
  })

  const generateScriptMutation = useMutation({
    mutationFn: ({ id, prompt }: { id: string; prompt: string }) =>
      api.projects.generateScript(id, prompt),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['project', variables.id] })
      queryClient.invalidateQueries({ queryKey: ['scenes', variables.id] })
    },
  })

  return {
    projects: query.data || projects,
    isLoading: query.isLoading,
    error: query.error,
    createProject: createMutation.mutate,
    updateProject: updateMutation.mutate,
    deleteProject: deleteMutation.mutate,
    generateScript: generateScriptMutation.mutate,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isGeneratingScript: generateScriptMutation.isPending,
  }
}

export function useProject(id: string | null) {
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: ['project', id],
    queryFn: async () => {
      if (!id) return null
      return await api.projects.get(id)
    },
    enabled: !!id,
  })

  return {
    project: query.data,
    isLoading: query.isLoading,
    error: query.error,
  }
}

