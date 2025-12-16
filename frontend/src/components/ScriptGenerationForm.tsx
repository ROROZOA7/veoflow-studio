'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import { useGenerateScript } from '@/hooks/useScript'

interface ScriptGenerationFormProps {
  projectId: string
  onSuccess?: (data: any) => void
  onError?: (error: Error) => void
}

export function ScriptGenerationForm({ projectId, onSuccess, onError }: ScriptGenerationFormProps) {
  const [mainContent, setMainContent] = useState('')
  const [videoDuration, setVideoDuration] = useState(300)
  const [style, setStyle] = useState('cartoon')
  const [targetAudience, setTargetAudience] = useState('children')
  const [aspectRatio, setAspectRatio] = useState('16:9')
  const [showOptional, setShowOptional] = useState(false)
  const [language, setLanguage] = useState('')
  const [voiceStyle, setVoiceStyle] = useState('')
  const [musicStyle, setMusicStyle] = useState('')
  const [colorPalette, setColorPalette] = useState('')
  const [transitionStyle, setTransitionStyle] = useState('')

  const generateScript = useGenerateScript()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const result = await generateScript.mutateAsync({
        projectId,
        data: {
          main_content: mainContent,
          video_duration: videoDuration,
          style,
          target_audience: targetAudience,
          aspect_ratio: aspectRatio,
          language: language || undefined,
          voice_style: voiceStyle || undefined,
          music_style: musicStyle || undefined,
          color_palette: colorPalette || undefined,
          transition_style: transitionStyle || undefined,
        },
      })
      
      onSuccess?.(result)
    } catch (error) {
      onError?.(error as Error)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generate Script from Parameters</CardTitle>
        <CardDescription>
          Provide the story content and parameters to generate a complete video script
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Required Fields */}
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Main Content/Story <span className="text-red-500">*</span>
              </label>
              <Textarea
                value={mainContent}
                onChange={(e) => setMainContent(e.target.value)}
                placeholder="The story of the tortoise and the hare"
                className="min-h-[120px]"
                required
              />
              <p className="text-xs text-muted-foreground mt-1">
                Describe the main story or concept for your video
              </p>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Video Duration (seconds) <span className="text-red-500">*</span>
              </label>
              <Input
                type="number"
                value={videoDuration}
                onChange={(e) => setVideoDuration(parseInt(e.target.value) || 300)}
                min={30}
                max={3600}
                required
              />
              <p className="text-xs text-muted-foreground mt-1">
                Total video duration in seconds (e.g., 300 for 5 minutes)
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Style <span className="text-red-500">*</span>
                </label>
                <Select value={style} onValueChange={setStyle}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cartoon">Cartoon</SelectItem>
                    <SelectItem value="3D animation">3D Animation</SelectItem>
                    <SelectItem value="realistic">Realistic</SelectItem>
                    <SelectItem value="Pixar style">Pixar Style</SelectItem>
                    <SelectItem value="anime">Anime</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Target Audience <span className="text-red-500">*</span>
                </label>
                <Select value={targetAudience} onValueChange={setTargetAudience}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="children">Children</SelectItem>
                    <SelectItem value="adults">Adults</SelectItem>
                    <SelectItem value="teenagers">Teenagers</SelectItem>
                    <SelectItem value="educational">Educational</SelectItem>
                    <SelectItem value="entertainment">Entertainment</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Aspect Ratio <span className="text-red-500">*</span>
              </label>
              <Select value={aspectRatio} onValueChange={setAspectRatio}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="16:9">16:9 (Widescreen)</SelectItem>
                  <SelectItem value="9:16">9:16 (Vertical)</SelectItem>
                  <SelectItem value="1:1">1:1 (Square)</SelectItem>
                  <SelectItem value="4:3">4:3 (Classic)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Optional Fields */}
          <div>
            <Button
              type="button"
              variant="ghost"
              onClick={() => setShowOptional(!showOptional)}
              className="w-full flex items-center justify-between"
            >
              <span>Optional Parameters</span>
              {showOptional ? <ChevronUp /> : <ChevronDown />}
            </Button>

            {showOptional && (
              <div className="mt-4 space-y-4 p-4 border rounded-lg">
                <div>
                  <label className="text-sm font-medium mb-2 block">Language/Locale</label>
                  <Input
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    placeholder="en-US, vi-VN"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Voice Style</label>
                  <Input
                    value={voiceStyle}
                    onChange={(e) => setVoiceStyle(e.target.value)}
                    placeholder="narrator, character voices"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Music Style</label>
                  <Input
                    value={musicStyle}
                    onChange={(e) => setMusicStyle(e.target.value)}
                    placeholder="upbeat, calm, dramatic"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Color Palette</label>
                  <Input
                    value={colorPalette}
                    onChange={(e) => setColorPalette(e.target.value)}
                    placeholder="bright, muted, pastel"
                  />
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Transition Style</label>
                  <Input
                    value={transitionStyle}
                    onChange={(e) => setTransitionStyle(e.target.value)}
                    placeholder="smooth, cut, fade"
                  />
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <Button
              type="submit"
              disabled={generateScript.isPending || !mainContent.trim()}
              className="flex-1"
            >
              {generateScript.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                'Generate Script'
              )}
            </Button>
          </div>

          {generateScript.isError && (
            <div className="text-sm text-red-600 bg-red-50 p-3 rounded">
              Error: {generateScript.error?.message || 'Failed to generate script'}
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  )
}



