'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2, Save } from 'lucide-react'
import { api } from '@/lib/api'
import { useQueryClient } from '@tanstack/react-query'

interface CharacterEditorProps {
  character: any
  projectId: string
  onSave?: () => void
}

export function CharacterEditor({ character, projectId, onSave }: CharacterEditorProps) {
  const queryClient = useQueryClient()
  const [isSaving, setIsSaving] = useState(false)
  const [formData, setFormData] = useState({
    name: character.name || '',
    gender: character.gender || '',
    age: character.age || null,
    age_description: character.age_description || '',
    species: character.species || '',
    voice_personality: character.voice_personality || '',
    body_build: character.body_build || '',
    face_shape: character.face_shape || '',
    hair: character.hair || '',
    skin_or_fur_color: character.skin_or_fur_color || '',
    signature_feature: character.signature_feature || '',
    outfit_top: character.outfit_top || '',
    outfit_bottom: character.outfit_bottom || '',
    helmet_or_hat: character.helmet_or_hat || '',
    shoes_or_footwear: character.shoes_or_footwear || '',
    props: JSON.stringify(character.props || [], null, 2),
    body_metrics: JSON.stringify(character.body_metrics || {}, null, 2),
    position: character.position || '',
    orientation: character.orientation || '',
    pose: character.pose || '',
    foot_placement: character.foot_placement || '',
    hand_detail: character.hand_detail || '',
    expression: character.expression || '',
    action_flow: JSON.stringify(character.action_flow || {}, null, 2),
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
        updateData.props = JSON.parse(formData.props)
      } catch {
        updateData.props = []
      }
      try {
        updateData.body_metrics = JSON.parse(formData.body_metrics)
      } catch {
        updateData.body_metrics = {}
      }
      try {
        updateData.action_flow = JSON.parse(formData.action_flow)
      } catch {
        updateData.action_flow = {}
      }

      await api.characters.update(character.id, updateData)
      queryClient.invalidateQueries({ queryKey: ['characters', projectId] })
      onSave?.()
    } catch (error) {
      console.error('Failed to save character:', error)
      alert('Failed to save character. Please check the JSON fields are valid.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Edit Character: {character.name}</CardTitle>
        <CardDescription>Update character DNA details</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Basic Info */}
        <div className="space-y-4">
          <h3 className="font-semibold">Basic Information</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Name</label>
              <Input
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Gender</label>
              <Select value={formData.gender} onValueChange={(v) => handleChange('gender', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="male">Male</SelectItem>
                  <SelectItem value="female">Female</SelectItem>
                  <SelectItem value="non-binary">Non-binary</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Age Description</label>
              <Input
                value={formData.age_description}
                onChange={(e) => handleChange('age_description', e.target.value)}
                placeholder="Mature, Young, etc."
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Species</label>
              <Input
                value={formData.species}
                onChange={(e) => handleChange('species', e.target.value)}
                placeholder="Rabbit - White Rabbit"
              />
            </div>
          </div>
        </div>

        {/* Appearance */}
        <div className="space-y-4">
          <h3 className="font-semibold">Appearance</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Body Build</label>
              <Input
                value={formData.body_build}
                onChange={(e) => handleChange('body_build', e.target.value)}
                placeholder="Chubby, soft"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Face Shape</label>
              <Input
                value={formData.face_shape}
                onChange={(e) => handleChange('face_shape', e.target.value)}
                placeholder="Round"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Hair</label>
              <Input
                value={formData.hair}
                onChange={(e) => handleChange('hair', e.target.value)}
                placeholder="White fur"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Skin/Fur Color</label>
              <Input
                value={formData.skin_or_fur_color}
                onChange={(e) => handleChange('skin_or_fur_color', e.target.value)}
                placeholder="Soft white fur"
              />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">Signature Feature</label>
            <Textarea
              value={formData.signature_feature}
              onChange={(e) => handleChange('signature_feature', e.target.value)}
              placeholder="Round glasses; gentle, warm smile"
              className="min-h-[80px]"
            />
          </div>
        </div>

        {/* Outfit */}
        <div className="space-y-4">
          <h3 className="font-semibold">Outfit</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Top</label>
              <Input
                value={formData.outfit_top}
                onChange={(e) => handleChange('outfit_top', e.target.value)}
                placeholder="Green gardening apron"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Bottom</label>
              <Input
                value={formData.outfit_bottom}
                onChange={(e) => handleChange('outfit_bottom', e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Hat/Helmet</label>
              <Input
                value={formData.helmet_or_hat}
                onChange={(e) => handleChange('helmet_or_hat', e.target.value)}
                placeholder="Light brown straw hat"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Shoes/Footwear</label>
              <Input
                value={formData.shoes_or_footwear}
                onChange={(e) => handleChange('shoes_or_footwear', e.target.value)}
                placeholder="Furry paws"
              />
            </div>
          </div>
        </div>

        {/* Voice & Personality */}
        <div>
          <label className="text-sm font-medium mb-2 block">Voice Personality</label>
          <Textarea
            value={formData.voice_personality}
            onChange={(e) => handleChange('voice_personality', e.target.value)}
            placeholder="Gentle, clear; gender=Male; locale=vi-VN"
            className="min-h-[80px]"
          />
        </div>

        {/* Props & Metrics (JSON) */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Props (JSON array)</label>
            <Textarea
              value={formData.props}
              onChange={(e) => handleChange('props', e.target.value)}
              className="min-h-[100px] font-mono text-xs"
              placeholder='["Tiny wooden watering can", "woven basket"]'
            />
          </div>
          <div>
            <label className="text-sm font-medium mb-2 block">Body Metrics (JSON object)</label>
            <Textarea
              value={formData.body_metrics}
              onChange={(e) => handleChange('body_metrics', e.target.value)}
              className="min-h-[100px] font-mono text-xs"
              placeholder='{"unit": "cm", "height": 45, "head": 12}'
            />
          </div>
        </div>

        {/* Position & Pose */}
        <div className="space-y-4">
          <h3 className="font-semibold">Position & Pose</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Position</label>
              <Input
                value={formData.position}
                onChange={(e) => handleChange('position', e.target.value)}
                placeholder="kneeling beside young tomato plants"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Orientation</label>
              <Input
                value={formData.orientation}
                onChange={(e) => handleChange('orientation', e.target.value)}
                placeholder="angled down towards plants"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Pose</label>
              <Input
                value={formData.pose}
                onChange={(e) => handleChange('pose', e.target.value)}
                placeholder="kneeling"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Expression</label>
              <Input
                value={formData.expression}
                onChange={(e) => handleChange('expression', e.target.value)}
                placeholder="calm expression"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Foot Placement</label>
              <Input
                value={formData.foot_placement}
                onChange={(e) => handleChange('foot_placement', e.target.value)}
                placeholder="paws tucked under body"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Hand Detail</label>
              <Input
                value={formData.hand_detail}
                onChange={(e) => handleChange('hand_detail', e.target.value)}
                placeholder="right paw gently presses soil"
              />
            </div>
          </div>
        </div>

        {/* Action Flow (JSON) */}
        <div>
          <label className="text-sm font-medium mb-2 block">Action Flow (JSON object)</label>
          <Textarea
            value={formData.action_flow}
            onChange={(e) => handleChange('action_flow', e.target.value)}
            className="min-h-[100px] font-mono text-xs"
            placeholder='{"pre_action": "...", "main_action": "..."}'
          />
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
                Save Character
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}



