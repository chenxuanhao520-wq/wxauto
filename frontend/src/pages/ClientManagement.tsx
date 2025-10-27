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
  Divider
} from 'antd';
import {
  SettingOutlined,
  MonitorOutlined,
  BarChartOutlined,
  WechatOutlined,
  ApiOutlined,
  DatabaseOutlined,
  RobotOutlined
} from '@ant-design/icons';

const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;

// 配置管理组件
const ConfigManagement = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [configs, setConfigs] = useState({});

  // 加载配置
  const loadConfigs = async () => {
    try {
      const response = await fetch('/api/config');
      const data = await response.json();
      setConfigs(data);
      form.setFieldsValue(data);
    } catch (error) {
      message.error('加载配置失败');
    }
  };

  // 保存配置
  const saveConfigs = async (values) => {
    setLoading(true);
    try {
      const response = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values)
      });
      
      if (response.ok) {
        message.success('配置保存成功');
        await loadConfigs();
      } else {
        message.error('配置保存失败');
      }
    } catch (error) {
      message.error('配置保存失败');
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

  // 实时状态更新
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch('/api/status');
        const data = await response.json();
        setStatus(data);
      } catch (error) {
        console.error('获取状态失败:', error);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // 获取最近消息
  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const response = await fetch('/api/messages/recent');
        const data = await response.json();
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
        const response = await fetch('/api/logs');
        const data = await response.json();
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
      width: 120
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
      render: (status) => (
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
      width: 120
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level) => {
        const colors = {
          DEBUG: 'blue',
          INFO: 'green',
          WARNING: 'orange',
          ERROR: 'red'
        };
        return <Tag color={colors[level]}>{level}</Tag>;
      }
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
        const response = await fetch('/api/statistics');
        const data = await response.json();
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
      sorter: (a, b) => a.message_count - b.message_count
    },
    {
      title: '处理率',
      dataIndex: 'process_rate',
      key: 'process_rate',
      render: (rate) => (
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
              value={stats.processed_messages / stats.total_messages * 100}
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
              prefix={<ApiOutlined />}
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
            />
          </Card>
        </Col>
      </Row>
    </Card>
  );
};

// 主组件
const ClientManagement = () => {
  return (
    <div style={{ padding: 24 }}>
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

export default ClientManagement;
