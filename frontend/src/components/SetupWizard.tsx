'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { ProfileManager } from '@/components/ProfileManager'
import { GuidedLoginDialog } from '@/components/GuidedLoginDialog'
import { CheckCircle2, XCircle, AlertCircle, Loader2, ExternalLink } from 'lucide-react'

interface SetupStatus {
  chrome_profile_exists: boolean
  chrome_profile_path: string
  is_logged_in: boolean | null
  login_test_error: string | null
  needs_setup: boolean
}

export function SetupWizard() {
  const [status, setStatus] = useState<SetupStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [testing, setTesting] = useState(false)
  const [openingBrowser, setOpeningBrowser] = useState(false)
  const [showGuidedLogin, setShowGuidedLogin] = useState(false)
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null)
  const [selectedProfileName, setSelectedProfileName] = useState<string>('')

  const loadStatus = async () => {
    try {
      setLoading(true)
      const data = await api.setup.getStatus()
      setStatus(data)
    } catch (error) {
      console.error('Failed to load setup status:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStatus()
  }, [])

  const handleTestConnection = async () => {
    try {
      setTesting(true)
      const result = await api.setup.testConnection()
      
      if (result.success) {
        // Reload status after test
        await loadStatus()
        alert(result.message)
      } else {
        alert(`Connection test failed: ${result.message}`)
      }
    } catch (error: any) {
      alert(`Error: ${error.message}`)
    } finally {
      setTesting(false)
    }
  }

  const handleOpenBrowser = async () => {
    try {
      setOpeningBrowser(true)
      const result = await api.setup.openBrowser()
      alert(result.message)
      // Reload status after opening browser
      setTimeout(() => loadStatus(), 2000)
    } catch (error: any) {
      alert(`Error: ${error.message}`)
    } finally {
      setOpeningBrowser(false)
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">Checking setup status...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!status) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-red-500">
            <XCircle className="h-6 w-6 mx-auto mb-2" />
            <p>Failed to load setup status</p>
            <Button onClick={loadStatus} className="mt-4">
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  const isFullySetup = status.chrome_profile_exists && status.is_logged_in === true

  const handleOpenGuidedLogin = async (profileId: string, profileName: string) => {
    setSelectedProfileId(profileId)
    setSelectedProfileName(profileName)
    setShowGuidedLogin(true)
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Google Flow Setup</CardTitle>
          <CardDescription>
            Configure your browser profile and log in to Google Flow for video generation
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
        {/* Status Overview */}
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-lg border">
            <div className="flex items-center gap-2">
              {status.chrome_profile_exists ? (
                <CheckCircle2 className="h-5 w-5 text-green-500" />
              ) : (
                <XCircle className="h-5 w-5 text-red-500" />
              )}
              <span className="font-medium">Chrome Profile</span>
            </div>
            <span className="text-sm text-muted-foreground">
              {status.chrome_profile_exists ? 'Configured' : 'Not Found'}
            </span>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg border">
            <div className="flex items-center gap-2">
              {status.is_logged_in === true ? (
                <CheckCircle2 className="h-5 w-5 text-green-500" />
              ) : status.is_logged_in === false ? (
                <XCircle className="h-5 w-5 text-red-500" />
              ) : (
                <AlertCircle className="h-5 w-5 text-yellow-500" />
              )}
              <span className="font-medium">Google Flow Login</span>
            </div>
            <span className="text-sm text-muted-foreground">
              {status.is_logged_in === true
                ? 'Logged In'
                : status.is_logged_in === false
                ? 'Not Logged In'
                : 'Unknown'}
            </span>
          </div>
        </div>

        {/* Setup Complete */}
        {isFullySetup && (
          <div className="p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
            <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
              <CheckCircle2 className="h-5 w-5" />
              <span className="font-medium">Setup Complete!</span>
            </div>
            <p className="text-sm text-green-600 dark:text-green-500 mt-1">
              Your browser is configured and you're logged in to Google Flow. You can start generating videos!
            </p>
          </div>
        )}

        {/* Setup Needed */}
        {status.needs_setup && (
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800">
              <div className="flex items-center gap-2 text-yellow-700 dark:text-yellow-400 mb-2">
                <AlertCircle className="h-5 w-5" />
                <span className="font-medium">Setup Required</span>
              </div>
              <p className="text-sm text-yellow-600 dark:text-yellow-500">
                {!status.chrome_profile_exists
                  ? 'Chrome profile not found. You need to set up your browser profile first.'
                  : 'You need to log in to Google Flow to generate videos.'}
              </p>
            </div>

            {/* Setup Steps */}
            <div className="space-y-3">
              <h4 className="font-medium text-sm">Setup Steps:</h4>
              
              {!status.chrome_profile_exists && (
                <div className="pl-4 border-l-2 border-muted">
                  <p className="text-sm mb-2">
                    <strong>Step 1:</strong> Set up Chrome profile
                  </p>
                  <p className="text-xs text-muted-foreground mb-2">
                    Run the setup script in the backend directory:
                  </p>
                  <code className="block text-xs bg-muted p-2 rounded mb-2">
                    cd backend && ./setup_chrome_profile.sh
                  </code>
                  <p className="text-xs text-muted-foreground">
                    Or manually copy your Chrome profile to: <code className="text-xs">{status.chrome_profile_path}</code>
                  </p>
                </div>
              )}

              {status.chrome_profile_exists && status.is_logged_in !== true && (
                <div className="pl-4 border-l-2 border-muted">
                  <p className="text-sm mb-2">
                    <strong>Step {!status.chrome_profile_exists ? '2' : '1'}:</strong> Log in to Google Flow
                  </p>
                  <p className="text-xs text-muted-foreground mb-3">
                    Open a browser window and log in to Google Flow. Your session will be saved automatically.
                  </p>
                  <Button
                    onClick={handleOpenBrowser}
                    disabled={openingBrowser}
                    className="w-full"
                  >
                    {openingBrowser ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Opening Browser...
                      </>
                    ) : (
                      <>
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Open Browser for Login
                      </>
                    )}
                  </Button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-4 border-t">
          <Button
            onClick={handleTestConnection}
            disabled={testing || openingBrowser}
            variant="outline"
            className="flex-1"
          >
            {testing ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              'Test Connection'
            )}
          </Button>
          <Button
            onClick={loadStatus}
            variant="outline"
            disabled={testing || openingBrowser}
          >
            Refresh Status
          </Button>
        </div>

        {/* Error Display */}
        {status.login_test_error && (
          <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
            <p className="text-sm text-red-700 dark:text-red-400">
              <strong>Error:</strong> {status.login_test_error}
            </p>
          </div>
        )}

        {/* Profile Info */}
        {status.chrome_profile_exists && (
          <div className="pt-4 border-t">
            <p className="text-xs text-muted-foreground">
              <strong>Profile Path:</strong> {status.chrome_profile_path}
            </p>
          </div>
        )}
        </CardContent>
      </Card>

      {/* Profile Manager */}
      <ProfileManager onOpenGuidedLogin={handleOpenGuidedLogin} />

      {/* Guided Login Dialog */}
      {showGuidedLogin && selectedProfileId && (
        <GuidedLoginDialog
          profileId={selectedProfileId}
          profileName={selectedProfileName}
          onClose={() => {
            setShowGuidedLogin(false)
            setSelectedProfileId(null)
            setSelectedProfileName('')
          }}
          onSuccess={() => {
            loadStatus()
          }}
        />
      )}
    </div>
  )
}

