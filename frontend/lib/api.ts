import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://86.50.20.163:5000' || 'http://localhost:5000';

// Client-side authenticated fetch utility using axios
export const authenticatedFetch = async (
  url: string,
  options: AxiosRequestConfig = {}
): Promise<AxiosResponse> => {
  try {
    const method = (options.method || 'GET').toUpperCase();
    const { data, ...restOptions } = options;
    
    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...restOptions,
    };

    console.log(`Making ${method} request to:`, url, config);
    
    switch (method) {
      case 'GET':
         console.log("GET data:", data);
        return await authenticatedAxios.get(url, config);
      case 'POST':
        console.log("POST data:", data);
        return await authenticatedAxios.post(url, data, config);
      case 'PUT':
        return await authenticatedAxios.put(url, data, config);
      case 'DELETE':
        return await authenticatedAxios.delete(url, config);
      case 'PATCH':
        return await authenticatedAxios.patch(url, data, config);
      default:
         console.log("Request data:", data);
        return await authenticatedAxios.request({ ...config, method, url, data });
    }
  } catch (error) {
    console.error('Authenticated fetch error:', error);
    throw error;
  }
};

// Axios instance with authentication
export const authenticatedAxios = axios.create({
  baseURL: BASE_URL,
});

// Request interceptor to add auth token
authenticatedAxios.interceptors.request.use(
  async (config) => {
    try {
      const response = await fetch('/auth/access-token');
      if (response.ok) {
        const { token } = await response.json();
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Failed to add auth token:', error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
authenticatedAxios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login on auth failure
      window.location.href = '/auth/login';
    }
    return Promise.reject(error);
  }
);


// Speech API utilities
export const speechApi = {
  // Get all speeches for the authenticated user
  getSpeeches: async (): Promise<any> => {
    const response = await authenticatedFetch('/api/v1/speeches');
    return response.data;
  },

  // Create a new speech
  createSpeech: async (speechData: {
    title: string;
    goal: string;
    audience_description: string;
    key_points?: string;
    self_improvement_goal?: string;
    context: string;
  }): Promise<any> => {
    const response = await authenticatedFetch('/api/v1/speeches', {
      method: 'POST',
      data: speechData,
    });
    return response.data.speech;
  },

  // Get a specific speech
  getSpeech: async (speechId: string): Promise<any> => {
    const response = await authenticatedFetch(`/api/v1/speeches/${speechId}`);
    return response.data.speech;
  },

  // Update a speech
  updateSpeech: async (speechId: string, speechData: {
    title?: string;
    goal?: string;
    audience_description?: string;
    key_points?: string;
    self_improvement_goal?: string;
    context?: string;
  }): Promise<any> => {
    const response = await authenticatedFetch(`/api/v1/speeches/${speechId}`, {
      method: 'PUT',
      data: speechData,
    });
    return response.data;
  },

  // Delete a speech
  deleteSpeech: async (speechId: string): Promise<void> => {
    const response = await authenticatedFetch(`/api/v1/speeches/${speechId}`, {
      method: 'DELETE',
    });
    // No return needed for delete operations
  },
};

// Session API utilities
export const sessionApi = {
  // Get all sessions for a speech
  getSessions: async (speechId: string): Promise<any> => {
    const response = await authenticatedFetch(`/api/v1/speeches/${speechId}/sessions`);
    return response.data;
  },

  // Get a specific session
  getSession: async (sessionId: string): Promise<any> => {
    const response = await authenticatedFetch(`/api/v1/sessions/${sessionId}`);
    return response.data.session;
  },

  // Delete a session
  deleteSession: async (sessionId: string): Promise<void> => {
    const response = await authenticatedFetch(`/api/v1/sessions/${sessionId}`, {
      method: 'DELETE',
    });
    // No return needed for delete operations
  },

  // Analyze speech and create session
  analyzeAndCreateSession: async (speechId: string, file: File, sessionTitle?: string): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('speech_id', speechId);
    if (sessionTitle) {
      formData.append('session_title', sessionTitle);
    }

    const response = await authenticatedAxios.post('/api/v1/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  // Refresh media URL for a session
  refreshMediaUrl: async (sessionId: string): Promise<any> => {
    const response = await authenticatedFetch(`/api/v1/sessions/${sessionId}/refresh-media-url`, {
      method: 'POST',
    });
    return response.data;
  },

  // Fix missing blob name for a session
  fixBlobName: async (sessionId: string): Promise<any> => {
    const response = await authenticatedFetch(`/api/v1/sessions/${sessionId}/fix-blob-name`, {
      method: 'POST',
    });
    return response.data;
  },

  // Get user self-rating for a session
  getSelfRating: async (sessionId: string): Promise<any> => {
    const response = await authenticatedFetch(`/api/v1/sessions/${sessionId}/self-rating`);
    return response.data;
  },

  // Save or update user self-rating for a session
  saveSelfRating: async (sessionId: string, ratingData: any): Promise<any> => {
    const response = await authenticatedFetch(`/api/v1/sessions/${sessionId}/self-rating`, {
      method: 'POST',
      data: ratingData,
    });
    return response.data;
  },

  // Update user self-rating for a session
  updateSelfRating: async (sessionId: string, ratingData: any): Promise<any> => {
    const response = await authenticatedFetch(`/api/v1/sessions/${sessionId}/self-rating`, {
      method: 'PUT',
      data: ratingData,
    });
    return response.data;
  },

  // Delete user self-rating for a session
  deleteSelfRating: async (sessionId: string): Promise<any> => {
    const response = await authenticatedFetch(`/api/v1/sessions/${sessionId}/self-rating`, {
      method: 'DELETE',
    });
    return response.data;
  },
};

export default { speechApi, sessionApi };
