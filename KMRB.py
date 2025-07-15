#!/usr/bin/env python3
"""
KMRB 영화 등급 모니터링 시스템
TARGET_COUNT 달성 시 자동 중단
"""

import requests
import re
import time
from datetime import datetime
from urllib.parse import urlencode

class MovieMonitor:
    def __init__(self):
        # 설정값
        self.TARGET_COUNT = 1  # 목표 숫자 (달성 시 중단)
        self.SEARCH_KEYWORD = "판타스틱 4"  # 검색할 영화명
        
        # 텔레그램 설정
        self.TELEGRAM_TOKEN = "7787965493:AAEeHQIi61sUVPFjjcAWFzsQWc2WQnfUAk0"
        self.TELEGRAM_CHAT_ID = "1680893056"
        
        # KMRB 사이트 설정
        self.BASE_URL = "https://www.kmrb.or.kr/kor/CMS/TotalSearch/search.do"
        self.PARAMS = {
            'mCode': 'MN132',
            'site_code': '',
            'category_code': 'ORS',
            'category_code2': 'MV',
            'category_code3': '',
            'grade_name': '',
            'rcv_no': '',
            'return_url': '',
            'searchKeyword': self.SEARCH_KEYWORD
        }
        
        # 등급 매핑
        self.GRADE_MAP = {
            '전체관람가': '전체 관람가',
            '12세이상관람가': '12세 관람가',
            '15세이상관람가': '15세 관람가',
            '청소년관람불가': '19세 관람가'
        }
    
    def get_movie_details(self):
        """KMRB 사이트에서 영화 상세 정보 추출"""
        try:
            # URL 생성
            url = f"{self.BASE_URL}?{urlencode(self.PARAMS)}"
            
            # 헤더 설정
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # 요청 보내기
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # HTML에서 영화 개수 추출
            count_pattern = r'<span[^>]*class="text"[^>]*>영화\((\d+)\)</span>'
            count_match = re.search(count_pattern, response.text)
            
            if not count_match:
                self.log("영화 개수를 찾을 수 없습니다.")
                return None, []
            
            count = int(count_match.group(1))
            self.log(f"현재 영화 개수: {count}")
            
            # 영화 상세 정보 추출 (최신순으로 정렬됨)
            movies = []
            
            # 영화 항목 패턴 - onclick 속성에서 정보 추출
            movie_pattern = r'<a[^>]*href="#tab"[^>]*onclick="gradeView\(\'ORS\',\'MV\',\s*\'\',\'([^\']*)\',\'([^\']*)\',\s*\'\',\'[^\']*\'\s*\);"[^>]*>.*?<em[^>]*>\s*([^<]+)\s*</em>'
            
            matches = re.findall(movie_pattern, response.text, re.DOTALL)
            
            for match in matches:
                grade_raw = match[0]  # 등급 (예: "12세이상관람가")
                rcv_no = match[1]     # 수신번호
                title = match[2].strip()  # 제목
                
                # 등급 변환
                grade_display = self.GRADE_MAP.get(grade_raw, grade_raw)
                
                movies.append({
                    'title': title,
                    'grade': grade_display,
                    'grade_raw': grade_raw,
                    'rcv_no': rcv_no
                })
            
            self.log(f"추출된 영화 정보: {len(movies)}개")
            return count, movies
            
        except requests.RequestException as e:
            self.log(f"네트워크 오류: {e}")
            return None, []
        except Exception as e:
            self.log(f"오류 발생: {e}")
            return None, []
    
    def create_search_url(self, title):
        """영화 제목으로 검색 URL 생성"""
        search_params = {
            'mCode': 'MN132',
            'site_code': '',
            'category_code': 'ORS',
            'category_code2': 'MV',
            'category_code3': '',
            'grade_name': '',
            'rcv_no': '',
            'return_url': '',
            'searchKeyword': title
        }
        return f"{self.BASE_URL}?{urlencode(search_params)}"
    
    def format_movie_message(self, movies, current_count):
        """새로운 영화 정보만 텔레그램 메시지 형식으로 변환"""
        if not movies:
            return "영화 정보를 찾을 수 없습니다."
        
        message = "🎬 <b>판타스틱 4 영등위 심의 완료!</b>\n\n"
        
        # 차이값만큼 최신 영화만 전송
        new_movie_count = current_count - self.TARGET_COUNT
        new_movies = movies[:new_movie_count]  # 최신 영화부터
        
        self.log(f"새로운 영화 {new_movie_count}개 중 {len(new_movies)}개 전송")
        
        for movie in new_movies:
            # 영화 제목으로 검색 URL 생성
            search_url = self.create_search_url(movie['title'])
            
            # 영화 제목과 등급을 하이퍼링크로 구성
            message += f"<a href=\"{search_url}\">{movie['title']} ({movie['grade']})</a>\n"
        
        return message
    
    def send_telegram(self, message):
        """텔레그램 메시지 전송"""
        try:
            url = f"https://api.telegram.org/bot{self.TELEGRAM_TOKEN}/sendMessage"
            data = {
                'chat_id': self.TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                self.log("텔레그램 알림 전송 성공")
            else:
                self.log(f"텔레그램 전송 실패: {response.status_code}")
                
        except Exception as e:
            self.log(f"텔레그램 전송 오류: {e}")
    
    def log(self, message):
        """로그 출력"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def run_continuous_monitor(self):
        """1분마다 지속적으로 모니터링, 목표 달성 시 중단"""
        self.log(f"KMRB 모니터링 시작 - 목표: {self.TARGET_COUNT}개 이상")
        
        while True:
            try:
                # 현재 영화 정보 확인
                current_count, movies = self.get_movie_details()
                if current_count is None:
                    self.log("영화 정보 확인 실패 - 1분 후 재시도")
                    time.sleep(60)
                    continue
                
                # 목표 달성 확인
                if current_count >= self.TARGET_COUNT:
                    self.log(f"🎉 목표 달성! 영화 개수: {current_count} >= {self.TARGET_COUNT}")
                    
                    # 텔레그램 알림 전송 (차이값만큼만)
                    message = self.format_movie_message(movies, current_count)
                    self.send_telegram(message)
                    
                    self.log("모니터링 완료 - 대기 모드로 전환")
                    # 목표 달성 후 무한 대기 (Render 재시작 방지)
                    while True:
                        self.log("목표 달성 완료 - 대기 중...")
                        time.sleep(3600)  # 1시간마다 상태 출력
                else:
                    self.log(f"목표 미달성: {current_count} < {self.TARGET_COUNT} - 1분 후 재시도")
                
                # 1분 대기
                time.sleep(60)
                
            except KeyboardInterrupt:
                self.log("모니터링 중단됨")
                break
            except Exception as e:
                self.log(f"예상치 못한 오류: {e} - 1분 후 재시도")
                time.sleep(60)

def main():
    monitor = MovieMonitor()
    monitor.run_continuous_monitor()

if __name__ == "__main__":
    main()