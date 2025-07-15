#!/usr/bin/env python3
"""
단순한 KMRB 스케줄러 - Flask 없이 순수 스케줄링만
"""

import subprocess
import sys
import time
from datetime import datetime

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

def main():
    log("단순 KMRB 스케줄러 시작")
    
    # 시작 즉시 한 번 실행
    run_kmrb_monitor()
    
    # 5분마다 실행 (300초)
    while True:
        try:
            time.sleep(300)  # 5분 대기
            run_kmrb_monitor()
        except KeyboardInterrupt:
            log("스케줄러 중단됨")
            break
        except Exception as e:
            log(f"스케줄러 오류: {e}")
            time.sleep(60)  # 오류 시 1분 대기

if __name__ == "__main__":
    main()