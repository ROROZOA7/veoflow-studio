'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Settings as SettingsIcon } from 'lucide-react'
import { SetupWizard } from '@/components/SetupWizard'

export default function SettingsPage() {
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
            <CardTitle>API Configuration</CardTitle>
            <CardDescription>
              Configure API keys for AI services (optional - only for script generation)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">OpenAI API Key</label>
              <Input
                type="password"
                placeholder="sk-..."
                className="font-mono text-sm"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Optional: For GPT-based script generation
              </p>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Anthropic API Key</label>
              <Input
                type="password"
                placeholder="sk-ant-..."
                className="font-mono text-sm"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Optional: For Claude-based script generation
              </p>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Gemini API Key</label>
              <Input
                type="password"
                placeholder="your-gemini-key"
                className="font-mono text-sm"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Optional: For Gemini-based script generation
              </p>
            </div>
            <Button>Save API Keys</Button>
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

