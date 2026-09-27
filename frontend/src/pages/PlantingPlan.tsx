import { useEffect, useState } from 'react'
import { Sprout, TrendingUp, Mail, RefreshCw, PieChart, Users } from 'lucide-react'
import { aiAPI, emailAPI, vegetableAPI } from '../services/api'
import type { PlantingIntent, AISummary, Vegetable } from '../types'

export default function PlantingPlan() {
  const [plantingIntent, setPlantingIntent] = useState<PlantingIntent | null>(null)
  const [summaries, setSummaries] = useState<AISummary[]>([])
  const [vegetables, setVegetables] = useState<Vegetable[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [sending, setSending] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [summariesRes, vegRes] = await Promise.all([
          aiAPI.getSummaries('planting_intent'),
          vegetableAPI.getAll()
        ])
        setSummaries(summariesRes.data)
        setVegetables(vegRes.data)
        if (summariesRes.data.length > 0) {
          setPlantingIntent(summariesRes.data[0].content as PlantingIntent)
        }
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const generatePlan = async () => {
    setGenerating(true)
    try {
      const res = await aiAPI.generatePlantingIntent()
      setPlantingIntent(res.data)
      const summariesRes = await aiAPI.getSummaries('planting_intent')
      setSummaries(summariesRes.data)
    } catch (error) {
      console.error('Failed to generate planting intent:', error)
    } finally {
      setGenerating(false)
    }
  }

  const sendToAllMembers = async () => {
    if (!summaries[0]) return
    setSending(true)
    try {
      await emailAPI.sendPlantingIntent(summaries[0].id)
      alert('种植计划已发送给所有会员！')
    } catch (error) {
      console.error('Failed to send email:', error)
      alert('发送失败')
    } finally {
      setSending(false)
    }
  }

  const priorityColor: Record<string, string> = {
    '高': 'bg-red-100 text-red-700',
    '中': 'bg-yellow-100 text-yellow-700',
    '低': 'bg-green-100 text-green-700',
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
        <h2 className="text-xl font-semibold text-gray-800">下一季种植计划</h2>
        <div className="flex gap-3">
          <button
            onClick={generatePlan}
            disabled={generating}
            className="flex items-center gap-2 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
            {generating ? '生成中...' : '生成新计划'}
          </button>
          {plantingIntent && (
            <button
              onClick={sendToAllMembers}
              disabled={sending}
              className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
            >
              <Mail className="w-4 h-4" />
              {sending ? '发送中...' : '发送给会员'}
            </button>
          )}
        </div>
      </div>

      {!plantingIntent ? (
        <div className="bg-white rounded-xl p-12 text-center shadow-sm">
          <Sprout className="w-16 h-16 text-green-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-800 mb-2">还没有种植计划</h3>
          <p className="text-gray-500 mb-4">点击上方按钮，基于会员反馈生成下一季的种植计划</p>
          <button
            onClick={generatePlan}
            disabled={generating}
            className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
          >
            {generating ? '生成中...' : '开始生成'}
          </button>
        </div>
      ) : (
        <>
          <div className="grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-white rounded-xl p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <Sprout className="w-5 h-5 text-green-500" />
                拟种植蔬菜
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">蔬菜名称</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">种植面积(亩)</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">预计产量(公斤)</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">优先级</th>
                    </tr>
                  </thead>
                  <tbody>
                    {plantingIntent.next_season_vegetables.map((veg, index) => (
                      <tr key={index} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-3 px-4 text-sm font-medium text-gray-800">{veg.name}</td>
                        <td className="py-3 px-4 text-sm text-gray-600">{veg.planting_area}</td>
                        <td className="py-3 px-4 text-sm text-gray-600">{veg.expected_yield}</td>
                        <td className="py-3 px-4">
                          <span className={`text-xs px-2 py-1 rounded-full ${priorityColor[veg.priority]}`}>
                            {veg.priority}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="space-y-6">
              <div className="bg-white rounded-xl p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <PieChart className="w-5 h-5 text-purple-500" />
                  份额调整
                </h3>
                <div className="space-y-3">
                  {Object.entries(plantingIntent.share_adjustments).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">{key}</span>
                      <span className={`text-sm font-medium ${
                        String(value).includes('+') ? 'text-green-600' :
                        String(value).includes('-') ? 'text-red-600' : 'text-gray-600'
                      }`}>
                        {String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-xl p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <Users className="w-5 h-5 text-blue-500" />
                  会员偏好分析
                </h3>
                <div className="space-y-4">
                  <div>
                    <p className="text-xs text-gray-500 mb-2">最受欢迎</p>
                    <div className="flex flex-wrap gap-1">
                      {plantingIntent.member_preferences.most_popular?.map((item, i) => (
                        <span key={i} className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-2">待改进</p>
                    <div className="flex flex-wrap gap-1">
                      {plantingIntent.member_preferences.least_popular?.map((item, i) => (
                        <span key={i} className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded-full">
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-orange-500" />
              建议
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              {plantingIntent.recommendations.map((rec, index) => (
                <div key={index} className="flex items-start gap-3 p-4 bg-orange-50 rounded-lg">
                  <div className="w-6 h-6 bg-orange-500 text-white rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0">
                    {index + 1}
                  </div>
                  <p className="text-sm text-gray-700">{rec}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">历史计划</h3>
            <div className="space-y-3">
              {summaries.slice(0, 5).map((summary, index) => (
                <div
                  key={summary.id}
                  className={`flex items-center justify-between p-4 rounded-lg cursor-pointer transition-colors ${
                    index === 0 ? 'bg-green-50 border border-green-200' : 'bg-gray-50 hover:bg-gray-100'
                  }`}
                  onClick={() => setPlantingIntent(summary.content as PlantingIntent)}
                >
                  <div>
                    <p className="font-medium text-gray-800">
                      种植计划 v{summary.version}
                    </p>
                    <p className="text-sm text-gray-500">
                      {new Date(summary.created_at).toLocaleDateString('zh-CN', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>
                  {index === 0 && (
                    <span className="text-xs px-2 py-1 bg-green-500 text-white rounded-full">
                      当前
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
