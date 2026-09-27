import axios from 'axios'
import type {
  Vegetable,
  PlantingCalendar,
  Conversation,
  Message,
  Member,
  Feedback,
  AISummary,
  Recipe,
  PlantingIntent
} from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

export const vegetableAPI = {
  getAll: (season?: string) =>
    api.get<Vegetable[]>('/vegetables', { params: { season } }),
  getById: (id: number) =>
    api.get<Vegetable>(`/vegetables/${id}`),
  create: (data: Omit<Vegetable, 'id'>) =>
    api.post<Vegetable>('/vegetables', data),
  update: (id: number, data: Vegetable) =>
    api.put<Vegetable>(`/vegetables/${id}`, data),
  delete: (id: number) =>
    api.delete(`/vegetables/${id}`)
}

export const calendarAPI = {
  getAll: (startDate?: string, endDate?: string) =>
    api.get<PlantingCalendar[]>('/calendar', { params: { startDate, endDate } }),
  getByVegetable: (vegetableId: number) =>
    api.get<PlantingCalendar[]>(`/calendar/vegetable/${vegetableId}`),
  create: (data: Omit<PlantingCalendar, 'id'>) =>
    api.post<PlantingCalendar>('/calendar', data),
  toggle: (id: number) =>
    api.patch(`/calendar/${id}/toggle`)
}

export const conversationAPI = {
  getAll: (memberId?: number) =>
    api.get<Conversation[]>('/conversations', { params: { memberId } }),
  getById: (id: number) =>
    api.get<Conversation>(`/conversations/${id}`),
  create: (data: Omit<Conversation, 'id' | 'created_at'>) =>
    api.post<Conversation>('/conversations', data),
  getMessages: (id: number) =>
    api.get<Message[]>(`/conversations/${id}/messages`),
  addMessage: (data: Omit<Message, 'id' | 'timestamp'>) =>
    api.post<Message>('/conversations/messages', data),
  uploadAudio: (id: number, file: File) => {
    const formData = new FormData()
    formData.append('audio_file', file)
    return api.post(`/conversations/${id}/upload-audio`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  getTranscript: (id: number) =>
    api.get(`/conversations/${id}/transcript`),
  addFeedback: (data: Omit<Feedback, 'id' | 'created_at'>) =>
    api.post<Feedback>('/conversations/feedback', data),
  getFeedbacks: (memberId?: number, feedbackType?: string) =>
    api.get<Feedback[]>('/conversations/feedback/list', { params: { memberId, feedbackType } })
}

export const aiAPI = {
  transcribe: (conversationId: number) =>
    api.post(`/ai/transcribe/${conversationId}`),
  getTranscribeStatus: (conversationId: number) =>
    api.get(`/ai/transcribe/${conversationId}/status`),
  extractFeedback: (conversationId: number) =>
    api.post(`/ai/extract-feedback/${conversationId}`),
  generatePlantingIntent: (conversationIds?: number[]) =>
    api.post<PlantingIntent>('/ai/generate-planting-intent', { conversationIds }),
  generateRecipes: (vegetables: string[], count: number = 3) =>
    api.post<{ recipes: Recipe[] }>('/ai/generate-recipes', null, {
      params: { vegetables, count }
    }),
  generateMeetingSummary: (conversationId: number) =>
    api.post(`/ai/meeting-summary/${conversationId}`),
  getSummaries: (summaryType?: string) =>
    api.get<AISummary[]>('/ai/summaries', { params: { summaryType } }),
  getRecipes: () =>
    api.get<Recipe[]>('/ai/recipes')
}

export const emailAPI = {
  send: (toEmails: string[], subject: string, content: string, includeRecipes: boolean = true) =>
    api.post('/email/send', { to_emails: toEmails, subject, content, include_recipes: includeRecipes }),
  sendToAll: (subject: string, content: string, role?: string) =>
    api.post('/email/send-to-all', null, { params: { subject, content, role } }),
  sendPlantingIntent: (summaryId: number) =>
    api.post('/email/send-planting-intent', null, { params: { summary_id: summaryId } }),
  sendMeetingSummary: (summaryId: number) =>
    api.post('/email/send-meeting-summary', null, { params: { summary_id: summaryId } }),
  sendWeeklyUpdate: (weekNumber: number) =>
    api.post('/email/send-weekly-update', null, { params: { week_number: weekNumber } })
}

export const memberAPI = {
  getAll: (role?: string) =>
    api.get<Member[]>('/members', { params: { role } }),
  getById: (id: number) =>
    api.get<Member>(`/members/${id}`),
  create: (data: Omit<Member, 'id' | 'join_date'>) =>
    api.post<Member>('/members', data),
  update: (id: number, data: Omit<Member, 'id' | 'join_date'>) =>
    api.put<Member>(`/members/${id}`, data),
  delete: (id: number) =>
    api.delete(`/members/${id}`)
}

export default api
