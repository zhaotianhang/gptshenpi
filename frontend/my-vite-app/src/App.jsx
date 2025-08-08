import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useNavigate, useParams } from 'react-router-dom';
import { 
  Layout, Menu, Button, Form, Input, Card, Table, Tag, Modal, 
  message, Tabs, Space, Descriptions, Upload, Select, DatePicker,
  Statistic, Row, Col, Divider, Typography, Avatar, Badge, Tooltip,
  Popconfirm, Drawer, List, Timeline, Steps, Progress
} from 'antd';
import {
  UserOutlined, FileTextOutlined, CheckCircleOutlined, 
  CloseCircleOutlined, PlusOutlined, SearchOutlined,
  QrcodeOutlined, BarChartOutlined, SettingOutlined,
  LogoutOutlined, HomeOutlined, TeamOutlined, AuditOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Step } = Steps;

const API_BASE = '/api';

// 配置axios
axios.defaults.baseURL = API_BASE;
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function currentUser() {
  const token = localStorage.getItem('token');
  if (!token) return null;
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch (e) {
    return null;
  }
}

function Login() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const response = await axios.post('/login', values);
      localStorage.setItem('token', response.data.token);
      message.success('登录成功');
      navigate('/dashboard');
    } catch (error) {
      message.error('登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      height: '100vh', 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card style={{ width: 400, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={2}>财务审批系统</Title>
          <Text type="secondary">请登录您的账户</Text>
        </div>
        <Form
          name="login"
          onFinish={onFinish}
          layout="vertical"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名!' }]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="用户名" 
              size="large"
            />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码!' }]}
          >
            <Input.Password 
              prefix={<UserOutlined />} 
              placeholder="密码" 
              size="large"
            />
          </Form.Item>
          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
              size="large"
              block
            >
              登录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}

function Dashboard() {
  const [stats, setStats] = useState({});
  const user = currentUser();

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await axios.get('/statistics/dashboard');
      setStats(response.data);
    } catch (error) {
      console.error('加载统计数据失败:', error);
    }
  };

  return (
    <div>
      <Title level={2}>仪表板</Title>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="待审批"
              value={stats.pending || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已审批"
              value={stats.approved || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已驳回"
              value={stats.rejected || 0}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="总金额"
              value={stats.totalAmount || 0}
              prefix="¥"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}

function MyApplicationsList() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });

  useEffect(() => {
    loadApplications();
  }, [pagination.current]);

  const loadApplications = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`/approvals?scope=applicant&page=${pagination.current}&size=${pagination.pageSize}`);
      setApplications(response.data.items || []);
      setPagination(prev => ({
        ...prev,
        total: response.data.total || 0
      }));
    } catch (error) {
      message.error('加载申请列表失败');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: '申请编号',
      dataIndex: 'code',
      key: 'code',
    },
    {
      title: '标题',
      dataIndex: ['data', 'title'],
      key: 'title',
    },
    {
      title: '金额',
      dataIndex: ['data', 'totalAmount'],
      key: 'amount',
      render: (amount) => `¥${amount || 0}`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const statusMap = {
          'draft': { color: 'default', text: '草稿' },
          'pending': { color: 'processing', text: '审批中' },
          'approved': { color: 'success', text: '已通过' },
          'rejected': { color: 'error', text: '已驳回' },
          'cancelled': { color: 'default', text: '已取消' }
        };
        const config = statusMap[status] || { color: 'default', text: status };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Link to={`/approvals/${record.id}`}>查看详情</Link>
          {(record.status === 'draft' || record.status === 'rejected') && (
            <Link to={`/approvals/${record.id}/edit`}>编辑</Link>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3}>我的申请</Title>
        <Link to="/new-approval">
          <Button type="primary" icon={<PlusOutlined />}>
            发起申请
          </Button>
        </Link>
      </div>
      <Table
        columns={columns}
        dataSource={applications}
        loading={loading}
        pagination={pagination}
        onChange={(pagination) => setPagination(pagination)}
        rowKey="id"
      />
    </div>
  );
}

function MyApprovalsList() {
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadApprovals();
  }, []);

  const loadApprovals = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/approvals?scope=actor');
      setApprovals(response.data || []);
    } catch (error) {
      message.error('加载审批列表失败');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: '申请编号',
      dataIndex: 'code',
      key: 'code',
    },
    {
      title: '申请人',
      dataIndex: ['applicant', 'username'],
      key: 'applicant',
    },
    {
      title: '标题',
      dataIndex: ['data', 'title'],
      key: 'title',
    },
    {
      title: '金额',
      dataIndex: ['data', 'totalAmount'],
      key: 'amount',
      render: (amount) => `¥${amount || 0}`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const statusMap = {
          'pending': { color: 'processing', text: '待审批' },
          'approved': { color: 'success', text: '已通过' },
          'rejected': { color: 'error', text: '已驳回' }
        };
        const config = statusMap[status] || { color: 'default', text: status };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Link to={`/approvals/${record.id}`}>查看详情</Link>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={3}>我的审批</Title>
      <Table
        columns={columns}
        dataSource={approvals}
        loading={loading}
        rowKey="id"
      />
    </div>
  );
}

