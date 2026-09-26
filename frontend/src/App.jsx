// src/App.jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

import Login from './pages/Login'
import SignUp from './pages/SignUp'
import PasswordReset from './pages/PasswordReset'
import Dashboard from './pages/Dashboard'
import Stock from './pages/Stock'
import Receipts from './pages/Receipts'
import ReceiptDetail from './pages/ReceiptDetail'
import Delivery from './pages/Delivery'
import DeliveryDetail from './pages/DeliveryDetail'
import MoveHistory from './pages/MoveHistory'
import Warehouse from './pages/Warehouse'
import Location from './pages/Location'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Auth */}
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/forgot-password" element={<PasswordReset />} />

        {/* Core app */}
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/products" element={<Stock />} />

        {/* Operations */}
        <Route path="/receipts" element={<Receipts />} />
        <Route path="/receipts/:id" element={<ReceiptDetail />} />
        <Route path="/delivery" element={<Delivery />} />
        <Route path="/delivery/:id" element={<DeliveryDetail />} />

        {/* Move history */}
        <Route path="/move-history" element={<MoveHistory />} />

        {/* Settings */}
        <Route path="/settings/warehouse" element={<Warehouse />} />
        <Route path="/settings/location" element={<Location />} />

        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="*" element={<Navigate to="/login" />} />
        <Route path="/receipts/new" element={<ReceiptDetail />} />
        <Route path="/delivery/new" element={<DeliveryDetail />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App