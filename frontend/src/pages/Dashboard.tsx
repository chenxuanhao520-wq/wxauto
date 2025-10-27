import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Table, Typography, Space, Button } from 'antd'
import { 
  MessageOutlined, 
  UserOutlined, 
  SettingOutlined, 
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons'
import { healthService } from '../services/configService'

const { Title, Text } = Typography

interface HealthStatus {
  status: string
  timestamp: string
  services: {
    database: string
    vector: string
    ai_gateway: string
    config: string
  }
}

const Dashboard: React.FC = () => {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)

  // 加载健康状态
  const loadHealthStatus = async () => {
    try {
      setLoading(true)
      const response = await healthService.check()
      setHealthStatus(response.data)
    } catch (error) {
      console.error('加载健康状态失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHealthStatus()
    
    // 定期刷新状态
    const interval = setInterval(loadHealthStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  // 状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'warning':
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      default:
        return <ExclamationCircleOutlined style={{ color: '#d9d9d9' }} />
    }
  }

  // 服务状态表格数据
  const serviceColumns = [
    {
      title: '服务名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Space>
          {getStatusIcon(status)}
          <Text>{status}</Text>
        </Space>
      )
    }
  ]

  const serviceData = healthStatus ? [
    { key: '1', name: '数据库', status: healthStatus.services.database },
    { key: '2', name: '向量数据库', status: healthStatus.services.vector },
    { key: '3', name: 'AI网关', status: healthStatus.services.ai_gateway },
    { key: '4', name: '配置管理', status: healthStatus.services.config },
  ] : []

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Title level={2}>系统仪表盘</Title>
      
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="系统状态"
              value={healthStatus?.status || 'unknown'}
              prefix={getStatusIcon(healthStatus?.status || 'unknown')}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="在线用户"
              value={0}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="今日消息"
              value={0}
              prefix={<MessageOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="配置项"
              value={0}
              prefix={<SettingOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card 
            title="服务状态" 
            extra={
              <Button onClick={loadHealthStatus} loading={loading}>
                刷新
              </Button>
            }
          >
            <Table 
              dataSource={serviceData}
              columns={serviceColumns}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="系统信息">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>系统版本:</Text> <Text>v1.0.0</Text>
              </div>
              <div>
                <Text strong>最后更新:</Text> <Text>{healthStatus?.timestamp ? new Date(healthStatus.timestamp).toLocaleString() : '-'}</Text>
              </div>
              <div>
                <Text strong>运行时间:</Text> <Text>0 天 0 小时</Text>
              </div>
              <div>
                <Text strong>内存使用:</Text> <Text>0 MB</Text>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
