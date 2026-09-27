import { useEffect, useState } from 'react'
import { Calendar as CalendarIcon, Check, Clock, Droplets, Sprout, Scissors } from 'lucide-react'
import { calendarAPI, vegetableAPI } from '../services/api'
import type { PlantingCalendar, Vegetable } from '../types'

export default function Calendar() {
  const [calendarEntries, setCalendarEntries] = useState<PlantingCalendar[]>([])
  const [vegetables, setVegetables] = useState<Vegetable[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedMonth, setSelectedMonth] = useState(new Date())

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [calendarRes, vegRes] = await Promise.all([
          calendarAPI.getAll(),
          vegetableAPI.getAll()
        ])
        setCalendarEntries(calendarRes.data)
        setVegetables(vegRes.data)
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const activityConfig: Record<string, { icon: any; color: string; bgColor: string; label: string }> = {
    planting: { icon: Sprout, color: 'text-green-600', bgColor: 'bg-green-100', label: '播种' },
    watering: { icon: Droplets, color: 'text-blue-600', bgColor: 'bg-blue-100', label: '浇水' },
    fertilizing: { icon: Sprout, color: 'text-yellow-600', bgColor: 'bg-yellow-100', label: '施肥' },
    harvesting: { icon: Scissors, color: 'text-orange-600', bgColor: 'bg-orange-100', label: '收获' },
  }

  const getVegetableName = (vegetableId: number) => {
    return vegetables.find((v) => v.id === vegetableId)?.name || '未知蔬菜'
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('zh-CN', {
      month: 'long',
      day: 'numeric',
      weekday: 'short'
    })
  }

  const toggleCompleted = async (id: number) => {
    try {
      await calendarAPI.toggle(id)
      setCalendarEntries((prev) =>
        prev.map((entry) =>
          entry.id === id ? { ...entry, completed: !entry.completed } : entry
        )
      )
    } catch (error) {
      console.error('Failed to toggle completed:', error)
    }
  }

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear()
    const month = date.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const days = []

    for (let i = 0; i < firstDay.getDay(); i++) {
      days.push(null)
    }

    for (let i = 1; i <= lastDay.getDate(); i++) {
      days.push(new Date(year, month, i))
    }

    return days
  }

  const getEntriesForDate = (date: Date | null) => {
    if (!date) return []
    const dateStr = date.toISOString().split('T')[0]
    return calendarEntries.filter((entry) => entry.activity_date === dateStr)
  }

  const prevMonth = () => {
    setSelectedMonth(new Date(selectedMonth.getFullYear(), selectedMonth.getMonth() - 1, 1))
  }

  const nextMonth = () => {
    setSelectedMonth(new Date(selectedMonth.getFullYear(), selectedMonth.getMonth() + 1, 1))
  }

  const days = getDaysInMonth(selectedMonth)
  const weekDays = ['日', '一', '二', '三', '四', '五', '六']

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <button
              onClick={prevMonth}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              ←
            </button>
            <h2 className="text-xl font-semibold text-gray-800">
              {selectedMonth.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long' })}
            </h2>
            <button
              onClick={nextMonth}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              →
            </button>
          </div>
          <div className="flex items-center gap-2">
            {Object.entries(activityConfig).map(([key, config]) => {
              const Icon = config.icon
              return (
                <div key={key} className="flex items-center gap-1 text-xs text-gray-500">
                  <Icon className={`w-4 h-4 ${config.color}`} />
                  <span>{config.label}</span>
                </div>
              )
            })}
          </div>
        </div>

        <div className="grid grid-cols-7 gap-1">
          {weekDays.map((day) => (
            <div
              key={day}
              className="text-center text-sm font-medium text-gray-500 py-2"
            >
              {day}
            </div>
          ))}
          {days.map((date, index) => {
            const entries = getEntriesForDate(date)
            const isToday = date && date.toDateString() === new Date().toDateString()
            return (
              <div
                key={index}
                className={`min-h-24 p-2 border border-gray-100 rounded-lg ${
                  date ? 'bg-white hover:bg-gray-50' : 'bg-gray-50'
                } ${isToday ? 'ring-2 ring-green-500' : ''}`}
              >
                {date && (
                  <>
                    <div className="text-sm font-medium text-gray-700 mb-1">
                      {date.getDate()}
                    </div>
                    <div className="space-y-1">
                      {entries.slice(0, 2).map((entry) => {
                        const config = activityConfig[entry.activity_type]
                        const Icon = config?.icon || Clock
                        return (
                          <div
                            key={entry.id}
                            className={`text-xs p-1 rounded flex items-center gap-1 ${
                              entry.completed ? 'opacity-50 line-through' : ''
                            } ${config?.bgColor || 'bg-gray-100'}`}
                          >
                            <Icon className={`w-3 h-3 ${config?.color || 'text-gray-500'}`} />
                            <span className="truncate">{getVegetableName(entry.vegetable_id)}</span>
                          </div>
                        )
                      })}
                      {entries.length > 2 && (
                        <div className="text-xs text-gray-400">+{entries.length - 2} 更多</div>
                      )}
                    </div>
                  </>
                )}
              </div>
            )
          })}
        </div>
      </div>

      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">即将到来的农事活动</h3>
        <div className="space-y-3">
          {calendarEntries
            .filter((entry) => !entry.completed && new Date(entry.activity_date) >= new Date())
            .sort((a, b) => new Date(a.activity_date).getTime() - new Date(b.activity_date).getTime())
            .slice(0, 10)
            .map((entry) => {
              const config = activityConfig[entry.activity_type]
              const Icon = config?.icon || Clock
              return (
                <div
                  key={entry.id}
                  className="flex items-center justify-between p-3 border border-gray-100 rounded-lg hover:border-green-200 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${config?.bgColor || 'bg-gray-100'}`}>
                      <Icon className={`w-5 h-5 ${config?.color || 'text-gray-500'}`} />
                    </div>
                    <div>
                      <p className="font-medium text-gray-800">
                        {config?.label} - {getVegetableName(entry.vegetable_id)}
                      </p>
                      <p className="text-sm text-gray-500">
                        {formatDate(entry.activity_date)}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => toggleCompleted(entry.id)}
                    className={`p-2 rounded-lg transition-colors ${
                      entry.completed
                        ? 'bg-green-100 text-green-600'
                        : 'bg-gray-100 text-gray-400 hover:bg-green-50 hover:text-green-500'
                    }`}
                  >
                    <Check className="w-5 h-5" />
                  </button>
                </div>
              )
            })}
        </div>
      </div>
    </div>
  )
}