function NewApproval() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [templates, setTemplates] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await axios.get('/admin/templates');
      setTemplates(response.data || []);
    } catch (error) {
      console.error('加载模板失败:', error);
    }
  };

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const formData = {
        template_id: values.template_id,
        data: {
          title: values.title,
          content: values.content,
          remark: values.remark,
          totalAmount: values.totalAmount,
          items: values.items || []
        }
      };
      
      await axios.post('/approvals', formData);
      message.success('申请创建成功');
      navigate('/applications');
    } catch (error) {
      message.error('创建申请失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={3}>发起申请</Title>
      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
        >
          <Form.Item
            name="template_id"
            label="审批模板"
            rules={[{ required: true, message: '请选择审批模板!' }]}
          >
            <Select placeholder="选择审批模板">
              {templates.map(template => (
                <Select.Option key={template.id} value={template.id}>
                  {template.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="title"
            label="申请标题"
            rules={[{ required: true, message: '请输入申请标题!' }]}
          >
            <Input placeholder="请输入申请标题" />
          </Form.Item>

          <Form.Item
            name="content"
            label="申请内容"
            rules={[{ required: true, message: '请输入申请内容!' }]}
          >
            <Input.TextArea rows={4} placeholder="请输入申请内容" />
          </Form.Item>

          <Form.Item
            name="totalAmount"
            label="总金额"
            rules={[{ required: true, message: '请输入总金额!' }]}
          >
            <Input type="number" placeholder="请输入总金额" />
          </Form.Item>

          <Form.Item
            name="remark"
            label="备注"
          >
            <Input.TextArea rows={2} placeholder="请输入备注信息" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading}>
                提交申请
              </Button>
              <Button onClick={() => navigate('/applications')}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}

function ApprovalDetail() {
  const { id } = useParams();
  const [approval, setApproval] = useState(null);
  const [loading, setLoading] = useState(false);
  const [comments, setComments] = useState('');
  const navigate = useNavigate();
  const user = currentUser();

  useEffect(() => {
    loadApproval();
  }, [id]);

  const loadApproval = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`/approvals/${id}`);
      setApproval(response.data);
    } catch (error) {
      message.error('加载申请详情失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (action) => {
    try {
      await axios.post(`/approvals/${id}/${action}`, { comments });
      message.success(`${action === 'approve' ? '审批通过' : '审批驳回'}成功`);
      loadApproval();
      setComments('');
    } catch (error) {
      message.error('操作失败');
    }
  };

  if (loading) {
    return <div>加载中...</div>;
  }

  if (!approval) {
    return <div>申请不存在</div>;
  }

  const canEdit = user && user.id === approval.applicant_id && 
    (approval.status === 'draft' || approval.status === 'rejected');

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3}>申请详情</Title>
        <Space>
          {canEdit && (
            <>
              <Link to={`/approvals/${id}/edit`}>
                <Button icon={<PlusOutlined />}>编辑</Button>
              </Link>
              <Button onClick={() => navigate(`/approvals/${id}/submit`)}>
                重新提交
              </Button>
            </>
          )}
        </Space>
      </div>

      <Row gutter={16}>
        <Col span={16}>
          <Card title="基本信息">
            <Descriptions column={2}>
              <Descriptions.Item label="申请编号">{approval.code}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={approval.status === 'approved' ? 'success' : 
                          approval.status === 'rejected' ? 'error' : 'processing'}>
                  {approval.status}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="申请人">{approval.applicant?.username}</Descriptions.Item>
              <Descriptions.Item label="申请时间">
                {new Date(approval.created_at).toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="总金额">¥{approval.data?.totalAmount || 0}</Descriptions.Item>
            </Descriptions>
          </Card>

          <Card title="申请内容" style={{ marginTop: 16 }}>
            <div>
              <h4>标题</h4>
              <p>{approval.data?.title}</p>
              <h4>内容</h4>
              <p>{approval.data?.content}</p>
              {approval.data?.remark && (
                <>
                  <h4>备注</h4>
                  <p>{approval.data.remark}</p>
                </>
              )}
            </div>
          </Card>
        </Col>

        <Col span={8}>
          <Card title="审批操作">
            <Form layout="vertical">
              <Form.Item label="审批意见">
                <Input.TextArea
                  rows={4}
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  placeholder="请输入审批意见"
                />
              </Form.Item>
              <Form.Item>
                <Space>
                  <Button 
                    type="primary" 
                    onClick={() => handleAction('approve')}
                    icon={<CheckCircleOutlined />}
                  >
                    通过
                  </Button>
                  <Button 
                    danger 
                    onClick={() => handleAction('reject')}
                    icon={<CloseCircleOutlined />}
                  >
                    驳回
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  );
}

function VerificationScan() {
  const [code, setCode] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleVerify = async () => {
    if (!code.trim()) {
      message.warning('请输入二维码');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.get(`/verify/${code}`);
      setResult(response.data);
      message.success('核查成功');
    } catch (error) {
      message.error('核查失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={3}>核查扫码</Title>
      <Card>
        <Form layout="vertical">
          <Form.Item label="二维码">
            <Input
              prefix={<QrcodeOutlined />}
              placeholder="请输入或扫描二维码"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              onPressEnter={handleVerify}
            />
          </Form.Item>
          <Form.Item>
            <Button 
              type="primary" 
              onClick={handleVerify} 
              loading={loading}
              icon={<SearchOutlined />}
            >
              核查
            </Button>
          </Form.Item>
        </Form>

        {result && (
          <Card title="核查结果" style={{ marginTop: 16 }}>
            <Descriptions column={1}>
              <Descriptions.Item label="申请编号">{result.code}</Descriptions.Item>
              <Descriptions.Item label="申请人">{result.applicant?.username}</Descriptions.Item>
              <Descriptions.Item label="状态">{result.status}</Descriptions.Item>
              <Descriptions.Item label="金额">¥{result.data?.totalAmount || 0}</Descriptions.Item>
            </Descriptions>
          </Card>
        )}
      </Card>
    </div>
  );
}

function StatisticsView() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/statistics');
      setStats(response.data);
    } catch (error) {
      message.error('加载统计数据失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={3}>统计查看</Title>
      {loading ? (
        <div>加载中...</div>
      ) : stats ? (
        <Row gutter={16}>
          <Col span={12}>
            <Card title="金额统计">
              <Statistic title="总金额" value={stats.totalAmount || 0} prefix="¥" />
              <Statistic title="平均金额" value={stats.averageAmount || 0} prefix="¥" />
            </Card>
          </Col>
          <Col span={12}>
            <Card title="数量统计">
              <Statistic title="总申请数" value={stats.totalCount || 0} />
              <Statistic title="待审批数" value={stats.pendingCount || 0} />
            </Card>
          </Col>
        </Row>
      ) : (
        <div>暂无数据</div>
      )}
    </div>
  );
}

function MainLayout({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  const user = currentUser();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  const menuItems = [
    {
      key: 'dashboard',
      icon: <HomeOutlined />,
      label: <Link to="/dashboard">仪表板</Link>,
    },
    {
      key: 'applications',
      icon: <FileTextOutlined />,
      label: <Link to="/applications">我的申请</Link>,
    },
    {
      key: 'approvals',
      icon: <CheckCircleOutlined />,
      label: <Link to="/approvals">我的审批</Link>,
    },
    {
      key: 'new-approval',
      icon: <PlusOutlined />,
      label: <Link to="/new-approval">发起申请</Link>,
    },
    {
      key: 'scan',
      icon: <QrcodeOutlined />,
      label: <Link to="/scan">核查扫码</Link>,
    },
    {
      key: 'statistics',
      icon: <BarChartOutlined />,
      label: <Link to="/statistics">统计查看</Link>,
    },
  ];

  if (!user) {
    return <Login />;
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div style={{ height: 32, margin: 16, background: 'rgba(255, 255, 255, 0.2)' }} />
        <Menu
          theme="dark"
          defaultSelectedKeys={['dashboard']}
          mode="inline"
          items={menuItems}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: '0 16px', background: '#fff', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0 }}>财务审批系统</Title>
          <Space>
            <Text>欢迎，{user.username}</Text>
            <Button icon={<LogoutOutlined />} onClick={handleLogout}>
              退出
            </Button>
          </Space>
        </Header>
        <Content style={{ margin: '16px' }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/dashboard" element={
          <MainLayout>
            <Dashboard />
          </MainLayout>
        } />
        <Route path="/applications" element={
          <MainLayout>
            <MyApplicationsList />
          </MainLayout>
        } />
        <Route path="/approvals" element={
          <MainLayout>
            <MyApprovalsList />
          </MainLayout>
        } />
        <Route path="/new-approval" element={
          <MainLayout>
            <NewApproval />
          </MainLayout>
        } />
        <Route path="/approvals/:id" element={
          <MainLayout>
            <ApprovalDetail />
          </MainLayout>
        } />
        <Route path="/approvals/:id/edit" element={
          <MainLayout>
            <NewApproval />
          </MainLayout>
        } />
        <Route path="/scan" element={
          <MainLayout>
            <VerificationScan />
          </MainLayout>
        } />
        <Route path="/statistics" element={
          <MainLayout>
            <StatisticsView />
          </MainLayout>
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
