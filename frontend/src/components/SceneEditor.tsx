'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, Save } from 'lucide-react'
import { api } from '@/lib/api'
import { useQueryClient } from '@tanstack/react-query'

interface SceneEditorProps {
  scene: any
  projectId: string
  totalDuration?: number
  onSave?: () => void
}

export function SceneEditor({ scene, projectId, totalDuration, onSave }: SceneEditorProps) {
  const queryClient = useQueryClient()
  const [isSaving, setIsSaving] = useState(false)
  const [formData, setFormData] = useState({
    scene_description: scene.scene_description || '',
    duration_sec: scene.duration_sec || 30,
    visual_style: scene.visual_style || '',
    environment: scene.environment || '',
    camera_angle: scene.camera_angle || '',
    prompt: scene.prompt || '',
    character_adaptations: JSON.stringify(scene.character_adaptations || {}, null, 2),
  })

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      // Parse JSON fields
      const updateData: any = { ...formData }
      try {
        updateData.character_adaptations = JSON.parse(formData.character_adaptations)
      } catch {
        updateData.character_adaptations = {}
      }

      // Validate duration if total duration is provided
      if (totalDuration) {
        const allScenes = await api.scenes.list(projectId)
        const currentTotal = allScenes
          .filter((s: any) => s.id !== scene.id)
          .reduce((sum: number, s: any) => sum + (s.duration_sec || 0), 0)
        const newTotal = currentTotal + updateData.duration_sec

        if (newTotal !== totalDuration) {
          const confirm = window.confirm(
            `Scene durations will sum to ${newTotal}s, but total duration is ${totalDuration}s. ` +
            `Continue anyway?`
          )
          if (!confirm) {
            setIsSaving(false)
            return
          }
        }
      }

      await api.scenes.update(scene.id, updateData)
      queryClient.invalidateQueries({ queryKey: ['scenes', projectId] })
      onSave?.()
    } catch (error) {
      console.error('Failed to save scene:', error)
      alert('Failed to save scene. Please check the JSON fields are valid.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Edit Scene {scene.number}</CardTitle>
        <CardDescription>Update scene details and prompt</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <label className="text-sm font-medium mb-2 block">Scene Description</label>
          <Textarea
            value={formData.scene_description}
            onChange={(e) => handleChange('scene_description', e.target.value)}
            placeholder="Brief description of the scene"
            className="min-h-[80px]"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium mb-2 block">
              Duration (seconds)
              {totalDuration && (
                <span className="text-xs text-muted-foreground ml-2">
                  Total: {totalDuration}s
                </span>
              )}
            </label>
            <Input
              type="number"
              value={formData.duration_sec}
              onChange={(e) => handleChange('duration_sec', parseInt(e.target.value) || 0)}
              min={1}
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">Camera Angle</label>
            <Input
              value={formData.camera_angle}
              onChange={(e) => handleChange('camera_angle', e.target.value)}
              placeholder="Medium shot, slightly angled down"
            />
          </div>
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block">Visual Style</label>
          <Textarea
            value={formData.visual_style}
            onChange={(e) => handleChange('visual_style', e.target.value)}
            placeholder="High-quality 3D animation in Pixar's signature style"
            className="min-h-[80px]"
          />
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block">Environment</label>
          <Textarea
            value={formData.environment}
            onChange={(e) => handleChange('environment', e.target.value)}
            placeholder="Garden with young tomato plants, soft morning light"
            className="min-h-[80px]"
          />
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block">Detailed Prompt</label>
          <Textarea
            value={formData.prompt}
            onChange={(e) => handleChange('prompt', e.target.value)}
            placeholder="Detailed prompt for video generation"
            className="min-h-[150px]"
          />
          <p className="text-xs text-muted-foreground mt-1">
            This is the main prompt used for video generation
          </p>
        </div>

        <div>
          <label className="text-sm font-medium mb-2 block">Character Adaptations (JSON object)</label>
          <Textarea
            value={formData.character_adaptations}
            onChange={(e) => handleChange('character_adaptations', e.target.value)}
            className="min-h-[120px] font-mono text-xs"
            placeholder='{"Character Name": {"position": "...", "pose": "..."}}'
          />
          <p className="text-xs text-muted-foreground mt-1">
            Scene-specific character details (JSON format)
          </p>
        </div>

        <div className="flex justify-end">
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Scene
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}



