import React, { useState, useEffect, useCallback } from 'react'
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Switch, 
  Select, 
  InputNumber, 
  message, 
  Spin, 
  Tabs, 
  Space, 
  Typography, 
  Divider,
  Row,
  Col,
  Badge,
  Tooltip,
  Table
} from 'antd'
import { configService } from '../services/configService'

const { Title, Text } = Typography
const { TabPane } = Tabs

interface ConfigItem {
  key: string
  display_name: string
  value: string
  value_type: string
  is_required: boolean
  is_encrypted: boolean
  help_text?: string
  default_value?: string
}

interface ConfigCategory {
  id: string
  name: string
  display_name: string
  description: string
  items: ConfigItem[]
}

interface ServiceStatus {
  service_name: string
  status: string
  last_check: string
  response_time_ms: number
  error_message?: string
}

const ConfigManagement: React.FC = () => {
  const [categories, setCategories] = useState<ConfigCategory[]>([])
  const [loading, setLoading] = useState(true)
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus[]>([])
  const [activeTab, setActiveTab] = useState('overview')
  const [form] = Form.useForm()

  // 加载配置数据
  const loadConfig = useCallback(async () => {
    try {
      setLoading(true)
      const response = await configService.getCategories()
      setCategories(response.data)
    } catch (error: any) {
      message.error('加载配置失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // 加载服务状态
  const loadServiceStatus = useCallback(async () => {
    try {
      const response = await configService.getStatus()
      setServiceStatus(response.data)
    } catch (error) {
      console.error('加载服务状态失败:', error)
    }
  }, [])

  // 更新配置
  const updateConfig = async (category: string, key: string, value: string) => {
    try {
      await configService.updateConfig({
        category,
        key,
        value,
        created_by: 'admin'
      })
      message.success('配置更新成功')
      loadConfig()
    } catch (error: any) {
      message.error('配置更新失败: ' + error.message)
    }
  }

  // 测试服务连接
  const testServiceConnection = async (category: string) => {
    try {
      const config = {}
      const categoryData = categories.find(cat => cat.name === category)
      if (categoryData) {
        categoryData.items.forEach(item => {
          config[item.key] = item.value || ''
        })
      }

      const response = await configService.testConnection({
        category,
        config
      })

      const status = response.data
      if (status.status === 'healthy') {
        message.success(`${category} 连接测试成功`)
      } else {
        message.warning(`${category} 连接测试失败: ${status.error_message}`)
      }
      
      loadServiceStatus()
    } catch (error: any) {
      message.error('连接测试失败: ' + error.message)
    }
  }

  // 同步配置
  const syncConfig = async () => {
    try {
      await configService.syncConfig()
      message.success('配置同步已启动')
    } catch (error: any) {
      message.error('配置同步失败: ' + error.message)
    }
  }

  // 导出配置
  const exportConfig = async () => {
    try {
      const response = await configService.exportConfig()
      const dataStr = JSON.stringify(response.data, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'config.json'
      link.click()
      URL.revokeObjectURL(url)
      message.success('配置导出成功')
    } catch (error: any) {
      message.error('配置导出失败: ' + error.message)
    }
  }

  useEffect(() => {
    loadConfig()
    loadServiceStatus()
    
    // 定期刷新服务状态
    const interval = setInterval(loadServiceStatus, 30000)
    return () => clearInterval(interval)
  }, [loadConfig, loadServiceStatus])

  // 状态指示器组件
  const StatusIndicator = ({ status }: { status: string }) => {
    const statusClass = `status-${status}`
    return <span className={`status-indicator ${statusClass}`}></span>
  }

  // 服务状态组件
  const ServiceStatusCard = () => {
    const statusColumns = [
      {
        title: '服务名称',
        dataIndex: 'service_name',
        key: 'service_name',
        render: (text: string) => <Text strong>{text}</Text>
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        render: (status: string) => (
          <Space>
            <StatusIndicator status={status} />
            <Text>{status}</Text>
          </Space>
        )
      },
      {
        title: '最后检查',
        dataIndex: 'last_check',
        key: 'last_check',
        render: (time: string) => time ? new Date(time).toLocaleString() : '-'
      },
      {
        title: '响应时间',
        dataIndex: 'response_time_ms',
        key: 'response_time_ms',
        render: (time: number) => time ? `${time}ms` : '-'
      },
      {
        title: '错误信息',
        dataIndex: 'error_message',
        key: 'error_message',
        render: (error: string) => error ? <Text type="danger">{error}</Text> : '-'
      }
    ]

    return (
      <Card title="服务状态" extra={
        <Button onClick={loadServiceStatus} loading={loading}>
          刷新状态
        </Button>
      }>
        <Table 
          dataSource={serviceStatus} 
          columns={statusColumns}
          pagination={false}
          size="small"
        />
      </Card>
    )
  }

  // 配置表单组件
  const ConfigForm = ({ category }: { category: ConfigCategory }) => {
    const handleSubmit = (values: any) => {
      Object.entries(values).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          updateConfig(category.name, key, value.toString())
        }
      })
    }

    return (
      <Card 
        title={category.display_name}
        extra={
          <Space>
            <Button 
              type="primary" 
              onClick={() => testServiceConnection(category.name)}
              loading={loading}
            >
              测试连接
            </Button>
            <Button onClick={() => form.submit()}>
              保存配置
            </Button>
          </Space>
        }
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={category.items.reduce((acc, item) => {
            acc[item.key] = item.value
            return acc
          }, {} as any)}
        >
          {category.items.map(item => (
            <Form.Item
              key={item.key}
              label={
                <Space>
                  <Text strong>{item.display_name}</Text>
                  {item.is_required && <Text type="danger">*</Text>}
                  {item.help_text && (
                    <Tooltip title={item.help_text}>
                      <Text type="secondary">?</Text>
                    </Tooltip>
                  )}
                </Space>
              }
              name={item.key}
              rules={[
                { 
                  required: item.is_required, 
                  message: `请输入${item.display_name}` 
                }
              ]}
            >
              {item.value_type === 'boolean' ? (
                <Switch />
              ) : item.value_type === 'number' ? (
                <InputNumber style={{ width: '100%' }} />
              ) : item.value_type === 'json' ? (
                <Input.TextArea rows={3} />
              ) : item.is_encrypted ? (
                <Input.Password placeholder="输入密码" />
              ) : (
                <Input placeholder={item.default_value} />
              )}
            </Form.Item>
          ))}
        </Form>
      </Card>
    )
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>配置管理系统</Title>
        <Space>
          <Button onClick={syncConfig}>
            同步配置
          </Button>
          <Button onClick={exportConfig}>
            导出配置
          </Button>
        </Space>
      </div>
      
      <Spin spinning={loading}>
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          items={[
            {
              key: 'overview',
              label: '概览',
              children: (
                <div>
                  <ServiceStatusCard />
                  <Divider />
                  <Row gutter={16}>
                    {categories.map(category => (
                      <Col span={8} key={category.id}>
                        <Card 
                          title={category.display_name}
                          extra={
                            <Badge 
                              status={
                                serviceStatus.find(s => s.service_name === category.name)?.status === 'healthy' 
                                  ? 'success' 
                                  : 'error'
                              }
                            />
                          }
                        >
                          <Text type="secondary">
                            {category.description}
                          </Text>
                          <br />
                          <Button 
                            type="link" 
                            onClick={() => setActiveTab(category.name)}
                          >
                            配置管理
                          </Button>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </div>
              )
            },
            ...categories.map(category => ({
              key: category.name,
              label: category.display_name,
              children: <ConfigForm category={category} />
            }))
          ]}
        />
      </Spin>
    </div>
  )
}

export default ConfigManagement
