#!/bin/bash
# -------------------------------------------------------------
# Script chạy ứng dụng Web UI SEMCAT / RoSE AMR
# -------------------------------------------------------------

# Chuyển thư mục về thư mục dự án
CDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$CDIR"

# Kích hoạt môi trường conda ssharp
eval "$(~/miniconda3/bin/conda shell.bash hook)"
conda activate ssharp

echo "=========================================================="
echo "🚀 Đang khởi chạy Giao diện Web SEMCAT / RoSE AMR..."
echo "=========================================================="

python ssharp/metric/app.py "$@"
