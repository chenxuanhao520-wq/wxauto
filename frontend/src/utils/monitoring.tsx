import React, { useState, useEffect, useCallback } from 'react';
import { message, notification } from 'antd';

// 错误监控和日志上报模块
class ErrorMonitor {
  private static instance: ErrorMonitor;
  private errorQueue: any[] = [];
  private logQueue: any[] = [];
  private isOnline: boolean = true;
  private apiBaseUrl: string = 'http://localhost:8002';

  private constructor() {
    this.setupGlobalErrorHandlers();
    this.setupNetworkMonitoring();
    this.startBatchUpload();
  }

  public static getInstance(): ErrorMonitor {
    if (!ErrorMonitor.instance) {
      ErrorMonitor.instance = new ErrorMonitor();
    }
    return ErrorMonitor.instance;
  }

  // 设置全局错误处理器
  private setupGlobalErrorHandlers(): void {
    // 捕获未处理的JavaScript错误
    window.addEventListener('error', (event) => {
      this.reportError({
        type: 'javascript_error',
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      });
    });

    // 捕获未处理的Promise拒绝
    window.addEventListener('unhandledrejection', (event) => {
      this.reportError({
        type: 'unhandled_promise_rejection',
        message: event.reason?.message || 'Unhandled Promise Rejection',
        stack: event.reason?.stack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      });
    });

    // 捕获React错误边界
    window.addEventListener('react_error', (event: any) => {
      this.reportError({
        type: 'react_error',
        message: event.detail.error?.message,
        stack: event.detail.error?.stack,
        componentStack: event.detail.componentStack,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      });
    });
  }

  // 设置网络监控
  private setupNetworkMonitoring(): void {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.flushQueues();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }

  // 上报错误
  public reportError(error: any): void {
    const errorEntry = {
      id: this.generateId(),
      level: 'ERROR',
      component: 'frontend',
      ...error
    };

    this.errorQueue.push(errorEntry);
    console.error('🚨 错误已记录:', errorEntry);

    // 如果队列满了，立即上传
    if (this.errorQueue.length >= 10) {
      this.flushErrorQueue();
    }
  }

  // 上报日志
  public reportLog(level: string, component: string, message: string, details?: any): void {
    const logEntry = {
      id: this.generateId(),
      timestamp: new Date().toISOString(),
      level,
      component,
      message,
      details: details || {}
    };

    this.logQueue.push(logEntry);
    console.log(`📋 日志已记录 [${level}]:`, message);

    // 如果队列满了，立即上传
    if (this.logQueue.length >= 50) {
      this.flushLogQueue();
    }
  }

  // 批量上传
  private startBatchUpload(): void {
    // 每30秒上传一次
    setInterval(() => {
      this.flushQueues();
    }, 30000);
  }

  // 刷新所有队列
  private async flushQueues(): Promise<void> {
    if (!this.isOnline) return;

    await Promise.all([
      this.flushErrorQueue(),
      this.flushLogQueue()
    ]);
  }

  // 上传错误队列
  private async flushErrorQueue(): Promise<void> {
    if (this.errorQueue.length === 0 || !this.isOnline) return;

    const errors = [...this.errorQueue];
    this.errorQueue = [];

    try {
      const response = await fetch(`${this.apiBaseUrl}/api/errors/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`
        },
        body: JSON.stringify({ errors })
      });

