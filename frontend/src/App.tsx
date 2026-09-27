import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Vegetables from './pages/Vegetables'
import Calendar from './pages/Calendar'
import Conversations from './pages/Conversations'
import ConversationDetail from './pages/ConversationDetail'
import PlantingPlan from './pages/PlantingPlan'
import Recipes from './pages/Recipes'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/vegetables" element={<Vegetables />} />
        <Route path="/calendar" element={<Calendar />} />
        <Route path="/conversations" element={<Conversations />} />
        <Route path="/conversations/:id" element={<ConversationDetail />} />
        <Route path="/planting-plan" element={<PlantingPlan />} />
        <Route path="/recipes" element={<Recipes />} />
      </Routes>
    </Layout>
  )
}

export default App
