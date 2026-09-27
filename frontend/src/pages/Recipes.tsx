import { useEffect, useState } from 'react'
import { BookOpen, Clock, ChefHat } from 'lucide-react'
import { aiAPI } from '../services/api'
import type { Recipe } from '../types'

export default function Recipes() {
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchRecipes = async () => {
      try {
        const res = await aiAPI.getRecipes()
        setRecipes(res.data)
      } catch (error) {
        console.error('Failed to fetch recipes:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchRecipes()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
        <BookOpen className="w-5 h-5 text-green-600" />
        推荐食谱
      </h2>

      {recipes.length === 0 ? (
        <div className="text-center py-12">
          <ChefHat className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">暂无食谱</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-4">
          {recipes.map((recipe) => (
            <div key={recipe.id} className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-800">{recipe.title}</h3>
                <span className="text-xs px-2 py-1 rounded-full bg-green-100 text-green-700">
                  {recipe.difficulty}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500 mb-3">
                <Clock className="w-3 h-3" />
                <span>{recipe.cooking_time} 分钟</span>
                <span>·</span>
                <span>{recipe.vegetables_used.join('、')}</span>
              </div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">食材</h4>
              <ul className="text-sm text-gray-600 list-disc list-inside mb-3">
                {recipe.ingredients.map((ing, i) => (
                  <li key={i}>{ing.name}: {ing.quantity}</li>
                ))}
              </ul>
              <h4 className="text-sm font-medium text-gray-700 mb-2">步骤</h4>
              <ol className="text-sm text-gray-600 list-decimal list-inside space-y-1">
                {recipe.steps.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
