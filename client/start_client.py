#!/usr/bin/env python3
"""
Wxauto Smart Service - 客户端启动脚本
一键启动Web前端和本地代理
"""

import os
import sys
import time
import subprocess
import threading
import webbrowser
from pathlib import Path
from typing import List, Optional

class ClientLauncher:
    """客户端启动器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.processes: List[subprocess.Popen] = []
        self.running = True
    
    def start_web_frontend(self) -> bool:
        """启动Web前端"""
        try:
            frontend_dir = self.project_root / "frontend"
            
            if not frontend_dir.exists():
                print("❌ 前端目录不存在")
                return False
            
            # 检查Node.js环境
            try:
                subprocess.run(["node", "--version"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print("❌ Node.js未安装，请先安装Node.js")
                return False
            
            # 安装依赖
            print("📦 安装前端依赖...")
            result = subprocess.run(
                ["npm", "install"],
                cwd=frontend_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ 前端依赖安装失败: {result.stderr}")
                return False
            
            # 启动前端开发服务器
            print("🚀 启动前端开发服务器...")
            process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes.append(process)
            
            # 等待前端启动
            time.sleep(5)
            
            # 打开浏览器
            try:
                webbrowser.open("http://localhost:3000")
                print("🌐 前端界面已打开: http://localhost:3000")
            except Exception as e:
                print(f"⚠️ 无法自动打开浏览器: {e}")
                print("请手动访问: http://localhost:3000")
            
            return True
            
        except Exception as e:
            print(f"❌ 启动前端失败: {e}")
            return False
    
    def start_local_agent(self) -> bool:
        """启动本地代理"""
        try:
            agent_file = self.project_root / "client" / "local_agent.py"
            
            if not agent_file.exists():
                print("❌ 本地代理文件不存在")
                return False
            
            # 检查Python环境
            try:
                subprocess.run([sys.executable, "--version"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print("❌ Python环境异常")
                return False
            
            # 启动本地代理
            print("🤖 启动本地微信代理...")
            process = subprocess.Popen(
                [sys.executable, str(agent_file), "--api-port", "8001"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes.append(process)
            
            # 等待代理启动
            time.sleep(3)
            
            print("✅ 本地代理启动成功")
            return True
            
        except Exception as e:
            print(f"❌ 启动本地代理失败: {e}")
            return False
    
    def start_backend_api(self) -> bool:
        """启动后端API"""
        try:
            api_file = self.project_root / "backend" / "api" / "client_management.py"
            
            if not api_file.exists():
                print("❌ 后端API文件不存在")
                return False
            
            # 启动后端API
            print("🔧 启动后端API服务...")
            process = subprocess.Popen(
                [sys.executable, str(api_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes.append(process)
            
            # 等待API启动
            time.sleep(3)
            
            print("✅ 后端API启动成功")
            return True
            
        except Exception as e:
            print(f"❌ 启动后端API失败: {e}")
            return False
    
    def monitor_processes(self):
        """监控进程状态"""
        while self.running:
            try:
                for i, process in enumerate(self.processes):
                    if process.poll() is not None:
                        print(f"⚠️ 进程 {i} 已退出")
                        self.processes.pop(i)
                        break
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ 监控进程失败: {e}")
                break
    
    def stop_all(self):
        """停止所有进程"""
        print("⏹️ 正在停止所有服务...")
        
        self.running = False
        
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                print(f"❌ 停止进程失败: {e}")
        
        self.processes.clear()
        print("✅ 所有服务已停止")
    
    def start_all(self) -> bool:
        """启动所有服务"""
        print("🚀 启动 Wxauto Smart Service 客户端")
        print("=" * 50)
        
        success = True
        
        # 启动后端API
        if not self.start_backend_api():
            success = False
        
        # 启动本地代理
        if not self.start_local_agent():
            success = False
        
        # 启动Web前端
        if not self.start_web_frontend():
            success = False
        
        if success:
            print("=" * 50)
            print("🎉 所有服务启动成功！")
            print("📱 Web前端: http://localhost:3000")
            print("🤖 本地代理: http://localhost:8001")
            print("🔧 后端API: http://localhost:8002")
            print("=" * 50)
            print("按 Ctrl+C 停止所有服务")
            
            # 启动监控线程
            monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
            monitor_thread.start()
            
            # 等待用户中断
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 收到退出信号")
                self.stop_all()
        else:
            print("❌ 部分服务启动失败")
            self.stop_all()
            return False
        
        return True


def main():
    """主函数"""
    launcher = ClientLauncher()
    
    try:
        launcher.start_all()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        launcher.stop_all()
        sys.exit(1)


if __name__ == "__main__":
    main()
