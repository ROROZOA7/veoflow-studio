'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { CheckCircle2, XCircle, Loader2, Plus, Trash2, ExternalLink, User } from 'lucide-react'

interface Profile {
  id: string
  name: string
  profile_path: string
  is_active: boolean
  created_at: string
  updated_at: string
  metadata: any
}

interface ProfileManagerProps {
  onOpenGuidedLogin?: (profileId: string, profileName: string) => void
}

export function ProfileManager({ onOpenGuidedLogin }: ProfileManagerProps = {}) {
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [newProfileName, setNewProfileName] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [openingId, setOpeningId] = useState<string | null>(null)

  const loadProfiles = async () => {
    try {
      setLoading(true)
      const response = await api.setup.listProfiles()
      setProfiles(response.profiles || [])
    } catch (error) {
      console.error('Failed to load profiles:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProfiles()
  }, [])

  const handleCreateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newProfileName.trim()) return

    try {
      setCreating(true)
      await api.setup.createProfile(newProfileName.trim())
      setNewProfileName('')
      setShowCreateForm(false)
      await loadProfiles()
    } catch (error: any) {
      alert(`Failed to create profile: ${error.message}`)
    } finally {
      setCreating(false)
    }
  }

  const handleDeleteProfile = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete profile "${name}"? This cannot be undone.`)) {
      return
    }

    try {
      setDeletingId(id)
      await api.setup.deleteProfile(id)
      await loadProfiles()
    } catch (error: any) {
      alert(`Failed to delete profile: ${error.message}`)
    } finally {
      setDeletingId(null)
    }
  }

  const handleSetActive = async (id: string) => {
    try {
      await api.setup.setActiveProfile(id)
      await loadProfiles()
    } catch (error: any) {
      alert(`Failed to set active profile: ${error.message}`)
    }
  }

  const handleOpenProfile = async (id: string) => {
    try {
      setOpeningId(id)
      await api.setup.openProfile(id)
      
      // If onOpenGuidedLogin callback is provided, open guided login dialog
      if (onOpenGuidedLogin) {
        const profile = profiles.find(p => p.id === id)
        if (profile) {
          onOpenGuidedLogin(id, profile.name)
        }
      }
    } catch (error: any) {
      alert(`Failed to open profile: ${error.message}`)
    } finally {
      setOpeningId(null)
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">Loading profiles...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  const activeProfile = profiles.find(p => p.is_active)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Chrome Profiles</CardTitle>
        <CardDescription>
          Manage Chrome profiles for browser automation. Each profile maintains its own login session.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Create Profile Form */}
        {showCreateForm ? (
          <form onSubmit={handleCreateProfile} className="space-y-3 p-4 border rounded-lg">
            <div>
              <label className="text-sm font-medium mb-2 block">Profile Name</label>
              <Input
                value={newProfileName}
                onChange={(e) => setNewProfileName(e.target.value)}
                placeholder="My Profile"
                required
                autoFocus
              />
            </div>
            <div className="flex gap-2">
              <Button type="submit" disabled={creating} size="sm">
                {creating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4 mr-2" />
                    Create
                  </>
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  setShowCreateForm(false)
                  setNewProfileName('')
                }}
              >
                Cancel
              </Button>
            </div>
          </form>
        ) : (
          <Button onClick={() => setShowCreateForm(true)} className="w-full">
            <Plus className="h-4 w-4 mr-2" />
            Create New Profile
          </Button>
        )}

        {/* Active Profile Indicator */}
        {activeProfile && (
          <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
            <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
              <CheckCircle2 className="h-5 w-5" />
              <span className="font-medium">Active Profile: {activeProfile.name}</span>
            </div>
          </div>
        )}

        {/* Profile List */}
        {profiles.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <User className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No profiles yet. Create your first profile to get started.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {profiles.map((profile) => (
              <div
                key={profile.id}
                className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3 flex-1">
                  {profile.is_active ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : (
                    <div className="h-5 w-5 rounded-full border-2 border-muted-foreground/30" />
                  )}
                  <div className="flex-1">
                    <div className="font-medium flex items-center gap-2">
                      {profile.name}
                      {profile.is_active && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                          Active
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Created {new Date(profile.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {!profile.is_active && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleSetActive(profile.id)}
                    >
                      Set Active
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleOpenProfile(profile.id)}
                    disabled={openingId === profile.id}
                  >
                    {openingId === profile.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <ExternalLink className="h-4 w-4 mr-2" />
                        Open
                      </>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDeleteProfile(profile.id, profile.name)}
                    disabled={deletingId === profile.id || profile.is_active}
                  >
                    {deletingId === profile.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

