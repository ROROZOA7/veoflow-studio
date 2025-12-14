/**
 * API client for VeoFlow Studio backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiError {
  detail: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error: ApiError = await response.json().catch(() => ({
          detail: `HTTP ${response.status}: ${response.statusText}`,
        }));
        throw new Error(error.detail || 'API request failed');
      }

      // Handle empty responses
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return {} as T;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Unknown error occurred');
    }
  }

  // Projects API
  projects = {
    list: () => this.request<any[]>('/api/projects'),
    get: (id: string) => this.request<any>(`/api/projects/${id}`),
    create: (data: any) =>
      this.request<any>('/api/projects', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (id: string, data: any) =>
      this.request<any>(`/api/projects/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      this.request<void>(`/api/projects/${id}`, {
        method: 'DELETE',
      }),
    generateScript: (id: string, prompt: string) =>
      this.request<any>(`/api/projects/${id}/generate-script`, {
        method: 'POST',
        body: JSON.stringify({ prompt }),
      }),
  };

  // Scenes API
  scenes = {
    list: (projectId: string) =>
      this.request<any[]>(`/api/scenes?project_id=${projectId}`),
    get: (id: string) => this.request<any>(`/api/scenes/${id}`),
    create: (data: any) =>
      this.request<any>('/api/scenes', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (id: string, data: any) =>
      this.request<any>(`/api/scenes/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      this.request<void>(`/api/scenes/${id}`, {
        method: 'DELETE',
      }),
    render: (sceneId: string, projectId: string) =>
      this.request<{ task_id: string; status: string }>(
        `/api/render/scenes/${sceneId}/render?project_id=${projectId}`,
        {
          method: 'POST',
        }
      ),
  };

  // Characters API
  characters = {
    list: (projectId: string) =>
      this.request<any[]>(`/api/characters?project_id=${projectId}`),
    get: (id: string) => this.request<any>(`/api/characters/${id}`),
    create: (data: any) =>
      this.request<any>('/api/characters', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (id: string, data: any) =>
      this.request<any>(`/api/characters/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      this.request<void>(`/api/characters/${id}`, {
        method: 'DELETE',
      }),
  };

  // Render API
  render = {
    getTaskStatus: (taskId: string) =>
      this.request<any>(`/api/render/tasks/${taskId}`),
    cancel: (sceneId: string) =>
      this.request<void>(`/api/render/scenes/${sceneId}/cancel`, {
        method: 'POST',
      }),
  };

  // Queue API
  queue = {
    list: () => this.request<any[]>('/api/queue'),
    stats: () => this.request<any>('/api/queue/stats'),
  };

  // Video stitching
  stitch = (projectId: string, options?: { transition?: string; duration?: number }) =>
    this.request<{ video_path: string }>(`/api/projects/${projectId}/stitch`, {
      method: 'POST',
      body: JSON.stringify(options || {}),
    });

  // Setup API
  setup = {
    getStatus: () => this.request<{
      chrome_profile_exists: boolean;
      chrome_profile_path: string;
      is_logged_in: boolean | null;
      login_test_error: string | null;
      needs_setup: boolean;
    }>('/api/setup/status'),
    testConnection: () =>
      this.request<{
        success: boolean;
        message: string;
        is_logged_in: boolean;
        screenshot_path: string | null;
      }>('/api/setup/test-connection', {
        method: 'POST',
      }),
    openBrowser: () =>
      this.request<{
        success: boolean;
        message: string;
      }>('/api/setup/open-browser', {
        method: 'POST',
      }),
    getChromeProfile: () =>
      this.request<{
        chrome_profile_path: string;
        profile_exists: boolean;
        use_existing_profile: boolean;
        existing_profile_path: string;
        file_count: number;
      }>('/api/setup/chrome-profile'),
    // Profile Management
    createProfile: (name: string) =>
      this.request<{
        success: boolean;
        profile: {
          id: string;
          name: string;
          profile_path: string;
          is_active: boolean;
          created_at: string;
          updated_at: string;
          metadata: any;
        };
      }>('/api/setup/profiles', {
        method: 'POST',
        body: JSON.stringify({ name }),
      }),
    listProfiles: () =>
      this.request<{
        success: boolean;
        profiles: Array<{
          id: string;
          name: string;
          profile_path: string;
          is_active: boolean;
          created_at: string;
          updated_at: string;
          metadata: any;
        }>;
      }>('/api/setup/profiles'),
    getProfile: (id: string) =>
      this.request<{
        success: boolean;
        profile: {
          id: string;
          name: string;
          profile_path: string;
          is_active: boolean;
          created_at: string;
          updated_at: string;
          metadata: any;
        };
      }>(`/api/setup/profiles/${id}`),
    deleteProfile: (id: string) =>
      this.request<{
        success: boolean;
        message: string;
      }>(`/api/setup/profiles/${id}`, {
        method: 'DELETE',
      }),
    setActiveProfile: (id: string) =>
      this.request<{
        success: boolean;
        message: string;
      }>(`/api/setup/profiles/${id}/set-active`, {
        method: 'POST',
      }),
    // Guided Login
    openProfile: (id: string) =>
      this.request<{
        success: boolean;
        message: string;
        profile_id: string;
        profile_name: string;
      }>(`/api/setup/profiles/${id}/open`, {
        method: 'POST',
      }),
    openGmail: (id: string) =>
      this.request<{
        success: boolean;
        message: string;
        url: string;
      }>(`/api/setup/profiles/${id}/open-gmail`, {
        method: 'POST',
      }),
    openFlow: (id: string) =>
      this.request<{
        success: boolean;
        message: string;
        url: string;
      }>(`/api/setup/profiles/${id}/open-flow`, {
        method: 'POST',
      }),
    getLoginStatus: (id: string) =>
      this.request<{
        success: boolean;
        gmail_logged_in: boolean;
        flow_logged_in: boolean;
        both_logged_in: boolean;
      }>(`/api/setup/profiles/${id}/login-status`),
    confirmLogin: (id: string) =>
      this.request<{
        success: boolean;
        message: string;
        cookies_count: number;
        login_status: {
          gmail_logged_in: boolean;
          flow_logged_in: boolean;
          both_logged_in: boolean;
        };
      }>(`/api/setup/profiles/${id}/confirm-login`, {
        method: 'POST',
      }),
    closeProfile: (id: string) =>
      this.request<{
        success: boolean;
        message: string;
      }>(`/api/setup/profiles/${id}/close`, {
        method: 'POST',
      }),
  };

  // Logs API
  logs = {
    getLogs: (params?: {
      level?: string;
      logger_name?: string;
      limit?: number;
      since?: string;
    }) => {
      const queryParams = new URLSearchParams()
      if (params?.level) queryParams.append('level', params.level)
      if (params?.logger_name) queryParams.append('logger_name', params.logger_name)
      if (params?.limit) queryParams.append('limit', params.limit.toString())
      if (params?.since) queryParams.append('since', params.since)
      
      const queryString = queryParams.toString()
      return this.request<{
        logs: Array<{
          timestamp: string;
          level: string;
          logger: string;
          message: string;
          extra: any;
        }>;
        total: number;
        has_more: boolean;
      }>(`/api/logs${queryString ? `?${queryString}` : ''}`)
    },
    getRecentLogs: (limit?: number) =>
      this.request<{
        logs: Array<{
          timestamp: string;
          level: string;
          logger: string;
          message: string;
          extra: any;
        }>;
        total: number;
        has_more: boolean;
      }>(`/api/logs/recent${limit ? `?limit=${limit}` : ''}`),
    clearLogs: () =>
      this.request<{ message: string }>('/api/logs', {
        method: 'DELETE',
      }),
  };
}

export const api = new ApiClient();

