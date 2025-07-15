#!/usr/bin/env python3
"""
Render용 KMRB 모니터링 스케줄러
5분마다 KMRB.py를 실행하여 영화 등급 변화를 모니터링
"""

import schedule
import time
import subprocess
import sys
import os
from datetime import datetime
from flask import Flask

# Flask 웹 서버 (Render에서 웹 서비스로 실행하기 위함)
app = Flask(__name__)

@app.route('/')
def home():
    return "KMRB Monitor is running!"

@app.route('/status')
def status():
    return {"status": "running", "timestamp": datetime.now().isoformat()}

def log(message):
    """로그 출력"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_kmrb_monitor():
    """KMRB 모니터링 실행"""
    try:
        log("KMRB 모니터링 시작")
        
        # KMRB.py 실행
        result = subprocess.run([sys.executable, "KMRB.py"], 
                              capture_output=True, text=True, timeout=60)
        
        # 출력 로그
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"오류: {result.stderr}")
        
        if result.returncode == 0:
            log("KMRB 모니터링 완료")
        else:
            log(f"KMRB 모니터링 실패 (코드: {result.returncode})")
            
    except subprocess.TimeoutExpired:
        log("KMRB 모니터링 시간 초과")
    except Exception as e:
        log(f"KMRB 모니터링 오류: {e}")

def run_scheduler():
    """스케줄러 실행"""
    log("Render KMRB 스케줄러 시작")
    
    # 5분마다 실행 스케줄 설정
    schedule.every(5).minutes.do(run_kmrb_monitor)
    
    # 시작 즉시 한 번 실행
    run_kmrb_monitor()
    
    # 스케줄 실행 루프
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)  # 30초마다 스케줄 체크
        except Exception as e:
            log(f"스케줄러 오류: {e}")
            time.sleep(60)  # 오류 시 1분 대기

if __name__ == "__main__":
    import threading
    
    # 스케줄러를 별도 스레드에서 실행
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Flask 웹 서버 실행 (Render에서 요구)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)