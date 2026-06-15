#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# 启动后端
echo "[info] 启动后端 http://localhost:5000 ..."
conda run -n foodwise python "$BACKEND_DIR/app.py" &
BACKEND_PID=$!

# 等待后端就绪（最多 10 秒）
for i in $(seq 1 10); do
    if curl -sf http://localhost:5000/api/health > /dev/null 2>&1; then
        echo "[info] 后端已就绪"
        break
    fi
    sleep 1
done

# 启动前端
echo "[info] 启动前端 http://localhost:5173 ..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "  慧食 FoodWise 已启动"
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:5000"
echo "  按 Ctrl+C 停止所有服务"
echo "========================================"

# Ctrl+C 时同时停止两个进程
trap "echo ''; echo '[info] 正在停止...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

wait
