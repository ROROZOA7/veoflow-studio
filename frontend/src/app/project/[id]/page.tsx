'use client'

import { useParams } from 'next/navigation'
import { useProject } from '@/hooks/useProjects'
import { useScenes } from '@/hooks/useScenes'
import { useProjects } from '@/hooks/useProjects'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Loader2, Plus, Play, Video, Trash2, Settings, Film, FileText, Wand2 } from 'lucide-react'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { RenderSettingsDialog } from '@/components/RenderSettingsDialog'
import { useQueryClient } from '@tanstack/react-query'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { ScriptGenerationForm } from '@/components/ScriptGenerationForm'
import { useScript } from '@/hooks/useScript'

export default function ProjectPage() {
  const params = useParams()
  const projectId = params.id as string
  const { project, isLoading: projectLoading } = useProject(projectId)
  const { scenes, isLoading: scenesLoading, createScene, deleteScene, renderScene } = useScenes(projectId)
  const { updateProject } = useProjects()
  const queryClient = useQueryClient()
  const [showSceneForm, setShowSceneForm] = useState(false)
  const [scenePrompt, setScenePrompt] = useState('')
  const [sceneNumber, setSceneNumber] = useState(1)
  const [showSettingsDialog, setShowSettingsDialog] = useState(false)
  
  const { data: script } = useScript(projectId)
  const [activeTab, setActiveTab] = useState('render') // Default to render tab
  
  // Switch to render tab when script is generated
  useEffect(() => {
    if (script) {
      setActiveTab('render')
    }
  }, [script])

  // Auto-refresh scenes every 3 seconds if there are any scenes with rendering or pending status
  useEffect(() => {
    const hasActiveScenes = scenes.some(s => s.status === 'rendering' || s.status === 'pending')
    if (!hasActiveScenes) return

    const interval = setInterval(() => {
      queryClient.refetchQueries({ queryKey: ['scenes', projectId] })
    }, 3000) // Poll every 3 seconds

    return () => clearInterval(interval)
  }, [scenes, projectId, queryClient])

  // Get render settings with defaults
  const renderSettings = project?.render_settings || {
    aspect_ratio: '16:9' as const,
    videos_per_scene: 2 as const,
    model: 'veo3.1-fast',
  }

  // Calculate next scene number based on existing scenes
  const getNextSceneNumber = () => {
    if (!scenes || scenes.length === 0) return 1
    const maxNumber = Math.max(...scenes.map(s => s.number || 0), 0)
    return maxNumber + 1
  }

  const handleOpenSceneForm = () => {
    const nextNumber = getNextSceneNumber()
    setSceneNumber(nextNumber)
    setShowSceneForm(true)
  }

  // Helper function to trigger status polling
  const startStatusPolling = () => {
    // Trigger immediate refresh - useEffect handles ongoing polling
    queryClient.refetchQueries({ queryKey: ['scenes', projectId] })
  }

  const handleCreateScene = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!scenePrompt.trim()) return

    try {
      // Use mutate with callback since createScene uses mutate, not mutateAsync
      createScene(
        {
          project_id: projectId,
          number: sceneNumber,
          prompt: scenePrompt,
        },
        {
          onSuccess: () => {
            setScenePrompt('')
            setSceneNumber(getNextSceneNumber())
            setShowSceneForm(false)
          },
          onError: (error: any) => {
            console.error('Failed to create scene:', error)
            alert(`Failed to create scene: ${error.message || 'Unknown error'}`)
          },
        }
      )
    } catch (error) {
      console.error('Failed to create scene:', error)
    }
  }

  const handleRender = async (sceneId: string) => {
    try {
      console.log(`Starting render for scene ${sceneId} in project ${projectId}`)
      await renderScene({ sceneId, projectId })
      console.log('Render request sent successfully')
      // Trigger immediate refresh and start polling
      startStatusPolling()
    } catch (error: any) {
      console.error('Failed to start render:', error)
      alert(`Failed to start render: ${error.message || 'Unknown error'}\n\nCheck the Logs page for details.`)
    }
  }

  const handleDeleteScene = async (sceneId: string) => {
    if (!confirm('Are you sure you want to delete this scene? This action cannot be undone.')) {
      return
    }

    try {
      await deleteScene(sceneId)
      console.log(`Scene ${sceneId} deleted successfully`)
    } catch (error: any) {
      console.error('Failed to delete scene:', error)
      alert(`Failed to delete scene: ${error.message || 'Unknown error'}`)
    }
  }

  const handleRenderAll = async () => {
    // Force a fresh refetch of scenes before rendering to ensure we have the latest data
    await queryClient.refetchQueries({ queryKey: ['scenes', projectId] })
    
    // Get fresh scenes data after refetch
    const freshScenes = queryClient.getQueryData(['scenes', projectId]) as any[] || scenes
    
    if (!freshScenes || freshScenes.length === 0) {
      alert('No scenes to render')
      return
    }

    const pendingScenes = freshScenes.filter(s => s.status === 'pending')
    if (pendingScenes.length === 0) {
      alert('No pending scenes to render. All scenes are already rendered, rendering, or failed.')
      return
    }

    if (!confirm(`Render all ${pendingScenes.length} pending scene(s)? This will queue all scenes for rendering.`)) {
      return
    }

    try {
      const { api } = await import('@/lib/api')
      const result = await api.render.renderAll(projectId)
      console.log(`Render all request sent successfully: ${result.scenes_count} scenes queued`)
      alert(`Successfully queued ${result.scenes_count} scene(s) for rendering!`)
      
      // Start polling for status updates
      startStatusPolling()
    } catch (error: any) {
      console.error('Failed to start render all:', error)
      alert(`Failed to start render all: ${error.message || 'Unknown error'}\n\nCheck the Logs page for details.`)
    }
  }

  if (projectLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">Project not found</h2>
          <Link href="/">
            <Button variant="outline">Back to Projects</Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <Link href="/" className="text-sm text-muted-foreground hover:text-foreground mb-4 inline-block">
          ← Back to Projects
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold">{project.name}</h1>
              <span className="text-sm text-muted-foreground font-mono bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                ID: {project.id}
              </span>
            </div>
            {project.description && (
              <p className="text-muted-foreground mt-2">{project.description}</p>
            )}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSettingsDialog(true)}
            className="flex items-center gap-2"
          >
            <Settings className="h-4 w-4" />
            Settings
          </Button>
        </div>
      </div>

      <RenderSettingsDialog
        open={showSettingsDialog}
        onOpenChange={setShowSettingsDialog}
        projectId={projectId}
        currentSettings={renderSettings}
        onSave={() => {
          // Invalidate project query to refresh data
          window.location.reload()
        }}
      />

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="mb-6">
          <TabsTrigger value="generate">
            <Wand2 className="mr-2 h-4 w-4" />
            Generate Script
          </TabsTrigger>
          <TabsTrigger value="render">
            <Film className="mr-2 h-4 w-4" />
            Render Video
          </TabsTrigger>
        </TabsList>

        {/* Generate Script Tab */}
        <TabsContent value="generate" className="space-y-6">
          {script ? (
            <Card>
              <CardHeader>
                <CardTitle>Script Generated</CardTitle>
                <CardDescription>
                  Your script has been generated. You can view and edit it, or proceed to render videos.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <strong>Total Duration:</strong> {script.video_duration}s
                  </div>
                  <div>
                    <strong>Scene Count:</strong> {script.scene_count || 0}
                  </div>
                  <div>
                    <strong>Style:</strong> {script.style}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Link href={`/project/${projectId}/script`}>
                    <Button>
                      <FileText className="mr-2 h-4 w-4" />
                      View & Edit Script
                    </Button>
                  </Link>
                  <Button
                    variant="outline"
                    onClick={() => setActiveTab('render')}
                  >
                    Go to Render Video
                    <Film className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Generate Script from Parameters</CardTitle>
                  <CardDescription>
                    Create a complete video script with characters and scenes from your story idea
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ScriptGenerationForm
                    projectId={projectId}
                    onSuccess={(data) => {
                      // Switch to render tab after successful generation
                      setTimeout(() => {
                        setActiveTab('render')
                        queryClient.invalidateQueries({ queryKey: ['scenes', projectId] })
                        queryClient.invalidateQueries({ queryKey: ['script', projectId] })
                      }, 1000)
                    }}
                  />
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Or Use Advanced Workflow</CardTitle>
                  <CardDescription>
                    Use the multi-step workflow for more control over script generation
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Link href={`/project/${projectId}/script`}>
                    <Button variant="outline" className="w-full">
                      <FileText className="mr-2 h-4 w-4" />
                      Open Script Generation Workflow
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Render Video Tab */}
        <TabsContent value="render" className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-semibold">Scenes</h2>
            <div className="flex gap-2">
              {scenes && scenes.length > 0 && (
                <Button
                  variant="default"
                  onClick={handleRenderAll}
                  disabled={scenes.filter(s => s.status === 'pending').length === 0}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Film className="mr-2 h-4 w-4" />
                  Render All Scenes
                </Button>
              )}
              <Button onClick={handleOpenSceneForm}>
                <Plus className="mr-2 h-4 w-4" />
                Add Scene
              </Button>
            </div>
          </div>

          {showSceneForm && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Create New Scene</CardTitle>
            <CardDescription>Add a scene with a prompt for video generation</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateScene} className="space-y-4">
              <div>
                <label className="text-sm font-medium">Scene Number</label>
                <Input
                  type="number"
                  value={sceneNumber}
                  onChange={(e) => {
                    const value = parseInt(e.target.value)
                    setSceneNumber(isNaN(value) ? 1 : Math.max(1, value))
                  }}
                  className="mt-1"
                  min={1}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Scene number is auto-incremented, but you can change it
                </p>
              </div>
              <div>
                <label className="text-sm font-medium">Scene Prompt</label>
                <Textarea
                  value={scenePrompt}
                  onChange={(e) => setScenePrompt(e.target.value)}
                  placeholder="A person walking through a beautiful city at sunset, cinematic wide shot, golden hour lighting"
                  className="mt-1 min-h-[100px]"
                  required
                />
              </div>
              <div className="flex gap-2">
                <Button type="submit">Create Scene</Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowSceneForm(false)
                    setScenePrompt('')
                    setSceneNumber(getNextSceneNumber())
                  }}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

          {scenesLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      ) : scenes.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Video className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No scenes yet</h3>
            <p className="text-muted-foreground mb-4">
              Create your first scene to start generating videos
            </p>
            <Button onClick={handleOpenSceneForm}>
              <Plus className="mr-2 h-4 w-4" />
              Add Scene
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {scenes.map((scene) => (
            <Card key={scene.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      Scene {scene.number}
                    </CardTitle>
                    <CardDescription className="mt-2">{scene.prompt}</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleRender(scene.id)}
                      disabled={scene.status === 'rendering' || scene.status === 'completed'}
                    >
                      <Play className="mr-2 h-4 w-4" />
                      {scene.status === 'rendering' ? 'Rendering...' : 'Render'}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDeleteScene(scene.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">Status:</span>
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        scene.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : scene.status === 'rendering'
                          ? 'bg-blue-100 text-blue-800'
                          : scene.status === 'failed'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {scene.status}
                    </span>
                  </div>
                  {scene.video_path && (
                    <div className="flex items-center gap-2">
                      <Video className="h-4 w-4" />
                      <span className="text-muted-foreground">Video ready</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
        </TabsContent>
      </Tabs>
    </div>
  )
}

