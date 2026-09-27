import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Leaf, Calendar, MessageSquare, Users, TrendingUp, BookOpen } from 'lucide-react'
import { vegetableAPI, memberAPI, aiAPI } from '../services/api'
import type { Vegetable, Member, Recipe } from '../types'

export default function Home() {
  const [vegetables, setVegetables] = useState<Vegetable[]>([])
  const [members, setMembers] = useState<Member[]>([])
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [vegRes, memberRes, recipeRes] = await Promise.all([
          vegetableAPI.getAll(),
          memberAPI.getAll(),
          aiAPI.getRecipes()
        ])
        setVegetables(vegRes.data.slice(0, 4))
        setMembers(memberRes.data)
        setRecipes(recipeRes.data.slice(0, 3))
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const stats = [
    { label: '当季蔬菜', value: vegetables.length, icon: Leaf, color: 'bg-green-500' },
    { label: '会员总数', value: members.length, icon: Users, color: 'bg-blue-500' },
    { label: '推荐食谱', value: recipes.length, icon: BookOpen, color: 'bg-orange-500' },
    { label: '种植计划', value: '进行中', icon: TrendingUp, color: 'bg-purple-500' },
  ]

  const seasonMap: Record<string, { label: string; color: string }> = {
    spring: { label: '春季', color: 'bg-green-100 text-green-700' },
    summer: { label: '夏季', color: 'bg-yellow-100 text-yellow-700' },
    autumn: { label: '秋季', color: 'bg-orange-100 text-orange-700' },
    winter: { label: '冬季', color: 'bg-blue-100 text-blue-700' },
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
      <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-2xl p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">欢迎来到 CSA 社区支持农业</h1>
        <p className="text-green-100 mb-4">
          连接农人与消费者，共享健康、可持续的生活方式
        </p>
        <div className="flex gap-3">
          <Link
            to="/vegetables"
            className="bg-white text-green-600 px-4 py-2 rounded-lg font-medium hover:bg-green-50 transition-colors"
          >
            查看当季蔬菜
          </Link>
          <Link
            to="/conversations"
            className="bg-green-600 text-white border border-green-400 px-4 py-2 rounded-lg font-medium hover:bg-green-700 transition-colors"
          >
            参与会员对话
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <div key={index} className="bg-white rounded-xl p-4 shadow-sm">
              <div className="flex items-center gap-3">
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-800">{stat.value}</p>
                  <p className="text-sm text-gray-500">{stat.label}</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800">当季蔬菜</h2>
            <Link to="/vegetables" className="text-green-600 text-sm hover:underline">
              查看全部
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {vegetables.map((veg) => (
              <div
                key={veg.id}
                className="border border-gray-100 rounded-lg p-3 hover:border-green-200 transition-colors"
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${seasonMap[veg.season]?.color}`}>
                    {seasonMap[veg.season]?.label}
                  </span>
                </div>
                <h3 className="font-medium text-gray-800">{veg.name}</h3>
                <p className="text-xs text-gray-500 mt-1 line-clamp-2">{veg.description}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800">推荐食谱</h2>
            <Link to="/recipes" className="text-green-600 text-sm hover:underline">
              查看全部
            </Link>
          </div>
          <div className="space-y-3">
            {recipes.map((recipe) => (
              <div
                key={recipe.id}
                className="flex items-center gap-4 p-3 border border-gray-100 rounded-lg hover:border-green-200 transition-colors"
              >
                <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                  <BookOpen className="w-6 h-6 text-orange-500" />
                </div>
                <div className="flex-1">
                  <h3 className="font-medium text-gray-800">{recipe.title}</h3>
                  <p className="text-xs text-gray-500">
                    用时: {recipe.cooking_time}分钟 · 难度: {recipe.difficulty}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">快速入口</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Link
            to="/calendar"
            className="flex flex-col items-center gap-2 p-4 bg-blue-50 rounded-xl hover:bg-blue-100 transition-colors"
          >
            <Calendar className="w-8 h-8 text-blue-500" />
            <span className="text-sm font-medium text-gray-700">种植日历</span>
          </Link>
          <Link
            to="/conversations"
            className="flex flex-col items-center gap-2 p-4 bg-purple-50 rounded-xl hover:bg-purple-100 transition-colors"
          >
            <MessageSquare className="w-8 h-8 text-purple-500" />
            <span className="text-sm font-medium text-gray-700">会员对话</span>
          </Link>
          <Link
            to="/planting-plan"
            className="flex flex-col items-center gap-2 p-4 bg-green-50 rounded-xl hover:bg-green-100 transition-colors"
          >
            <TrendingUp className="w-8 h-8 text-green-500" />
            <span className="text-sm font-medium text-gray-700">种植计划</span>
          </Link>
          <Link
            to="/members"
            className="flex flex-col items-center gap-2 p-4 bg-orange-50 rounded-xl hover:bg-orange-100 transition-colors"
          >
            <Users className="w-8 h-8 text-orange-500" />
            <span className="text-sm font-medium text-gray-700">会员管理</span>
          </Link>
        </div>
      </div>
    </div>
  )
}
