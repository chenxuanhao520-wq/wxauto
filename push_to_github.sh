#!/bin/bash
# 推送代码到 GitHub

echo "🚀 开始推送代码到 GitHub..."

# 检查网络连接
echo "📡 检查 GitHub 连接..."
if ! ping -c 1 github.com &> /dev/null; then
    echo "❌ 无法连接到 GitHub，请检查网络连接"
    exit 1
fi

echo "✅ GitHub 连接正常"

# 尝试推送
echo "📤 推送代码到远程仓库..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ 代码推送成功！"
    echo ""
    echo "📊 提交统计:"
    git log origin/main..main --oneline
    echo ""
    echo "🎉 GitHub 仓库已更新: https://github.com/chenxuanhao520-wq/wxauto"
else
    echo "❌ 推送失败，请检查："
    echo "  1. 网络连接是否正常"
    echo "  2. GitHub 访问权限是否正确"
    echo "  3. 是否需要配置代理"
    echo ""
    echo "💡 可以尝试："
    echo "  - 使用 SSH: git remote set-url origin git@github.com:chenxuanhao520-wq/wxauto.git"
    echo "  - 配置代理: git config --global http.proxy http://127.0.0.1:7890"
    echo "  - 手动推送: git push origin main --verbose"
fi

