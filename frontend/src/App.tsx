import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Layout } from 'antd'
import ConfigManagement from './pages/ConfigManagement'
import Dashboard from './pages/Dashboard'
import Header from './components/Header'
import './App.css'

const { Content } = Layout

function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header />
      <Content style={{ padding: '24px' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/config" element={<ConfigManagement />} />
        </Routes>
      </Content>
    </Layout>
  )
}

export default App
