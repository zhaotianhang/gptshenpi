# 财务审批系统

一个现代化的财务审批小程序，支持审批流程管理、二维码核查、统计分析等功能。

## 功能特性

### 核心功能
- **用户管理**: 支持管理员和普通用户角色
- **组织架构**: 组织、部门管理
- **审批流程**: 可配置的审批流程模板
- **审批管理**: 申请创建、提交、审批、驳回
- **二维码核查**: 支持二维码扫描验证
- **统计分析**: 多维度数据统计和导出
- **通知推送**: 审批状态变更通知

### 审批流程
- 支持多级审批流程
- 可配置审批人员和代审人员
- 支持审批和推送两种操作类型
- 流程可拆分为不同环节

### 审批单管理
- 包含审批单号及二维码
- 支持财务报销信息（条目、总金额、备注）
- 绑定发起人员、组织、部门信息
- 支持草稿状态和重新提交

### 核查功能
- 相机扫描二维码自动匹配审批单
- 核查记录管理
- 支持核查人员权限控制

### 统计功能
- 按时间、人员、组织、部门、审核状态统计
- 支持金额统计和列表查看
- 数据导出功能（CSV、Excel）

## 技术栈

### 后端
- **Flask**: Web框架
- **PyJWT**: JWT认证
- **qrcode**: 二维码生成
- **openpyxl**: Excel导出

### 前端
- **React**: 前端框架
- **Ant Design**: UI组件库
- **React Router**: 路由管理
- **Axios**: HTTP客户端

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- npm 8+

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd gptshenpi
```

2. **安装后端依赖**
```bash
pip install -r requirements.txt
```

3. **安装前端依赖**
```bash
cd frontend/my-vite-app
npm install
cd ../..
```

4. **启动服务**

方式一：使用启动脚本（推荐）
```bash
python run.py
```

方式二：分别启动
```bash
# 启动后端服务
python app.py

# 启动前端服务（新终端）
cd frontend/my-vite-app
npm run dev
```

5. **访问系统**
- 前端应用: http://localhost:5173
- 后端API: http://localhost:3000
- 管理后台: http://localhost:3000/admin

### 默认账户
- 管理员: admin / admin
- 普通用户: user / user

## 项目结构

```
gptshenpi/
├── app.py                 # 主应用文件
├── run.py                 # 启动脚本
├── requirements.txt       # Python依赖
├── storage.py            # 数据存储
├── controllers/          # 控制器
│   ├── approval.py       # 审批控制器
│   ├── verification.py   # 核查控制器
│   └── statistics.py     # 统计控制器
├── models/               # 数据模型
│   ├── user.py          # 用户模型
│   ├── approval_form.py # 审批单模型
│   └── ...
├── middleware/           # 中间件
│   └── auth.py          # 认证中间件
├── frontend/            # 前端应用
│   └── my-vite-app/
│       ├── src/
│       │   └── App.jsx  # 主应用组件
│       └── package.json
├── static/              # 静态文件
│   └── admin.html       # 管理后台
└── qr_codes/           # 二维码存储
```

## API文档

### 认证相关
- `POST /login` - 用户登录
- `GET /users/<id>` - 获取用户信息

### 审批相关
- `GET /approvals` - 获取审批列表
- `POST /approvals` - 创建审批单
- `GET /approvals/<id>` - 获取审批详情
- `PUT /approvals/<id>` - 更新审批单
- `POST /approvals/<id>/submit` - 提交审批
- `POST /approvals/<id>/approve` - 审批通过
- `POST /approvals/<id>/reject` - 审批驳回

### 核查相关
- `GET /verify/<code>` - 通过二维码验证
- `POST /verification/<code>` - 提交核查结果

### 统计相关
- `GET /statistics/dashboard` - 仪表板统计
- `GET /statistics/approvals` - 审批统计
- `GET /statistics/verification` - 核查统计

### 管理相关
- `GET /admin/users` - 用户管理
- `GET /admin/orgs` - 组织管理
- `GET /admin/depts` - 部门管理
- `GET /admin/templates` - 模板管理
- `GET /admin/verifiers` - 核查人员管理

## 开发指南

### 添加新功能
1. 在 `models/` 目录下添加数据模型
2. 在 `controllers/` 目录下添加控制器
3. 在 `app.py` 中注册路由
4. 在前端添加对应的页面和组件

### 数据库
项目使用JSON文件存储数据，数据文件为 `data.json`。

### 部署
1. 配置生产环境变量
2. 使用 gunicorn 部署后端
3. 构建前端静态文件
4. 配置反向代理

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