      if (response.ok) {
        console.log(`✅ 成功上传 ${errors.length} 个错误`);
      } else {
        console.error('❌ 错误上传失败:', response.status);
        // 重新加入队列
        this.errorQueue.unshift(...errors);
      }
    } catch (error) {
      console.error('❌ 错误上传异常:', error);
      // 重新加入队列
      this.errorQueue.unshift(...errors);
    }
  }

  // 上传日志队列
  private async flushLogQueue(): Promise<void> {
    if (this.logQueue.length === 0 || !this.isOnline) return;

    const logs = [...this.logQueue];
    this.logQueue = [];

    try {
      const response = await fetch(`${this.apiBaseUrl}/api/logs/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`
        },
        body: JSON.stringify({ logs })
      });

      if (response.ok) {
        console.log(`✅ 成功上传 ${logs.length} 条日志`);
      } else {
        console.error('❌ 日志上传失败:', response.status);
        // 重新加入队列
        this.logQueue.unshift(...logs);
      }
    } catch (error) {
      console.error('❌ 日志上传异常:', error);
      // 重新加入队列
      this.logQueue.unshift(...logs);
    }
  }

  // 生成唯一ID
  private generateId(): string {
    return `frontend_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // 获取认证令牌
  private getAuthToken(): string {
    return localStorage.getItem('auth_token') || '';
  }

  // 获取队列状态
  public getQueueStatus(): { errors: number; logs: number; isOnline: boolean } {
    return {
      errors: this.errorQueue.length,
      logs: this.logQueue.length,
      isOnline: this.isOnline
    };
  }
}

// React错误边界组件
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // 上报React错误
    const errorMonitor = ErrorMonitor.getInstance();
    errorMonitor.reportError({
      type: 'react_error_boundary',
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    });

    // 显示错误通知
    notification.error({
      message: '应用错误',
      description: '检测到应用错误，已自动上报。请刷新页面重试。',
      duration: 0
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '50px', textAlign: 'center' }}>
          <h2>😵 应用出现错误</h2>
          <p>我们已自动上报此错误，请刷新页面重试。</p>
          <button onClick={() => window.location.reload()}>
            刷新页面
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// API请求拦截器
class ApiInterceptor {
  private static instance: ApiInterceptor;
  private errorMonitor: ErrorMonitor;

  private constructor() {
    this.errorMonitor = ErrorMonitor.getInstance();
    this.setupInterceptors();
  }

  public static getInstance(): ApiInterceptor {
    if (!ApiInterceptor.instance) {
      ApiInterceptor.instance = new ApiInterceptor();
    }
    return ApiInterceptor.instance;
  }

  private setupInterceptors(): void {
    // 拦截fetch请求
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const startTime = Date.now();
      
      try {
        const response = await originalFetch(...args);
        const endTime = Date.now();
        
        // 记录API调用日志
        this.errorMonitor.reportLog(
          'INFO',
          'api_call',
          `API调用: ${args[0]}`,
          {
            method: 'GET', // 简化处理
            status: response.status,
            duration: endTime - startTime,
            url: args[0]
          }
        );

        // 如果API调用失败，记录错误
        if (!response.ok) {
          this.errorMonitor.reportError({
            type: 'api_error',
            message: `API调用失败: ${response.status}`,
            url: args[0],
            status: response.status,
            timestamp: new Date().toISOString()
          });
        }

        return response;
      } catch (error) {
        // 记录网络错误
        this.errorMonitor.reportError({
          type: 'network_error',
          message: error instanceof Error ? error.message : '网络请求失败',
          url: args[0],
          timestamp: new Date().toISOString()
        });
        
        throw error;
      }
    };
  }
}

// 性能监控
class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private errorMonitor: ErrorMonitor;

  private constructor() {
    this.errorMonitor = ErrorMonitor.getInstance();
    this.setupPerformanceMonitoring();
  }

  public static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  private setupPerformanceMonitoring(): void {
    // 监控页面加载性能
    window.addEventListener('load', () => {
      setTimeout(() => {
        const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        
        this.errorMonitor.reportLog(
          'INFO',
          'performance',
          '页面加载性能',
          {
            loadTime: perfData.loadEventEnd - perfData.loadEventStart,
            domContentLoaded: perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
            firstPaint: this.getFirstPaint(),
            firstContentfulPaint: this.getFirstContentfulPaint()
          }
        );
      }, 0);
    });

    // 监控长任务
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.duration > 50) { // 超过50ms的任务
            this.errorMonitor.reportLog(
              'WARNING',
              'performance',
              '检测到长任务',
              {
                duration: entry.duration,
                startTime: entry.startTime,
                name: entry.name
              }
            );
          }
        }
      });
      
      observer.observe({ entryTypes: ['longtask'] });
    }
  }

  private getFirstPaint(): number {
    const paintEntries = performance.getEntriesByType('paint');
    const fpEntry = paintEntries.find(entry => entry.name === 'first-paint');
    return fpEntry ? fpEntry.startTime : 0;
  }

  private getFirstContentfulPaint(): number {
    const paintEntries = performance.getEntriesByType('paint');
    const fcpEntry = paintEntries.find(entry => entry.name === 'first-contentful-paint');
    return fcpEntry ? fcpEntry.startTime : 0;
  }
}

// 用户行为监控
class UserBehaviorMonitor {
  private static instance: UserBehaviorMonitor;
  private errorMonitor: ErrorMonitor;
  private sessionId: string;

  private constructor() {
    this.errorMonitor = ErrorMonitor.getInstance();
    this.sessionId = this.generateSessionId();
    this.setupBehaviorTracking();
  }

  public static getInstance(): UserBehaviorMonitor {
    if (!UserBehaviorMonitor.instance) {
      UserBehaviorMonitor.instance = new UserBehaviorMonitor();
    }
    return UserBehaviorMonitor.instance;
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupBehaviorTracking(): void {
    // 跟踪页面访问
    this.trackPageView();

    // 跟踪用户交互
    document.addEventListener('click', (event) => {
      const target = event.target as HTMLElement;
      this.errorMonitor.reportLog(
        'INFO',
        'user_behavior',
        '用户点击',
        {
          sessionId: this.sessionId,
          element: target.tagName,
          className: target.className,
          id: target.id,
          text: target.textContent?.substring(0, 100),
          url: window.location.href,
          timestamp: new Date().toISOString()
        }
      );
    });

    // 跟踪表单提交
    document.addEventListener('submit', (event) => {
      const form = event.target as HTMLFormElement;
      this.errorMonitor.reportLog(
        'INFO',
        'user_behavior',
        '表单提交',
        {
          sessionId: this.sessionId,
          formId: form.id,
          formClass: form.className,
          action: form.action,
          method: form.method,
          url: window.location.href,
          timestamp: new Date().toISOString()
        }
      );
    });
  }

  private trackPageView(): void {
    this.errorMonitor.reportLog(
      'INFO',
      'user_behavior',
      '页面访问',
      {
        sessionId: this.sessionId,
        url: window.location.href,
        referrer: document.referrer,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString()
      }
    );
  }
}

// 初始化监控系统
export const initializeMonitoring = (): void => {
  // 初始化错误监控
  ErrorMonitor.getInstance();
  
  // 初始化API拦截器
  ApiInterceptor.getInstance();
  
  // 初始化性能监控
  PerformanceMonitor.getInstance();
  
  // 初始化用户行为监控
  UserBehaviorMonitor.getInstance();
  
  console.log('🔍 监控系统已初始化');
};

// 导出组件和工具
export { ErrorBoundary, ErrorMonitor };
export default ErrorBoundary;
