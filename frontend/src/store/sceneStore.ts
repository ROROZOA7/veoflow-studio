import { create } from 'zustand'

interface Scene {
  id: string
  project_id: string
  number: number
  prompt: string
  script?: string
  video_path?: string
  thumbnail_path?: string
  metadata?: any
  status: string
}

interface SceneStore {
  scenes: Scene[]
  setScenes: (scenes: Scene[]) => void
  addScene: (scene: Scene) => void
  updateScene: (id: string, scene: Partial<Scene>) => void
  deleteScene: (id: string) => void
  getScenesByProject: (projectId: string) => Scene[]
  getScene: (id: string) => Scene | undefined
}

export const useSceneStore = create<SceneStore>((set, get) => ({
  scenes: [],
  setScenes: (scenes) => set({ scenes }),
  addScene: (scene) => set((state) => ({ scenes: [...state.scenes, scene] })),
  updateScene: (id, updates) =>
    set((state) => ({
      scenes: state.scenes.map((s) => (s.id === id ? { ...s, ...updates } : s)),
    })),
  deleteScene: (id) =>
    set((state) => ({ scenes: state.scenes.filter((s) => s.id !== id) })),
  getScenesByProject: (projectId) =>
    get().scenes.filter((s) => s.project_id === projectId).sort((a, b) => a.number - b.number),
  getScene: (id) => get().scenes.find((s) => s.id === id),
}))

