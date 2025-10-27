import React, { useState, useEffect } from 'react';
import {
  Card,
  Tabs,
  Form,
  Input,
  Button,
  Select,
  Switch,
  Table,
  Tag,
  Space,
  Modal,
  message,
  Row,
  Col,
  Statistic,
  Progress,
  Alert,
  Divider,
  notification
} from 'antd';
import {
  SettingOutlined,
  MonitorOutlined,
  BarChartOutlined,
  WechatOutlined,
  ApiOutlined,
  DatabaseOutlined,
  RobotOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { ErrorBoundary, initializeMonitoring } from '../utils/monitoring';

const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;

// API客户端
class ApiClient {
  private baseUrl: string = 'http://localhost:8002';
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('auth_token');
  }

  private async request(endpoint: string, options: RequestInit = {}): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API请求失败:', error);
      throw error;
    }
  }

  async login(username: string, password: string): Promise<string> {
    const response = await this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });

    this.token = response.access_token;
    localStorage.setItem('auth_token', this.token);
    return this.token;
  }

  async getConfig(): Promise<any> {
    return this.request('/api/config');
  }

  async updateConfig(config: any): Promise<any> {
    return this.request('/api/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getStatus(): Promise<any> {
    return this.request('/api/status');
  }

  async getRecentMessages(limit: number = 50): Promise<any[]> {
    return this.request(`/api/messages/recent?limit=${limit}`);
  }

  async getLogs(limit: number = 100): Promise<any[]> {
    return this.request(`/api/logs?limit=${limit}`);
  }

  async getStatistics(): Promise<any> {
    return this.request('/api/statistics');
  }
}

// 创建API客户端实例
const apiClient = new ApiClient();

