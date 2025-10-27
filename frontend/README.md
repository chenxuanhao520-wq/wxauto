# 🎨 Wxauto 前端界面

基于React + TypeScript + Ant Design的现代化前端界面。

## ✨ 核心特性

- ⚛️ **React 18** - 最新的React特性
- 🔷 **TypeScript** - 类型安全的JavaScript
- 🎨 **Ant Design 5** - 企业级UI组件库
- ⚡ **Vite** - 快速的构建工具
- 🔄 **React Router** - 客户端路由
- 📦 **Zustand** - 轻量级状态管理
- 🌐 **Axios** - HTTP客户端

## 🚀 快速开始

### 1. 安装依赖
```bash
npm install
# 或
yarn install
```

### 2. 启动开发服务器
```bash
npm run dev
# 或
yarn dev
```

### 3. 构建生产版本
```bash
npm run build
# 或
yarn build
```

### 4. 预览生产版本
```bash
npm run preview
# 或
yarn preview
```

## 📁 项目结构

```
frontend/
├── src/
│   ├── components/           # 可复用组件
│   │   └── Header.tsx       # 头部组件
│   ├── pages/               # 页面组件
│   │   ├── Dashboard.tsx    # 仪表盘
│   │   └── ConfigManagement.tsx # 配置管理
│   ├── services/           # API服务
│   │   └── configService.ts # 配置服务
│   ├── hooks/              # 自定义Hooks
│   ├── utils/              # 工具函数
│   ├── types/              # TypeScript类型定义
│   ├── App.tsx             # 主应用组件
│   ├── main.tsx            # 应用入口
│   ├── App.css             # 应用样式
│   └── index.css           # 全局样式
├── public/                 # 静态资源
├── package.json            # 项目配置
├── vite.config.ts         # Vite配置
├── tsconfig.json          # TypeScript配置
└── index.html             # HTML模板
```

## 🎨 页面功能

### 仪表盘 (Dashboard)
- 系统状态概览
- 服务健康检查
- 实时数据展示
- 系统信息

### 配置管理 (Config Management)
- 服务配置管理
- 连接测试
- 配置同步
- 配置导出

## 🔧 开发指南

### 添加新页面
1. 在 `src/pages/` 中创建新组件
2. 在 `src/App.tsx` 中添加路由
3. 更新导航菜单

### 添加新组件
1. 在 `src/components/` 中创建组件
2. 导出组件
3. 在需要的地方导入使用

### 添加API服务
1. 在 `src/services/` 中创建服务文件
2. 定义API接口
3. 在组件中使用

## 🎯 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI库**: Ant Design 5.x
- **路由**: React Router v6
- **状态管理**: Zustand
- **HTTP客户端**: Axios
- **样式**: CSS Modules
- **图标**: Ant Design Icons

## 📱 响应式设计

- 支持桌面端、平板端、移动端
- 使用Ant Design的栅格系统
- 响应式布局和组件

## 🔧 配置

### 环境变量
```bash
# API基础URL
VITE_API_BASE_URL=http://localhost:8000

# 应用标题
VITE_APP_TITLE=微信客服中台
```

### 代理配置
开发环境下，API请求会自动代理到后端服务：
```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

## 🧪 测试

```bash
# 运行测试
npm run test

# 类型检查
npm run type-check

# 代码检查
npm run lint
```

## 🚀 部署

### 构建生产版本
```bash
npm run build
```

### 部署到静态服务器
将 `dist/` 目录部署到任何静态文件服务器。

### Docker部署
```bash
# 构建镜像
docker build -t wxauto-frontend .

# 运行容器
docker run -p 3000:80 wxauto-frontend
```

## 📄 许可证

MIT License
