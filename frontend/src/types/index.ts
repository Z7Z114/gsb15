export interface Member {
  id: number
  name: string
  email: string
  phone?: string
  role: 'farmer' | 'consumer'
  join_date: string
  is_active: boolean
  preferences?: Record<string, any>
}

export interface Vegetable {
  id: number
  name: string
  english_name?: string
  season: 'spring' | 'summer' | 'autumn' | 'winter'
  planting_start?: string
  planting_end?: string
  harvest_start?: string
  harvest_end?: string
  description?: string
  nutritional_value?: string
  storage_method?: string
  image_url?: string
  is_available: boolean
  share_quota: number
}

export interface PlantingCalendar {
  id: number
  vegetable_id: number
  activity_type: 'planting' | 'watering' | 'fertilizing' | 'harvesting'
  activity_date: string
  description?: string
  completed: boolean
}

export interface Conversation {
  id: number
  member_id: number
  title?: string
  created_at: string
  status: 'active' | 'closed' | 'archived'
}

export interface Message {
  id: number
  conversation_id: number
  sender_role: 'farmer' | 'consumer' | 'system'
  speaker_id?: string
  content: string
  timestamp: string
}

export interface Transcript {
  id: number
  conversation_id: number
  audio_file_path?: string
  raw_transcript?: string
  processed_transcript?: {
    segments: Array<{
      start: number
      end: number
      text: string
      speaker?: string
    }>
    speaker_roles: Record<string, string>
  }
  diarization_result?: {
    speakers: string[]
    segments: Array<{
      start: number
      end: number
      speaker: string
    }>
  }
  created_at: string
}

export interface Feedback {
  id: number
  member_id: number
  conversation_id?: number
  feedback_type: 'taste' | 'delivery' | 'quality' | 'other'
  content: string
  rating?: number
  created_at: string
}

export interface AISummary {
  id: number
  summary_type: 'planting_intent' | 'share_adjustment' | 'meeting_summary'
  content: Record<string, any>
  source_conversation_ids?: number[]
  created_at: string
  version: string
}

export interface Recipe {
  id: number
  title: string
  vegetables_used: string[]
  ingredients: Array<{
    name: string
    quantity: string
  }>
  steps: string[]
  cooking_time?: number
  difficulty?: '简单' | '中等' | '困难'
  image_url?: string
  created_at: string
}

export interface PlantingIntent {
  next_season_vegetables: Array<{
    name: string
    planting_area: number
    expected_yield: number
    priority: '高' | '中' | '低'
  }>
  share_adjustments: Record<string, any>
  member_preferences: {
    most_popular: string[]
    least_popular: string[]
    common_requests: string[]
  }
  recommendations: string[]
}
