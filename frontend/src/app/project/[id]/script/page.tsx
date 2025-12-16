'use client'

import { useParams, useRouter } from 'next/navigation'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ScriptGenerationForm } from '@/components/ScriptGenerationForm'
import { CharacterEditor } from '@/components/CharacterEditor'
import { SceneEditor } from '@/components/SceneEditor'
import { useScript } from '@/hooks/useScript'
import { useScenes } from '@/hooks/useScenes'
import { api } from '@/lib/api'
import { useQuery } from '@tanstack/react-query'
import { Loader2, ArrowLeft, ArrowRight, CheckCircle2, Circle } from 'lucide-react'
import Link from 'next/link'

type Step = 'parameters' | 'script-preview' | 'characters' | 'scenes' | 'review'

export default function ScriptGenerationPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string

  const [currentStep, setCurrentStep] = useState<Step>('parameters')
  const [generationResult, setGenerationResult] = useState<any>(null)

  const { data: script, isLoading: scriptLoading } = useScript(projectId)
  const { scenes, isLoading: scenesLoading } = useScenes(projectId)
  const { data: characters, isLoading: charactersLoading } = useQuery({
    queryKey: ['characters', projectId],
    queryFn: () => api.characters.list(projectId),
    enabled: !!projectId,
  })

  const steps: { id: Step; label: string }[] = [
    { id: 'parameters', label: 'Parameters' },
    { id: 'script-preview', label: 'Script Preview' },
    { id: 'characters', label: 'Characters' },
    { id: 'scenes', label: 'Scenes' },
    { id: 'review', label: 'Review' },
  ]

  const currentStepIndex = steps.findIndex(s => s.id === currentStep)

  const canNavigateToStep = (stepId: Step, index: number) => {
    // Always allow going backwards
    if (index <= currentStepIndex) return true

    // Gate forward navigation based on data availability
    if (stepId === 'script-preview') {
      return !!script
    }
    if (stepId === 'characters') {
      return !!characters && characters.length > 0
    }
    if (stepId === 'scenes') {
      return !!scenes && scenes.length > 0
    }
    if (stepId === 'review') {
      return !!script && !!scenes && scenes.length > 0
    }
    return false
  }

  const handleGenerationSuccess = (data: any) => {
    setGenerationResult(data)
    setCurrentStep('script-preview')
  }

  const handleNext = () => {
    if (currentStepIndex < steps.length - 1) {
      setCurrentStep(steps[currentStepIndex + 1].id)
    }
  }

  const handleBack = () => {
    if (currentStepIndex > 0) {
      setCurrentStep(steps[currentStepIndex - 1].id)
    }
  }

  const handleContinueToRendering = () => {
    router.push(`/project/${projectId}`)
  }

  if (scriptLoading || scenesLoading || charactersLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <Link href={`/project/${projectId}`} className="text-sm text-muted-foreground hover:text-foreground mb-4 inline-block">
          ← Back to Project
        </Link>
        <h1 className="text-3xl font-bold mb-2">Script Generation Workflow</h1>
        <p className="text-muted-foreground">
          Generate a complete video script with characters and scenes
        </p>
      </div>

      {/* Step Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center flex-1">
              <button
                type="button"
                className="flex flex-col items-center flex-1 focus:outline-none"
                onClick={() => {
                  if (canNavigateToStep(step.id, index)) {
                    setCurrentStep(step.id)
                  }
                }}
                disabled={!canNavigateToStep(step.id, index)}
              >
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    index === currentStepIndex
                      ? 'bg-blue-600 text-white'
                      : index < currentStepIndex
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-200 text-gray-600'
                  } ${
                    canNavigateToStep(step.id, index)
                      ? 'cursor-pointer'
                      : 'cursor-not-allowed opacity-60'
                  }`}
                >
                  {index < currentStepIndex ? (
                    <CheckCircle2 className="h-6 w-6" />
                  ) : (
                    <span>{index + 1}</span>
                  )}
                </div>
                <span className="text-xs mt-2 text-center">{step.label}</span>
              </button>
              {index < steps.length - 1 && (
                <div
                  className={`h-1 flex-1 mx-2 ${
                    index < currentStepIndex ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="mb-6">
        {currentStep === 'parameters' && (
          <ScriptGenerationForm
            projectId={projectId}
            onSuccess={handleGenerationSuccess}
          />
        )}

        {currentStep === 'script-preview' && script && (
          <Card>
            <CardHeader>
              <CardTitle>Script Preview</CardTitle>
              <CardDescription>Review the generated script</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Story Structure</h3>
                {script.story_structure && (
                  <div className="space-y-2 text-sm">
                    <div>
                      <strong>Beginning:</strong> {script.story_structure.beginning || 'N/A'}
                    </div>
                    <div>
                      <strong>Middle:</strong> {script.story_structure.middle || 'N/A'}
                    </div>
                    <div>
                      <strong>End:</strong> {script.story_structure.end || 'N/A'}
                    </div>
                  </div>
                )}
              </div>
              <div>
                <h3 className="font-semibold mb-2">Full Script</h3>
                <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg max-h-96 overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-sm">
                    {script.full_script || 'No script generated yet'}
                  </pre>
                </div>
              </div>
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
            </CardContent>
          </Card>
        )}

        {currentStep === 'characters' && characters && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Characters</CardTitle>
                <CardDescription>
                  Review and edit character designs. Characters will maintain consistency across all scenes.
                </CardDescription>
              </CardHeader>
            </Card>
            {characters.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center text-muted-foreground">
                  No characters generated yet. Generate a script first.
                </CardContent>
              </Card>
            ) : (
              characters.map((character: any) => (
                <CharacterEditor
                  key={character.id}
                  character={character}
                  projectId={projectId}
                  onSave={() => {
                    // Character saved
                  }}
                />
              ))
            )}
          </div>
        )}

        {currentStep === 'scenes' && scenes && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Scenes</CardTitle>
                <CardDescription>
                  Review and edit scene prompts. Ensure durations sum to total video duration.
                </CardDescription>
              </CardHeader>
            </Card>
            {scenes.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center text-muted-foreground">
                  No scenes generated yet. Generate a script first.
                </CardContent>
              </Card>
            ) : (
              scenes.map((scene: any) => (
                <SceneEditor
                  key={scene.id}
                  scene={scene}
                  projectId={projectId}
                  totalDuration={script?.video_duration}
                  onSave={() => {
                    // Scene saved
                  }}
                />
              ))
            )}
          </div>
        )}

        {currentStep === 'review' && (
          <Card>
            <CardHeader>
              <CardTitle>Review & Summary</CardTitle>
              <CardDescription>Review everything before proceeding to rendering</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Script Summary</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <strong>Total Duration:</strong> {script?.video_duration || 0}s
                  </div>
                  <div>
                    <strong>Scene Count:</strong> {scenes?.length || 0}
                  </div>
                  <div>
                    <strong>Character Count:</strong> {characters?.length || 0}
                  </div>
                  <div>
                    <strong>Style:</strong> {script?.style || 'N/A'}
                  </div>
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Scenes</h3>
                <div className="space-y-2">
                  {scenes?.map((scene: any) => (
                    <div key={scene.id} className="text-sm p-2 bg-gray-50 dark:bg-gray-900 rounded">
                      <strong>Scene {scene.number}:</strong> {scene.scene_description || scene.prompt?.substring(0, 100)}
                      {' '}({scene.duration_sec || 0}s)
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Characters</h3>
                <div className="space-y-2">
                  {characters?.map((char: any) => (
                    <div key={char.id} className="text-sm p-2 bg-gray-50 dark:bg-gray-900 rounded">
                      <strong>{char.name}:</strong> {char.species || 'Unknown species'}
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={handleBack}
          disabled={currentStepIndex === 0}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <div className="flex gap-2">
          {currentStep === 'review' ? (
            <Button onClick={handleContinueToRendering}>
              Continue to Rendering
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          ) : (
            <Button
              onClick={handleNext}
              disabled={
                (currentStep === 'parameters' && !generationResult) ||
                (currentStep === 'script-preview' && !script) ||
                (currentStep === 'characters' && (!characters || characters.length === 0)) ||
                (currentStep === 'scenes' && (!scenes || scenes.length === 0))
              }
            >
              Next
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

