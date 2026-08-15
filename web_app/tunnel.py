import subprocess
import time
import sys
import os

def start_localtunnel(port=8000):
    print(f"\n🌐 Đang tạo đường link công khai (Public Link) cho cổng {port}...")
    try:
        process = subprocess.Popen(
            ["npx", "-y", "localtunnel", "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        time.sleep(3)
        print("="*65)
        print(f"🚀 DỰ ÁN WEB SEMCAT / RoSE AMR - BACKEND + FRONTEND ACTIVE!")
        print(f"📍 TRUY CẬP CỤC BỘ (LOCAL):    http://localhost:{port}")
        print("🌐 LINK CÔNG KHAI (PUBLIC):    Đang lắng nghe kết nối từ localtunnel...")
        print("="*65 + "\n")
        return process
    except Exception as e:
        print(f"⚠️ Không thể khởi chạy localtunnel: {e}")
        return None

if __name__ == "__main__":
    start_localtunnel()
