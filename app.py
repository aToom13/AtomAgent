#!/usr/bin/env python3
"""
AtomAgent Ana Başlatma Scripti
Backend ve Frontend'i aynı anda başlatır
"""

import os
import sys
import subprocess
import time
import threading
import signal
from pathlib import Path

def run_command(command, cwd=None):
    """Komut çalıştır ve çıktıyı göster"""
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Çıktıyı gerçek zamanlı göster
        for line in process.stdout:
            print(line, end='')
        
        return process.wait()
    except Exception as e:
        print(f"Hata: {e}")
        return 1

def start_backend():
    """Backend sunucusunu başlat"""
    print("🚀 Backend sunucusu başlatılıyor...")
    backend_dir = Path("src/backend")
    
    if not backend_dir.exists():
        print("❌ Backend dizini bulunamadı: src/backend")
        return False
    
    # Backend dizinine geç ve server.py'yi çalıştır
    os.chdir(backend_dir)
    return run_command("python server.py")

def start_frontend():
    """Frontend sunucusunu başlat"""
    print("🎨 Frontend sunucusu başlatılıyor...")
    
    # Ana dizine dön
    os.chdir("..")
    
    # npm run dev komutunu çalıştır
    return run_command("npm run dev")

def main():
    """Ana fonksiyon"""
    print("🔧 AtomAgent Başlatma Sistemi")
    print("=" * 50)
    
    # Backend ve frontend process'leri
    backend_process = None
    frontend_process = None
    
    def signal_handler(signum, frame):
        """Ctrl+C ile process'leri sonlandır"""
        print("\n🛑 Sistem kapatılıyor...")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        sys.exit(0)
    
    # Sinyal handler'ı ekle
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Backend'i arka planda başlat
        print("1️⃣  Backend sunucusu arka planda başlatılıyor...")
        backend_thread = threading.Thread(target=start_backend)
        backend_thread.daemon = True
        backend_thread.start()
        
        # Backend'in başlaması için bekle
        print("⏳ Backend başlatılıyor, lütfen bekleyin...")
        time.sleep(5)
        
        # Frontend'i arka planda başlat
        print("2️⃣  Frontend sunucusu arka planda başlatılıyor...")
        frontend_thread = threading.Thread(target=start_frontend)
        frontend_thread.daemon = True
        frontend_thread.start()
        
        # Frontend'in başlaması için bekle
        print("⏳ Frontend başlatılıyor, lütfen bekleyin...")
        time.sleep(3)
        
        print("\n✅ Sistem başarıyla başlatıldı!")
        print("=" * 50)
        print("🌐 Frontend: http://localhost:5173")
        print("🔧 Backend:  http://localhost:5001")
        print("⚠️  Çıkmak için Ctrl+C'ye basın")
        print("=" * 50)
        
        # Process'lerin bitmesini bekle
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
