import React from 'react'
import { Layout, Typography, Button, Space } from 'antd'
import { Link, useLocation } from 'react-router-dom'
import { SettingOutlined, DashboardOutlined } from '@ant-design/icons'

const { Header: AntHeader } = Layout
const { Title } = Typography

const Header: React.FC = () => {
  const location = useLocation()

  return (
    <AntHeader style={{ 
      background: '#fff', 
      padding: '0 24px', 
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    }}>
      <Title level={3} style={{ margin: 0 }}>
        微信客服中台
      </Title>
      <Space>
        <Button 
          type={location.pathname === '/' ? 'primary' : 'default'}
          icon={<DashboardOutlined />}
        >
          <Link to="/">仪表盘</Link>
        </Button>
        <Button 
          type={location.pathname === '/config' ? 'primary' : 'default'}
          icon={<SettingOutlined />}
        >
          <Link to="/config">配置管理</Link>
        </Button>
      </Space>
    </AntHeader>
  )
}

export default Header
