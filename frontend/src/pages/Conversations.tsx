import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { MessageSquare, Plus, User, Clock } from 'lucide-react'
import { conversationAPI, memberAPI } from '../services/api'
import type { Conversation, Member } from '../types'

export default function Conversations() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [members, setMembers] = useState<Member[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [convRes, memberRes] = await Promise.all([
          conversationAPI.getAll(),
          memberAPI.getAll()
        ])
        setConversations(convRes.data)
        setMembers(memberRes.data)
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const getMemberName = (memberId: number) => {
    return members.find((m) => m.id === memberId)?.name || '未知会员'
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const statusConfig: Record<string, { label: string; color: string }> = {
    active: { label: '进行中', color: 'bg-green-100 text-green-700' },
    closed: { label: '已关闭', color: 'bg-gray-100 text-gray-600' },
    archived: { label: '已归档', color: 'bg-blue-100 text-blue-700' },
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-800">会员对话</h2>
        <button className="flex items-center gap-2 bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors">
          <Plus className="w-4 h-4" />
          新建对话
        </button>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {conversations.map((conv) => {
          const status = statusConfig[conv.status]
          return (
            <Link
              key={conv.id}
              to={`/conversations/${conv.id}`}
              className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 hover:border-green-200 hover:shadow-md transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-800">{getMemberName(conv.member_id)}</h3>
                    <p className="text-xs text-gray-500">{conv.title || '无标题对话'}</p>
                  </div>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${status?.color}`}>
                  {status?.label}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <MessageSquare className="w-3 h-3" />
                <span>对话 #{conv.id}</span>
                <span className="mx-1">·</span>
                <Clock className="w-3 h-3" />
                <span>{formatDate(conv.created_at)}</span>
              </div>
            </Link>
          )
        })}
      </div>

      {conversations.length === 0 && (
        <div className="text-center py-12">
          <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">暂无对话记录</p>
          <p className="text-sm text-gray-400 mt-1">点击右上角按钮创建新对话</p>
        </div>
      )}
    </div>
  )
}
