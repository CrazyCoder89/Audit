import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Lobby from './pages/Lobby'
import Room from './pages/Room'


export default function App() {
  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      background: '#0A0E1A',
      overflow: 'hidden'
    }}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Lobby />} />
          <Route path="/room/:id" element={<Room />} />
        </Routes>
      </BrowserRouter>
    </div>
  )
}