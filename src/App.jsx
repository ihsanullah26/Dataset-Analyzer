import Name from './Name.jsx'
import DataPlacer from './assets/DataPlacer.jsx'

export default function App() {
  return (
    <div className="flex flex-col  items-center h-screen bg-gradient-to-r from-pink-100 to-purple-100 gap-10 mt-12">
      <Name/>
      <DataPlacer/>
    </div>
  )
}
