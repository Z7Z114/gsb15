import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Send,
  Upload,
  Mic,
  FileText,
  Sparkles,
  Star,
  ThumbsUp,
  Truck
} from 'lucide-react'
import { conversationAPI, aiAPI } from '../services/api'
import type { Message, Transcript, Feedback } from '../types'

export default function ConversationDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const [messages, setMessages] = useState<Message[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [transcript, setTranscript] = useState<Transcript | null>(null)
  const [transcribeStatus, setTranscribeStatus] = useState<any>(null)
  const [feedback, setFeedback] = useState('')
  const [feedbackType, setFeedbackType] = useState('taste')
  const [rating, setRating] = useState(5)
  const [loading, setLoading] = useState(true)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [extractedFeedback, setExtractedFeedback] = useState<any>(null)

  useEffect(() => {
    if (!id) return
    const fetchData = async () => {
      try {
        const [messagesRes, transcriptRes] = await Promise.all([
          conversationAPI.getMessages(parseInt(id)),
          conversationAPI.getTranscript(parseInt(id))
        ])
        setMessages(messagesRes.data)
        if (transcriptRes.data) {
          setTranscript(transcriptRes.data)
        }
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [id])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    if (!newMessage.trim() || !id) return

    try {
      const res = await conversationAPI.addMessage({
        conversation_id: parseInt(id),
        sender_role: 'consumer',
        content: newMessage
      })
      setMessages((prev) => [...prev, res.data])
      setNewMessage('')
    } catch (error) {
      console.error('Failed to send message:', error)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !id) return

    try {
      await conversationAPI.uploadAudio(parseInt(id), file)
      alert('音频上传成功！')
    } catch (error) {
      console.error('Failed to upload audio:', error)
      alert('上传失败')
    }
  }

  const startTranscription = async () => {
    if (!id) return
    setIsTranscribing(true)
    try {
      await aiAPI.transcribe(parseInt(id))
      const checkStatus = async () => {
        const res = await aiAPI.getTranscribeStatus(parseInt(id))
        setTranscribeStatus(res.data)
        if (!res.data.has_processed_transcript) {
          setTimeout(checkStatus, 2000)
        } else {
          setIsTranscribing(false)
          const transcriptRes = await conversationAPI.getTranscript(parseInt(id))
          setTranscript(transcriptRes.data)
        }
      }
      setTimeout(checkStatus, 2000)
    } catch (error) {
      console.error('Failed to start transcription:', error)
      setIsTranscribing(false)
    }
  }

  const extractFeedback = async () => {
    if (!id) return
    try {
      const res = await aiAPI.extractFeedback(parseInt(id))
      setExtractedFeedback(res.data.feedback)
    } catch (error) {
      console.error('Failed to extract feedback:', error)
    }
  }

  const submitFeedback = async () => {
    if (!feedback.trim() || !id) return
    try {
      await conversationAPI.addFeedback({
        member_id: 2,
        conversation_id: parseInt(id),
        feedback_type: feedbackType,
        content: feedback,
        rating
      })
      setFeedback('')
      alert('反馈提交成功！')
    } catch (error) {
      console.error('Failed to submit feedback:', error)
      alert('提交失败')
    }
  }

  const formatTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const feedbackTypeConfig = [
    { value: 'taste', label: '口味偏好', icon: Star },
    { value: 'delivery', label: '配送反馈', icon: Truck },
    { value: 'quality', label: '品质反馈', icon: ThumbsUp },
    { value: 'other', label: '其他', icon: FileText },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500" />
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col gap-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/conversations')}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-xl font-semibold text-gray-800">对话详情 #{id}</h2>
          <p className="text-sm text-gray-500">会员对话记录</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6 flex-1 min-h-0">
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm flex flex-col">
          <div className="p-4 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-gray-800">对话消息</h3>
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg cursor-pointer transition-colors">
                  <Upload className="w-4 h-4" />
                  <span>上传音频</span>
                  <input
                    type="file"
                    accept="audio/*"
                    className="hidden"
                    onChange={handleFileUpload}
                  />
                </label>
                {transcript && !transcript.processed_transcript && (
                  <button
                    onClick={startTranscription}
                    disabled={isTranscribing}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors disabled:opacity-50"
                  >
                    <Mic className="w-4 h-4" />
                    {isTranscribing ? '转写中...' : '开始转写'}
                  </button>
                )}
                {transcript?.processed_transcript && (
                  <button
                    onClick={extractFeedback}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                  >
                    <Sparkles className="w-4 h-4" />
                    提取反馈
                  </button>
                )}
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.sender_role === 'consumer' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[70%] px-4 py-2 rounded-2xl ${
                    msg.sender_role === 'consumer'
                      ? 'bg-green-500 text-white rounded-br-sm'
                      : 'bg-gray-100 text-gray-800 rounded-bl-sm'
                  }`}
                >
                  <p className="text-sm">{msg.content}</p>
                  <p className={`text-xs mt-1 ${msg.sender_role === 'consumer' ? 'text-green-100' : 'text-gray-400'}`}>
                    {formatTime(msg.timestamp)}
                  </p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-4 border-t border-gray-100">
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="输入消息..."
                className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              />
              <button
                onClick={sendMessage}
                className="p-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {transcript?.processed_transcript && (
            <div className="bg-white rounded-xl p-4 shadow-sm">
              <h3 className="font-medium text-gray-800 mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                转写结果
              </h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {transcript.processed_transcript.segments.map((seg, index) => (
                  <div key={index} className="text-sm p-2 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-purple-600 font-medium">
                        {transcript.processed_transcript.speaker_roles[seg.speaker || ''] || seg.speaker || '未知'}
                      </span>
                      <span className="text-xs text-gray-400">
                        {Math.floor(seg.start / 60)}:{String(Math.floor(seg.start % 60)).padStart(2, '0')}
                      </span>
                    </div>
                    <p className="text-gray-700">{seg.text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {extractedFeedback && (
            <div className="bg-white rounded-xl p-4 shadow-sm">
              <h3 className="font-medium text-gray-800 mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-yellow-500" />
                AI 提取的反馈
              </h3>
              <div className="space-y-3">
                {extractedFeedback.taste_preferences?.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-1">口味偏好</p>
                    <div className="flex flex-wrap gap-1">
                      {extractedFeedback.taste_preferences.map((pref: string, i: number) => (
                        <span key={i} className="text-xs px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full">
                          {pref}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {extractedFeedback.delivery_feedback?.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-1">配送反馈</p>
                    <ul className="text-sm text-gray-700 list-disc list-inside">
                      {extractedFeedback.delivery_feedback.map((item: string, i: number) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {extractedFeedback.suggestions?.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-1">建议</p>
                    <ul className="text-sm text-gray-700 list-disc list-inside">
                      {extractedFeedback.suggestions.map((item: string, i: number) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="bg-white rounded-xl p-4 shadow-sm">
            <h3 className="font-medium text-gray-800 mb-3">提交反馈</h3>
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {feedbackTypeConfig.map((type) => {
                  const Icon = type.icon
                  return (
                    <button
                      key={type.value}
                      onClick={() => setFeedbackType(type.value)}
                      className={`flex items-center gap-1 px-3 py-1.5 text-xs rounded-lg transition-colors ${
                        feedbackType === type.value
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      <Icon className="w-3 h-3" />
                      {type.label}
                    </button>
                  )
                })}
              </div>

              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => setRating(star)}
                    className="p-0.5"
                  >
                    <Star
                      className={`w-5 h-5 ${
                        star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
                      }`}
                    />
                  </button>
                ))}
              </div>

              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="请输入您的反馈..."
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
                rows={3}
              />

              <button
                onClick={submitFeedback}
                className="w-full py-2 bg-green-500 text-white rounded-lg text-sm font-medium hover:bg-green-600 transition-colors"
              >
                提交反馈
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
