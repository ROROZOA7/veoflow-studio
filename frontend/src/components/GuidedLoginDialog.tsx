'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { CheckCircle2, XCircle, Loader2, ExternalLink, Mail, Video, AlertCircle } from 'lucide-react'

interface GuidedLoginDialogProps {
  profileId: string
  profileName: string
  onClose: () => void
  onSuccess: () => void
}

export function GuidedLoginDialog({ profileId, profileName, onClose, onSuccess }: GuidedLoginDialogProps) {
  const [activeTab, setActiveTab] = useState<'gmail' | 'flow'>('gmail')
  const [gmailOpened, setGmailOpened] = useState(false)
  const [flowOpened, setFlowOpened] = useState(false)
  const [openingGmail, setOpeningGmail] = useState(false)
  const [openingFlow, setOpeningFlow] = useState(false)
  const [checkingStatus, setCheckingStatus] = useState(false)
  const [loginStatus, setLoginStatus] = useState<{
    gmail_logged_in: boolean
    flow_logged_in: boolean
    both_logged_in: boolean
  } | null>(null)
  const [confirming, setConfirming] = useState(false)

  const checkLoginStatus = async () => {
    try {
      setCheckingStatus(true)
      const response = await api.setup.getLoginStatus(profileId)
      setLoginStatus(response)
    } catch (error) {
      console.error('Failed to check login status:', error)
    } finally {
      setCheckingStatus(false)
    }
  }

  // Removed auto-polling - user will manually check status when ready
  // This prevents any interference with manual login process

  const handleOpenGmail = async () => {
    try {
      setOpeningGmail(true)
      await api.setup.openGmail(profileId)
      setGmailOpened(true)
    } catch (error: any) {
      alert(`Failed to open Gmail: ${error.message}`)
    } finally {
      setOpeningGmail(false)
    }
  }

  const handleOpenFlow = async () => {
    try {
      setOpeningFlow(true)
      await api.setup.openFlow(profileId)
      setFlowOpened(true)
    } catch (error: any) {
      alert(`Failed to open Flow: ${error.message}`)
    } finally {
      setOpeningFlow(false)
    }
  }

  const handleConfirmLogin = async () => {
    try {
      setConfirming(true)
      const response = await api.setup.confirmLogin(profileId)
      
      if (response.success) {
        alert(`Success! ${response.message}\nCookies saved: ${response.cookies_count}`)
        onSuccess()
        onClose()
      } else {
        alert(`Login not complete: ${response.message}`)
      }
    } catch (error: any) {
      alert(`Failed to confirm login: ${error.message}`)
    } finally {
      setConfirming(false)
    }
  }

  const canConfirm = loginStatus?.both_logged_in === true

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <CardTitle>Guided Login for {profileName}</CardTitle>
          <CardDescription>
            Follow these steps to log in to Google Flow. The browser will open automatically.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Tab Navigation */}
          <div className="flex gap-2 border-b">
            <button
              onClick={() => setActiveTab('gmail')}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'gmail'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Mail className="h-4 w-4 inline mr-2" />
              Step 1: Login Gmail
            </button>
            <button
              onClick={() => setActiveTab('flow')}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'flow'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Video className="h-4 w-4 inline mr-2" />
              Step 2: Login Flow
            </button>
          </div>

          {/* Gmail Tab */}
          {activeTab === 'gmail' && (
            <div className="space-y-4">
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <h3 className="font-semibold mb-2">Step 1: Login to Gmail</h3>
                <ol className="list-decimal list-inside space-y-2 text-sm">
                  <li>Click the "Open Gmail" button below</li>
                  <li>A browser tab will open with the Gmail login page</li>
                  <li><strong>Log in to your Google account manually</strong> in that browser tab</li>
                  <li>After logging in, click "Check Login Status" to verify</li>
                  <li><strong>Important:</strong> The browser will not interfere with your login - it's just a normal browser window</li>
                </ol>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Gmail URL:</span>
                  <code className="text-xs bg-muted px-2 py-1 rounded">
                    https://accounts.google.com/signin
                  </code>
                </div>

                <Button
                  onClick={handleOpenGmail}
                  disabled={openingGmail}
                  className="w-full"
                >
                  {openingGmail ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Opening Gmail...
                    </>
                  ) : (
                    <>
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Open Gmail
                    </>
                  )}
                </Button>

                {gmailOpened && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 p-3 rounded-lg bg-muted">
                      {loginStatus?.gmail_logged_in ? (
                        <>
                          <CheckCircle2 className="h-5 w-5 text-green-500" />
                          <span className="text-sm text-green-700 dark:text-green-400">
                            Gmail login detected
                          </span>
                        </>
                      ) : (
                        <>
                          <AlertCircle className="h-5 w-5 text-yellow-500" />
                          <span className="text-sm text-muted-foreground">
                            Please log in to Gmail in the browser window
                          </span>
                        </>
                      )}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={checkLoginStatus}
                      disabled={checkingStatus}
                      className="w-full"
                    >
                      {checkingStatus ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Checking...
                        </>
                      ) : (
                        'Check Login Status'
                      )}
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Flow Tab */}
          {activeTab === 'flow' && (
            <div className="space-y-4">
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <h3 className="font-semibold mb-2">Step 2: Login to Google Flow</h3>
                <ol className="list-decimal list-inside space-y-2 text-sm">
                  <li>Make sure you've completed Step 1 (Gmail login)</li>
                  <li>Click the "Open Flow" button below</li>
                  <li>A browser tab will open with the Google Flow page</li>
                  <li><strong>Log in to Google Flow manually</strong> if prompted</li>
                  <li>After logging in, click "Check Login Status" to verify</li>
                  <li><strong>Important:</strong> The browser will not interfere with your login - it's just a normal browser window</li>
                </ol>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">Flow URL:</span>
                  <code className="text-xs bg-muted px-2 py-1 rounded">
                    https://labs.google/fx/tools/flow/
                  </code>
                </div>

                <Button
                  onClick={handleOpenFlow}
                  disabled={openingFlow || !gmailOpened}
                  className="w-full"
                >
                  {openingFlow ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Opening Flow...
                    </>
                  ) : (
                    <>
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Open Flow
                    </>
                  )}
                </Button>

                {!gmailOpened && (
                  <p className="text-xs text-muted-foreground">
                    Please complete Step 1 (Gmail login) first
                  </p>
                )}

                {flowOpened && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 p-3 rounded-lg bg-muted">
                      {loginStatus?.flow_logged_in ? (
                        <>
                          <CheckCircle2 className="h-5 w-5 text-green-500" />
                          <span className="text-sm text-green-700 dark:text-green-400">
                            Flow login detected
                          </span>
                        </>
                      ) : (
                        <>
                          <AlertCircle className="h-5 w-5 text-yellow-500" />
                          <span className="text-sm text-muted-foreground">
                            Please log in to Flow in the browser window
                          </span>
                        </>
                      )}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={checkLoginStatus}
                      disabled={checkingStatus}
                      className="w-full"
                    >
                      {checkingStatus ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Checking...
                        </>
                      ) : (
                        'Check Login Status'
                      )}
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Status Summary */}
          {loginStatus && (
            <div className="p-4 rounded-lg border">
              <h4 className="font-medium mb-2">Login Status</h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Gmail:</span>
                  {loginStatus.gmail_logged_in ? (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-500" />
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Flow:</span>
                  {loginStatus.flow_logged_in ? (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-500" />
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 pt-4 border-t">
            <Button
              onClick={handleConfirmLogin}
              disabled={!canConfirm || confirming}
              className="flex-1"
            >
              {confirming ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Confirm Login & Save Cookie
                </>
              )}
            </Button>
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>

          {!canConfirm && loginStatus && (
            <p className="text-xs text-muted-foreground text-center">
              Please complete both login steps before confirming
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

