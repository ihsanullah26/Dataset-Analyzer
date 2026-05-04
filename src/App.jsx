import Name from './Name.jsx'
import DataPlacer from './DataPlacer.jsx'

export default function App() {
  return (
    <div className="flex flex-col  items-center bg-gradient-to-r from-pink-100 to-purple-100 gap-10 pb-5">
      <Name/>
      <DataPlacer/>
    </div>
  )
}
