#!/bin/bash
# -------------------------------------------------------------
# SEMCAT / RoSE AMR Web Application Launcher
# (FastAPI Backend + Glassmorphic Frontend + Public Link)
# -------------------------------------------------------------

CDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$CDIR"

eval "$(~/miniconda3/bin/conda shell.bash hook)"
conda activate ssharp

PORT=8000
IS_SHARE=0

for arg in "$@"
do
    if [ "$arg" == "--share" ]; then
        IS_SHARE=1
    fi
done

echo "=========================================================="
echo "🚀 ĐANG KHỞI CHẠY HỆ THỐNG WEB SEMCAT / RoSE AMR"
echo "=========================================================="
echo "📍 Địa chỉ máy cục bộ (Local): http://localhost:$PORT"

if [ $IS_SHARE -eq 1 ]; then
    echo "🌐 Đang khởi tạo đường link công khai (Public Link)..."
    npx -y localtunnel --port $PORT &
    TUNNEL_PID=$!
fi

echo "----------------------------------------------------------"
echo "Bấm Ctrl+C để dừng hệ thống."
echo "=========================================================="

python web_app/server.py
