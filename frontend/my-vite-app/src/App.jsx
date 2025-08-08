import React from 'react';
import { BrowserRouter, Routes, Route, Link, useNavigate, useParams } from 'react-router-dom';
const API_BASE = '/api';

function apiFetch(path, options = {}) {
  const token = localStorage.getItem('token');
  const headers = Object.assign({ 'Content-Type': 'application/json' }, options.headers || {});
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return fetch(`${API_BASE}${path}`, { ...options, headers });
}

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

function MyApplicationsList() {
  const [items, setItems] = React.useState([]);
  React.useEffect(() => {
    apiFetch('/approvals?scope=applicant').then(async res => {
      if (res.ok) setItems(await res.json());
    });
  }, []);
  return (
    <div>
      <h2>我的申请</h2>
      <ul>
        {items.map(item => (
          <li key={item.id}>
            {item.code} - {item.status} <Link to={`/approvals/${item.id}`}>详情</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function MyApprovalsList() {
  const [items, setItems] = React.useState([]);
  React.useEffect(() => {
    apiFetch('/approvals?scope=actor').then(async res => {
      if (res.ok) setItems(await res.json());
    });
  }, []);
  return (
    <div>
      <h2>我的审批</h2>
      <ul>
        {items.map(item => (
          <li key={item.id}>
            {item.code} - {item.status} <Link to={`/approvals/${item.id}`}>详情</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function NewApproval() {
  const [title, setTitle] = React.useState('');
  const [content, setContent] = React.useState('');
  const [remark, setRemark] = React.useState('');
  const [attachments, setAttachments] = React.useState([]);
  const [templateId, setTemplateId] = React.useState('');
  const navigate = useNavigate();
  function handleFiles(e) {
    setAttachments(Array.from(e.target.files).map(f => f.name));
  }
  async function submit(e) {
    e.preventDefault();
    const data = { title, content, remark, attachments };
    const res = await apiFetch('/approvals', {
      method: 'POST',
      body: JSON.stringify({ data, template_id: parseInt(templateId) })
    });
    if (res.ok) navigate('/approvals');
  }
  return (
    <div>
      <h2>发起审批</h2>
      <form onSubmit={submit}>
        <input placeholder="标题" value={title} onChange={e => setTitle(e.target.value)} />
        <textarea placeholder="内容" value={content} onChange={e => setContent(e.target.value)} />
        <textarea placeholder="备注" value={remark} onChange={e => setRemark(e.target.value)} />
        <input type="file" multiple onChange={handleFiles} />
        <input placeholder="模板ID" value={templateId} onChange={e => setTemplateId(e.target.value)} />
        <button type="submit">保存</button>
      </form>
    </div>
  );
}

function EditApproval() {
  const { id } = useParams();
  const [title, setTitle] = React.useState('');
  const [content, setContent] = React.useState('');
  const [remark, setRemark] = React.useState('');
  const [attachments, setAttachments] = React.useState([]);
  const navigate = useNavigate();
  React.useEffect(() => {
    apiFetch(`/approvals/${id}`).then(async res => {
      if (res.ok) {
        const item = await res.json();
        setTitle(item.data.title || '');
        setContent(item.data.content || '');
        setRemark(item.data.remark || '');
        setAttachments(item.data.attachments || []);
      }
    });
  }, [id]);
  function handleFiles(e) {
    setAttachments(Array.from(e.target.files).map(f => f.name));
  }
  async function submit(e) {
    e.preventDefault();
    const data = { title, content, remark, attachments };
    const res = await apiFetch(`/approvals/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ data })
    });
    if (res.ok) navigate(`/approvals/${id}`);
  }
  return (
    <div>
      <h2>编辑审批</h2>
      <form onSubmit={submit}>
        <input placeholder="标题" value={title} onChange={e => setTitle(e.target.value)} />
        <textarea placeholder="内容" value={content} onChange={e => setContent(e.target.value)} />
        <textarea placeholder="备注" value={remark} onChange={e => setRemark(e.target.value)} />
        <input type="file" multiple onChange={handleFiles} />
        <button type="submit">保存</button>
      </form>
    </div>
  );
}

function ApprovalDetail() {
  const { id } = useParams();
  const [item, setItem] = React.useState(null);
  const [comments, setComments] = React.useState('');
  const [files, setFiles] = React.useState([]);
  const navigate = useNavigate();
  const user = currentUser();
  React.useEffect(() => {
    apiFetch(`/approvals/${id}`).then(async res => {
      if (res.ok) setItem(await res.json());
    });
  }, [id]);
  function handleFiles(e) {
    setFiles(Array.from(e.target.files).map(f => f.name));
  }
  async function action(path) {
    const res = await apiFetch(`/approvals/${id}/${path}`, {
      method: 'POST',
      body: JSON.stringify({ comments, attachments: files })
    });
    if (res.ok) setItem(await res.json());
  }
  async function resubmit() {
    const res = await apiFetch(`/approvals/${id}/submit`, { method: 'POST' });
    if (res.ok) setItem(await res.json());
  }
  if (!item) return <div>加载中...</div>;
  const canEdit = user && user.id === item.applicant_id && (item.status === 'draft' || item.status === 'rejected');
  return (
    <div>
      <h2>审批详情</h2>
      <div>编号: {item.code}</div>
      <div>状态: {item.status}</div>
      <div>标题: {item.data.title}</div>
      <div>内容: {item.data.content}</div>
      <div>备注: {item.data.remark}</div>
      {item.data.attachments && item.data.attachments.length > 0 && (
        <ul>
          {item.data.attachments.map((a, i) => (
            <li key={i}>{a}</li>
          ))}
        </ul>
      )}
      {item.workflow && (
        <ul>
          {item.workflow.flow.map(n => (
            <li key={n.id}>{n.id} - {n.status}</li>
          ))}
        </ul>
      )}
      <textarea placeholder="审批备注" value={comments} onChange={e => setComments(e.target.value)} />
      <input type="file" multiple onChange={handleFiles} />
      <button onClick={() => action('approve')}>通过</button>
      <button onClick={() => action('reject')}>驳回</button>
      {canEdit && <button onClick={() => navigate(`/approvals/${id}/edit`)}>编辑</button>}
      {canEdit && <button onClick={resubmit}>重新提交</button>}
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
        <Link to="/approvals">我的申请</Link> |
        <Link to="/tasks">我的审批</Link> |
        <Link to="/new">发起审批</Link> |
        <Link to="/scan">核查扫码</Link> |
        <Link to="/stats">统计查看</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/approvals" element={<MyApplicationsList />} />
        <Route path="/tasks" element={<MyApprovalsList />} />
        <Route path="/new" element={<NewApproval />} />
        <Route path="/approvals/:id" element={<ApprovalDetail />} />
        <Route path="/approvals/:id/edit" element={<EditApproval />} />
        <Route path="/scan" element={<VerificationScan />} />
        <Route path="/stats" element={<StatisticsView />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
