import { useEffect, useState } from 'react'
import { Leaf, Info, Calendar, Package } from 'lucide-react'
import { vegetableAPI } from '../services/api'
import type { Vegetable } from '../types'

export default function Vegetables() {
  const [vegetables, setVegetables] = useState<Vegetable[]>([])
  const [selectedSeason, setSelectedSeason] = useState<string>('')
  const [selectedVegetable, setSelectedVegetable] = useState<Vegetable | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchVegetables = async () => {
      try {
        const res = await vegetableAPI.getAll(selectedSeason || undefined)
        setVegetables(res.data)
      } catch (error) {
        console.error('Failed to fetch vegetables:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchVegetables()
  }, [selectedSeason])

  const seasonMap: Record<string, { label: string; color: string; bgColor: string }> = {
    spring: { label: '春季', color: 'text-green-700', bgColor: 'bg-green-100' },
    summer: { label: '夏季', color: 'text-yellow-700', bgColor: 'bg-yellow-100' },
    autumn: { label: '秋季', color: 'text-orange-700', bgColor: 'bg-orange-100' },
    winter: { label: '冬季', color: 'text-blue-700', bgColor: 'bg-blue-100' },
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('zh-CN')
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
        <h2 className="text-xl font-semibold text-gray-800">当季蔬菜品种</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setSelectedSeason('')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              selectedSeason === ''
                ? 'bg-green-500 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            全部
          </button>
          {Object.entries(seasonMap).map(([key, value]) => (
            <button
              key={key}
              onClick={() => setSelectedSeason(key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedSeason === key
                  ? `${value.bgColor} ${value.color}`
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              {value.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {vegetables.map((veg) => {
          const season = seasonMap[veg.season]
          return (
            <div
              key={veg.id}
              onClick={() => setSelectedVegetable(veg)}
              className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 hover:border-green-200 hover:shadow-md transition-all cursor-pointer"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 ${season?.bgColor} rounded-xl flex items-center justify-center`}>
                    <Leaf className={`w-6 h-6 ${season?.color}`} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-800">{veg.name}</h3>
                    {veg.english_name && (
                      <p className="text-xs text-gray-400">{veg.english_name}</p>
                    )}
                  </div>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${season?.bgColor} ${season?.color}`}>
                  {season?.label}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-3 line-clamp-2">{veg.description}</p>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  <span>种植: {formatDate(veg.planting_start)}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Package className="w-3 h-3" />
                  <span>份额: {veg.share_quota}份</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {selectedVegetable && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedVegetable(null)}
        >
          <div
            className="bg-white rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-14 h-14 ${seasonMap[selectedVegetable.season]?.bgColor} rounded-xl flex items-center justify-center`}>
                    <Leaf className={`w-7 h-7 ${seasonMap[selectedVegetable.season]?.color}`} />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-800">{selectedVegetable.name}</h3>
                    {selectedVegetable.english_name && (
                      <p className="text-sm text-gray-400">{selectedVegetable.english_name}</p>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => setSelectedVegetable(null)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-500 mb-1">描述</h4>
                  <p className="text-gray-700">{selectedVegetable.description}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 rounded-lg p-3">
                    <h4 className="text-xs text-gray-500 mb-1">种植时间</h4>
                    <p className="text-sm text-gray-700">
                      {formatDate(selectedVegetable.planting_start)} - {formatDate(selectedVegetable.planting_end)}
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <h4 className="text-xs text-gray-500 mb-1">收获时间</h4>
                    <p className="text-sm text-gray-700">
                      {formatDate(selectedVegetable.harvest_start)} - {formatDate(selectedVegetable.harvest_end)}
                    </p>
                  </div>
                </div>

                {selectedVegetable.nutritional_value && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-500 mb-1">营养价值</h4>
                    <p className="text-sm text-gray-700">{selectedVegetable.nutritional_value}</p>
                  </div>
                )}

                {selectedVegetable.storage_method && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-500 mb-1">保存方法</h4>
                    <p className="text-sm text-gray-700">{selectedVegetable.storage_method}</p>
                  </div>
                )}

                <div className="bg-green-50 rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <Info className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-green-700">本周份额</span>
                  </div>
                  <p className="text-2xl font-bold text-green-600 mt-1">
                    {selectedVegetable.share_quota} 份
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
