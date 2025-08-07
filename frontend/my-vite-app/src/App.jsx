import React from 'react';
import { BrowserRouter, Routes, Route, Link, useNavigate, useParams } from 'react-router-dom';
const API_BASE = '/api';

function apiFetch(path, options = {}) {
  const token = localStorage.getItem('token');
  const headers = Object.assign({ 'Content-Type': 'application/json' }, options.headers || {});
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetch(`${API_BASE}${path}`, { ...options, headers });
}

function Login() {
  const [username, setUsername] = React.useState('');
  const [password, setPassword] = React.useState('');
  const navigate = useNavigate();
  async function submit(e) {
    e.preventDefault();
    const res = await apiFetch('/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('token', data.token);
      navigate('/approvals');
    }
  }
  return (
    <div>
      <h2>登录</h2>
      <form onSubmit={submit}>
        <input placeholder="用户名" value={username} onChange={e => setUsername(e.target.value)} />
        <input placeholder="密码" type="password" value={password} onChange={e => setPassword(e.target.value)} />
        <button type="submit">登录</button>
      </form>
    </div>
  );
}

function ApprovalList() {
  const [items, setItems] = React.useState([]);
  React.useEffect(() => {
    apiFetch('/approvals').then(async res => {
      if (res.ok) setItems(await res.json());
    });
  }, []);
  return (
    <div>
      <h2>审批单列表</h2>
      <Link to="/new">发起审批</Link>
      <ul>
        {items.map(item => (
          <li key={item.id}>
            {item.title} - {item.status} <Link to={`/process/${item.id}`}>处理</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function NewApproval() {
  const [title, setTitle] = React.useState('');
  const [content, setContent] = React.useState('');
  const [templateId, setTemplateId] = React.useState('');
  const navigate = useNavigate();
  async function submit(e) {
    e.preventDefault();
    const res = await apiFetch('/approvals', {
      method: 'POST',
      body: JSON.stringify({ title, content, template_id: parseInt(templateId) })
    });
    if (res.ok) navigate('/approvals');
  }
  return (
    <div>
      <h2>发起审批</h2>
      <form onSubmit={submit}>
        <input placeholder="标题" value={title} onChange={e => setTitle(e.target.value)} />
        <textarea placeholder="内容" value={content} onChange={e => setContent(e.target.value)} />
        <input placeholder="模板ID" value={templateId} onChange={e => setTemplateId(e.target.value)} />
        <button type="submit">提交</button>
      </form>
    </div>
  );
}

function ApprovalProcess() {
  const { id } = useParams();
  const [item, setItem] = React.useState(null);
  const [comments, setComments] = React.useState('');
  const [attachments, setAttachments] = React.useState('');
  React.useEffect(() => {
    apiFetch(`/approvals/${id}`).then(async res => {
      if (res.ok) setItem(await res.json());
    });
  }, [id]);
  async function action(path) {
    const res = await apiFetch(`/approvals/${id}/${path}`, {
      method: 'POST',
      body: JSON.stringify({ comments, attachments: attachments.split(',').map(s=>s.trim()).filter(Boolean) })
    });
    if (res.ok) setItem(await res.json());
  }
  if (!item) return <div>加载中...</div>;
  return (
    <div>
      <h2>审批处理</h2>
      <div>{item.title}</div>
      <div>{item.content}</div>
      {item.workflow && (
        <ul>
          {item.workflow.flow.map(n => (
            <li key={n.id}>{n.id} - {n.status}</li>
          ))}
        </ul>
      )}
      <textarea placeholder="备注" value={comments} onChange={e=>setComments(e.target.value)} />
      <input placeholder="附件,以逗号分隔" value={attachments} onChange={e=>setAttachments(e.target.value)} />
      <button onClick={() => action('approve')}>通过</button>
      <button onClick={() => action('reject')}>拒绝</button>
    </div>
  );
}

function VerificationScan() {
  const [code, setCode] = React.useState('');
  const [result, setResult] = React.useState(null);
  async function verify() {
    const res = await apiFetch(`/verify/${code}`);
    if (res.ok) setResult(await res.json());
  }
  return (
    <div>
      <h2>核查扫码</h2>
      <input placeholder="二维码" value={code} onChange={e => setCode(e.target.value)} />
      <button onClick={verify}>核查</button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}

function StatisticsView() {
  const [stats, setStats] = React.useState(null);
  React.useEffect(() => {
    apiFetch('/statistics').then(async res => {
      if (res.ok) setStats(await res.json());
    });
  }, []);
  return (
    <div>
      <h2>统计查看</h2>
      {stats ? <pre>{JSON.stringify(stats, null, 2)}</pre> : '加载中...'}
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/">登录</Link> |
        <Link to="/approvals">审批单列表</Link> |
        <Link to="/new">发起审批</Link> |
        <Link to="/scan">核查扫码</Link> |
        <Link to="/stats">统计查看</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/approvals" element={<ApprovalList />} />
        <Route path="/new" element={<NewApproval />} />
        <Route path="/process/:id" element={<ApprovalProcess />} />
        <Route path="/scan" element={<VerificationScan />} />
        <Route path="/stats" element={<StatisticsView />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App
