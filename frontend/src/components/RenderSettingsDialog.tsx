'use client'

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Loader2 } from 'lucide-react'

interface RenderSettings {
  aspect_ratio: '16:9' | '9:16'
  videos_per_scene: 1 | 2 | 3 | 4
  model: string
}

interface RenderSettingsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  projectId: string
  currentSettings: RenderSettings
  onSave: () => void
}

export function RenderSettingsDialog({
  open,
  onOpenChange,
  projectId,
  currentSettings,
  onSave,
}: RenderSettingsDialogProps) {
  const [settings, setSettings] = useState<RenderSettings>(currentSettings)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    setSettings(currentSettings)
  }, [currentSettings, open])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/projects/${projectId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          render_settings: {
            aspect_ratio: settings.aspect_ratio,
            videos_per_scene: settings.videos_per_scene,
            model: settings.model,
          },
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to save settings')
      }

      onSave()
      onOpenChange(false)
    } catch (error) {
      console.error('Failed to save render settings:', error)
      alert('Failed to save settings. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  const calculateCredits = () => {
    // Calculate credits based on settings (example calculation)
    // This is a placeholder - adjust based on actual credit calculation logic
    const baseCredits = 5
    const videoMultiplier = settings.videos_per_scene
    return baseCredits * videoMultiplier
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Render Settings</DialogTitle>
          <DialogDescription>
            Configure render settings for this project. Changes will apply to all future scene renders.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Aspect Ratio */}
          <div>
            <label className="text-sm font-medium mb-2 block">
              Tỷ lệ khung hình (Aspect Ratio)
            </label>
            <Select
              value={settings.aspect_ratio}
              onValueChange={(value) =>
                setSettings({ ...settings, aspect_ratio: value as '16:9' | '9:16' })
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="16:9">Khổ ngang (16:9)</SelectItem>
                <SelectItem value="9:16">Khổ dọc (9:16)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Videos Per Scene */}
          <div>
            <label className="text-sm font-medium mb-2 block">
              Câu trả lời đầu ra cho mỗi câu (Output answers per query)
            </label>
            <Select
              value={settings.videos_per_scene.toString()}
              onValueChange={(value) =>
                setSettings({ ...settings, videos_per_scene: parseInt(value) as 1 | 2 | 3 | 4 })
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1</SelectItem>
                <SelectItem value="2">2</SelectItem>
                <SelectItem value="3">3</SelectItem>
                <SelectItem value="4">4</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Model */}
          <div>
            <label className="text-sm font-medium mb-2 block">
              Mô hình (Model)
            </label>
            <Select
              value={settings.model}
              onValueChange={(value) => setSettings({ ...settings, model: value })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="veo3.1-fast">Veo 3.1 - Fast</SelectItem>
                <SelectItem value="veo3.1-standard">Veo 3.1 - Standard</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Credit Information */}
          <div className="rounded-md bg-gray-50 dark:bg-gray-900 p-3 text-sm text-gray-700 dark:text-gray-300">
            Dựa trên chế độ cài đặt hiện tại, bạn cần dùng {calculateCredits()} tín dụng cho mỗi lần tạo.
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isSaving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Settings'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