// 配置管理组件
const ConfigManagement = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [configs, setConfigs] = useState({});

  // 加载配置
  const loadConfigs = async () => {
    try {
      const data = await apiClient.getConfig();
      setConfigs(data);
      form.setFieldsValue(data);
    } catch (error) {
      message.error('加载配置失败');
      console.error('加载配置失败:', error);
    }
  };

  // 保存配置
  const saveConfigs = async (values: any) => {
    setLoading(true);
    try {
      await apiClient.updateConfig(values);
      message.success('配置保存成功');
      await loadConfigs();
    } catch (error) {
      message.error('配置保存失败');
      console.error('配置保存失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfigs();
  }, []);

  return (
    <Card title={<><SettingOutlined /> 系统配置</>}>
      <Form
        form={form}
        layout="vertical"
        onFinish={saveConfigs}
        initialValues={{
          enable_humanize: true,
          auto_reply: true,
          log_level: 'INFO'
        }}
      >
        <Row gutter={24}>
          <Col span={12}>
            <Card size="small" title="微信配置">
              <Form.Item
                name="whitelist_groups"
                label="白名单群聊"
                tooltip="每行一个群名，只有这些群的消息会被处理"
              >
                <TextArea
                  rows={6}
                  placeholder="客服群&#10;技术支持群&#10;VIP客户群"
                />
              </Form.Item>

              <Form.Item
                name="enable_humanize"
                label="启用拟人化行为"
                valuePropName="checked"
                tooltip="模拟真人打字速度和语气"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="reply_delay_min"
                label="回复延迟范围（秒）"
              >
                <Input.Group compact>
                  <Form.Item name="reply_delay_min" noStyle>
                    <Input placeholder="最小" style={{ width: '50%' }} />
                  </Form.Item>
                  <Form.Item name="reply_delay_max" noStyle>
                    <Input placeholder="最大" style={{ width: '50%' }} />
                  </Form.Item>
                </Input.Group>
              </Form.Item>
            </Card>
          </Col>

          <Col span={12}>
            <Card size="small" title="AI配置">
              <Form.Item
                name="ai_model"
                label="AI模型"
                tooltip="选择用于智能回复的AI模型"
              >
                <Select>
                  <Option value="qwen">通义千问</Option>
                  <Option value="glm">智谱GLM</Option>
                  <Option value="openai">OpenAI GPT</Option>
                  <Option value="claude">Claude</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="ai_api_key"
                label="API密钥"
                tooltip="对应AI模型的API密钥"
              >
                <Input.Password placeholder="请输入API密钥" />
              </Form.Item>

              <Form.Item
                name="ai_temperature"
                label="创造性程度"
                tooltip="0-1之间，越高越有创造性"
              >
                <Input type="number" min={0} max={1} step={0.1} />
              </Form.Item>

              <Form.Item
                name="max_tokens"
                label="最大回复长度"
              >
                <Input type="number" placeholder="500" />
              </Form.Item>
            </Card>
          </Col>
        </Row>

        <Row gutter={24} style={{ marginTop: 16 }}>
          <Col span={12}>
            <Card size="small" title="服务器配置">
              <Form.Item
                name="server_url"
                label="后端服务器地址"
                tooltip="本地代理连接的后端服务器"
              >
                <Input placeholder="http://localhost:8000" />
              </Form.Item>

              <Form.Item
                name="api_key"
                label="服务器API密钥"
              >
                <Input.Password placeholder="服务器认证密钥" />
              </Form.Item>

              <Form.Item
                name="heartbeat_interval"
                label="心跳间隔（秒）"
              >
                <Input type="number" placeholder="30" />
              </Form.Item>
            </Card>
          </Col>

          <Col span={12}>
            <Card size="small" title="高级配置">
              <Form.Item
                name="log_level"
                label="日志级别"
              >
                <Select>
                  <Option value="DEBUG">DEBUG</Option>
                  <Option value="INFO">INFO</Option>
                  <Option value="WARNING">WARNING</Option>
                  <Option value="ERROR">ERROR</Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="auto_start"
                label="开机自启动"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="minimize_to_tray"
                label="最小化到系统托盘"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="cache_size"
                label="本地缓存大小（MB）"
              >
                <Input type="number" placeholder="100" />
              </Form.Item>
            </Card>
          </Col>
        </Row>

        <Divider />

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>
              保存配置
            </Button>
            <Button onClick={loadConfigs}>
              重新加载
            </Button>
            <Button danger onClick={() => form.resetFields()}>
              重置
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

// 监控面板组件
const MonitorPanel = () => {
  const [status, setStatus] = useState({
    service_running: false,
    wechat_connected: false,
    server_connected: false,
    message_count: 0,
    error_count: 0,
    uptime: '00:00:00'
  });

  const [recentMessages, setRecentMessages] = useState([]);
  const [logs, setLogs] = useState([]);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  // 实时状态更新
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const data = await apiClient.getStatus();
        setStatus(data);
        setConnectionError(null);
      } catch (error) {
        console.error('获取状态失败:', error);
        setConnectionError('无法连接到服务器');
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // 获取最近消息
  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const data = await apiClient.getRecentMessages();
        setRecentMessages(data);
      } catch (error) {
        console.error('获取消息失败:', error);
      }
    };

    fetchMessages();
    const interval = setInterval(fetchMessages, 5000);
    return () => clearInterval(interval);
  }, []);

  // 获取日志
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const data = await apiClient.getLogs();
        setLogs(data);
      } catch (error) {
        console.error('获取日志失败:', error);
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 10000);
    return () => clearInterval(interval);
  }, []);

  const messageColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 120,
      render: (timestamp: string) => new Date(timestamp).toLocaleTimeString()
    },
    {
      title: '群聊',
      dataIndex: 'group_name',
      key: 'group_name',
      width: 150
    },
    {
      title: '发送者',
      dataIndex: 'sender_name',
      key: 'sender_name',
      width: 120
    },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => (
        <Tag color={status === 'processed' ? 'green' : 'orange'}>
          {status === 'processed' ? '已处理' : '处理中'}
        </Tag>
      )
    }
  ];

  const logColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 120,
      render: (timestamp: string) => new Date(timestamp).toLocaleTimeString()
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level: string) => {
        const colors = {
          DEBUG: 'blue',
          INFO: 'green',
          WARNING: 'orange',
          ERROR: 'red'
        };
        return <Tag color={colors[level as keyof typeof colors]}>{level}</Tag>;
      }
    },
    {
      title: '组件',
      dataIndex: 'component',
      key: 'component',
      width: 120
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true
    }
  ];

  return (
    <Card title={<><MonitorOutlined /> 实时监控</>}>
      {connectionError && (
        <Alert
          message="连接错误"
          description={connectionError}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Row gutter={24}>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="服务状态"
              value={status.service_running ? '运行中' : '已停止'}
              valueStyle={{ color: status.service_running ? '#3f8600' : '#cf1322' }}
              prefix={<WechatOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="微信连接"
              value={status.wechat_connected ? '已连接' : '未连接'}
              valueStyle={{ color: status.wechat_connected ? '#3f8600' : '#cf1322' }}
              prefix={<ApiOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="今日消息"
              value={status.message_count}
              prefix={<RobotOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="运行时间"
              value={status.uptime}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={24} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card size="small" title="最近消息">
            <Table
              dataSource={recentMessages}
              columns={messageColumns}
              pagination={false}
              size="small"
              scroll={{ y: 300 }}
              rowKey="id"
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card size="small" title="系统日志">
            <Table
              dataSource={logs}
              columns={logColumns}
              pagination={false}
              size="small"
              scroll={{ y: 300 }}
              rowKey="timestamp"
            />
          </Card>
        </Col>
      </Row>

      {status.error_count > 0 && (
        <Alert
          message={`检测到 ${status.error_count} 个错误`}
          description="请检查系统日志或联系技术支持"
          type="error"
          showIcon
          style={{ marginTop: 16 }}
        />
      )}
    </Card>
  );
};

// 统计分析组件
const StatisticsPanel = () => {
  const [stats, setStats] = useState({
    total_messages: 0,
    processed_messages: 0,
    error_rate: 0,
    avg_response_time: 0,
    top_groups: [],
    hourly_stats: []
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await apiClient.getStatistics();
        setStats(data);
      } catch (error) {
        console.error('获取统计失败:', error);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const groupColumns = [
    {
      title: '群聊名称',
      dataIndex: 'group_name',
      key: 'group_name'
    },
    {
      title: '消息数量',
      dataIndex: 'message_count',
      key: 'message_count',
      sorter: (a: any, b: any) => a.message_count - b.message_count
    },
    {
      title: '处理率',
      dataIndex: 'process_rate',
      key: 'process_rate',
      render: (rate: number) => (
        <Progress percent={rate} size="small" />
      )
    }
  ];

  return (
    <Card title={<><BarChartOutlined /> 统计分析</>}>
      <Row gutter={24}>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="总消息数"
              value={stats.total_messages}
              prefix={<WechatOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="处理率"
              value={stats.processed_messages / Math.max(stats.total_messages, 1) * 100}
              precision={1}
              suffix="%"
              prefix={<RobotOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="错误率"
              value={stats.error_rate}
              precision={2}
              suffix="%"
              valueStyle={{ color: stats.error_rate > 5 ? '#cf1322' : '#3f8600' }}
              prefix={<ExclamationCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="平均响应时间"
              value={stats.avg_response_time}
              precision={1}
              suffix="秒"
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={24} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card size="small" title="群聊活跃度排行">
            <Table
              dataSource={stats.top_groups}
              columns={groupColumns}
              pagination={false}
              size="small"
              rowKey="group_name"
            />
          </Card>
        </Col>
      </Row>
    </Card>
  );
};

// 登录组件
const LoginForm = ({ onLogin }: { onLogin: (token: string) => void }) => {
  const [loading, setLoading] = useState(false);

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const token = await apiClient.login(values.username, values.password);
      onLogin(token);
      message.success('登录成功');
    } catch (error) {
      message.error('登录失败，请检查用户名和密码');
      console.error('登录失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="登录" style={{ width: 400, margin: '100px auto' }}>
      <Form onFinish={handleLogin}>
        <Form.Item
          name="username"
          rules={[{ required: true, message: '请输入用户名' }]}
        >
          <Input placeholder="用户名" />
        </Form.Item>
        <Form.Item
          name="password"
          rules={[{ required: true, message: '请输入密码' }]}
        >
          <Input.Password placeholder="密码" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>
            登录
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

// 主组件
const ClientManagement = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    // 检查是否已登录
    const savedToken = localStorage.getItem('auth_token');
    if (savedToken) {
      setToken(savedToken);
      setIsLoggedIn(true);
    }

    // 初始化监控系统
    initializeMonitoring();
  }, []);

  const handleLogin = (newToken: string) => {
    setToken(newToken);
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    setToken(null);
    setIsLoggedIn(false);
  };

  if (!isLoggedIn) {
    return <LoginForm onLogin={handleLogin} />;
  }

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16, textAlign: 'right' }}>
        <Button onClick={handleLogout}>
          退出登录
        </Button>
      </div>
      
      <Tabs defaultActiveKey="config" size="large">
        <TabPane tab={<><SettingOutlined /> 配置管理</>} key="config">
          <ConfigManagement />
        </TabPane>
        <TabPane tab={<><MonitorOutlined /> 实时监控</>} key="monitor">
          <MonitorPanel />
        </TabPane>
        <TabPane tab={<><BarChartOutlined /> 统计分析</>} key="statistics">
          <StatisticsPanel />
        </TabPane>
      </Tabs>
    </div>
  );
};

// 导出带错误边界的组件
const ClientManagementWithErrorBoundary = () => (
  <ErrorBoundary>
    <ClientManagement />
  </ErrorBoundary>
);

export default ClientManagementWithErrorBoundary;
