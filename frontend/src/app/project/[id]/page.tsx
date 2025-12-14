'use client'

import { useParams } from 'next/navigation'
import { useProject } from '@/hooks/useProjects'
import { useScenes } from '@/hooks/useScenes'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Loader2, Plus, Play, Video, Trash2 } from 'lucide-react'
import { useState } from 'react'
import Link from 'next/link'

export default function ProjectPage() {
  const params = useParams()
  const projectId = params.id as string
  const { project, isLoading: projectLoading } = useProject(projectId)
  const { scenes, isLoading: scenesLoading, createScene, deleteScene, renderScene } = useScenes(projectId)
  const [showSceneForm, setShowSceneForm] = useState(false)
  const [scenePrompt, setScenePrompt] = useState('')
  const [sceneNumber, setSceneNumber] = useState(1)

  const handleCreateScene = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!scenePrompt.trim()) return

    try {
      await createScene({
        project_id: projectId,
        number: sceneNumber,
        prompt: scenePrompt,
      })
      setScenePrompt('')
      setSceneNumber(scenes.length + 1)
      setShowSceneForm(false)
    } catch (error) {
      console.error('Failed to create scene:', error)
    }
  }

  const handleRender = async (sceneId: string) => {
    try {
      console.log(`Starting render for scene ${sceneId} in project ${projectId}`)
      await renderScene({ sceneId, projectId })
      console.log('Render request sent successfully')
    } catch (error: any) {
      console.error('Failed to start render:', error)
      alert(`Failed to start render: ${error.message || 'Unknown error'}\n\nCheck the Logs page for details.`)
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
        <h1 className="text-3xl font-bold">{project.name}</h1>
        {project.description && (
          <p className="text-muted-foreground mt-2">{project.description}</p>
        )}
      </div>

      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Scenes</h2>
        <Button onClick={() => setShowSceneForm(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Scene
        </Button>
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
                  onChange={(e) => setSceneNumber(parseInt(e.target.value) || 1)}
                  className="mt-1"
                  min={1}
                />
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
            <Button onClick={() => setShowSceneForm(true)}>
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
                      onClick={() => deleteScene(scene.id)}
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
    </div>
  )
}

