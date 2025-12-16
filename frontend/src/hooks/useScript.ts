import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useScript(projectId: string) {
  return useQuery({
    queryKey: ['script', projectId],
    queryFn: () => api.scripts.get(projectId),
    enabled: !!projectId,
  })
}

export function useGenerateScript() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ projectId, data }: {
      projectId: string
      data: {
        main_content: string
        video_duration: number
        style: string
        target_audience: string
        aspect_ratio: string
        language?: string
        voice_style?: string
        music_style?: string
        color_palette?: string
        transition_style?: string
      }
    }) => api.projects.generateScriptFromParameters(projectId, data),
    onSuccess: (data, variables) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['script', variables.projectId] })
      queryClient.invalidateQueries({ queryKey: ['scenes', variables.projectId] })
      queryClient.invalidateQueries({ queryKey: ['characters', variables.projectId] })
      queryClient.invalidateQueries({ queryKey: ['project', variables.projectId] })
    },
  })
}

export function useUpdateScript() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ projectId, data }: {
      projectId: string
      data: {
        main_content?: string
        full_script?: string
        story_structure?: any
      }
    }) => api.scripts.update(projectId, data),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['script', variables.projectId] })
    },
  })
}



