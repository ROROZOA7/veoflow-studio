'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Settings as SettingsIcon, Loader2, CheckCircle2 } from 'lucide-react'
import { SetupWizard } from '@/components/SetupWizard'
import { api } from '@/lib/api'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const [openaiKey, setOpenaiKey] = useState('')
  const [anthropicKey, setAnthropicKey] = useState('')
  const [geminiKey, setGeminiKey] = useState('')
  const [provider, setProvider] = useState('openai')
  const [model, setModel] = useState('gpt-4o-mini')
  const [temperature, setTemperature] = useState(0.7)
  const [maxTokens, setMaxTokens] = useState(2000)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success'>('idle')

  const { data: aiConfig, isLoading } = useQuery({
    queryKey: ['aiConfig'],
    queryFn: () => api.aiConfig.get(),
  })

  const updateConfig = useMutation({
    mutationFn: (data: any) => api.aiConfig.update(data),
    onSuccess: () => {
      setSaveStatus('success')
      queryClient.invalidateQueries({ queryKey: ['aiConfig'] })
      setTimeout(() => setSaveStatus('idle'), 2000)
    },
  })

  useEffect(() => {
    if (aiConfig) {
      setProvider(aiConfig.provider)
      setModel(aiConfig.model)
      setTemperature(aiConfig.temperature)
      setMaxTokens(aiConfig.max_tokens)
      // Don't populate keys if they exist (for security)
      if (!aiConfig.has_openai_key) setOpenaiKey('')
      if (!aiConfig.has_anthropic_key) setAnthropicKey('')
      if (!aiConfig.has_gemini_key) setGeminiKey('')
    }
  }, [aiConfig])

  // Update model when provider changes
  useEffect(() => {
    const options = getModelOptions(provider)
    if (options.length > 0 && !options.some(opt => opt.value === model)) {
      setModel(options[0].value)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [provider])

  const handleSave = async () => {
    setSaveStatus('saving')
    try {
      const updateData: any = {
        provider,
        model,
        temperature,
        max_tokens: maxTokens,
      }
      
      // Only include keys if they were changed (not empty)
      if (openaiKey.trim()) updateData.openai_api_key = openaiKey.trim()
      if (anthropicKey.trim()) updateData.anthropic_api_key = anthropicKey.trim()
      if (geminiKey.trim()) updateData.gemini_api_key = geminiKey.trim()
      
      await updateConfig.mutateAsync(updateData)
    } catch (error: any) {
      alert(`Failed to save: ${error.message}`)
      setSaveStatus('idle')
    }
  }

  const getModelOptions = (provider: string) => {
    switch (provider) {
      case 'openai':
        return [
          { value: 'gpt-4o-mini', label: 'GPT 5 Nano (gpt-4o-mini)' },
          { value: 'gpt-4.1-mini', label: 'GPT-4.1 Mini' },
          { value: 'gpt-4.1', label: 'GPT-4.1' },
        ]
      case 'anthropic':
        return [
          { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
          { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet' },
          { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku' },
        ]
      case 'gemini':
        return [
          { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash (Fast, price-performance)' },
          { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash (Previous gen)' },
          { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro (Higher quality)' },
        ]
      default:
        return []
    }
  }
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <SettingsIcon className="h-8 w-8" />
          Settings
        </h1>
        <p className="text-muted-foreground mt-2">
          Configure VeoFlow Studio settings
        </p>
      </div>

      <div className="space-y-6">
        {/* Setup Wizard - Most Important */}
        <SetupWizard />

        <Card>
          <CardHeader>
            <CardTitle>AI Configuration</CardTitle>
            <CardDescription>
              Configure AI provider and API keys for script generation
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      AI Provider <span className="text-red-500">*</span>
                    </label>
                    <Select value={provider} onValueChange={setProvider}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="openai">OpenAI (Default)</SelectItem>
                        <SelectItem value="gemini">Gemini</SelectItem>
                        <SelectItem value="anthropic">Anthropic</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Model <span className="text-red-500">*</span>
                    </label>
                    <Select value={model} onValueChange={setModel}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {getModelOptions(provider).map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Temperature</label>
                    <Input
                      type="number"
                      step="0.1"
                      min="0"
                      max="2"
                      value={temperature}
                      onChange={(e) => setTemperature(parseFloat(e.target.value) || 0.7)}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Controls randomness (0.0-2.0)
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Max Tokens</label>
                    <Input
                      type="number"
                      min="100"
                      max="8000"
                      value={maxTokens}
                      onChange={(e) => setMaxTokens(parseInt(e.target.value) || 2000)}
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Maximum response length
                    </p>
                  </div>
                </div>

                <div className="border-t pt-4 mt-4">
                  <h3 className="text-sm font-semibold mb-4">API Keys</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">
                        OpenAI API Key
                        {aiConfig?.has_openai_key && (
                          <span className="ml-2 text-xs text-green-600">✓ Configured</span>
                        )}
                      </label>
                      <Input
                        type="password"
                        placeholder={aiConfig?.has_openai_key ? "•••••••• (leave blank to keep current)" : "sk-..."}
                        value={openaiKey}
                        onChange={(e) => setOpenaiKey(e.target.value)}
                        className="font-mono text-sm"
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        Required for OpenAI provider
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">
                        Anthropic API Key
                        {aiConfig?.has_anthropic_key && (
                          <span className="ml-2 text-xs text-green-600">✓ Configured</span>
                        )}
                      </label>
                      <Input
                        type="password"
                        placeholder={aiConfig?.has_anthropic_key ? "•••••••• (leave blank to keep current)" : "sk-ant-..."}
                        value={anthropicKey}
                        onChange={(e) => setAnthropicKey(e.target.value)}
                        className="font-mono text-sm"
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        Required for Anthropic provider
                      </p>
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">
                        Gemini API Key
                        {aiConfig?.has_gemini_key && (
                          <span className="ml-2 text-xs text-green-600">✓ Configured</span>
                        )}
                      </label>
                      <Input
                        type="password"
                        placeholder={aiConfig?.has_gemini_key ? "•••••••• (leave blank to keep current)" : "your-gemini-key"}
                        value={geminiKey}
                        onChange={(e) => setGeminiKey(e.target.value)}
                        className="font-mono text-sm"
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        Required for Gemini provider (default)
                      </p>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4 border-t">
                  <div>
                    {saveStatus === 'success' && (
                      <div className="flex items-center gap-2 text-sm text-green-600">
                        <CheckCircle2 className="h-4 w-4" />
                        Configuration saved successfully
                      </div>
                    )}
                  </div>
                  <Button
                    onClick={handleSave}
                    disabled={saveStatus === 'saving'}
                  >
                    {saveStatus === 'saving' ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      'Save Configuration'
                    )}
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Browser Configuration</CardTitle>
            <CardDescription>
              Configure browser automation settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Headless Mode</label>
              <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                <option value="false">Off (Show browser window)</option>
                <option value="true">On (Hide browser window)</option>
              </select>
              <p className="text-xs text-muted-foreground mt-1">
                Set to Off for first-time Google Flow login
              </p>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Chrome Profile Path</label>
              <Input
                defaultValue="./chromedata"
                className="font-mono text-sm"
              />
            </div>
            <Button>Save Browser Settings</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>About</CardTitle>
            <CardDescription>
              VeoFlow Studio information
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Version:</span>
                <span className="font-medium">1.0.0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Backend API:</span>
                <span className="font-medium">http://localhost:8000</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

