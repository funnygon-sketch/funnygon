"""
프로젝트 전역 설정.
환경변수로 민감정보(API 키)를 주입받습니다. GitHub Actions에서는
Repository Secrets로 등록해서 사용하세요.
"""
import os

# ── 팀 설정 ──────────────────────────────────────────────
# KBO 사이트 game id 접두어에 쓰이는 팀 코드 (예: 20260401HHLG0 → HH가 한화)
TEAM_NAME = "한화이글스"
TEAM_CODE = "HH"

# ── 티켓팅 예측 규칙 ──────────────────────────────────────
# 확인된 정보: 2026시즌 기준 홈경기 일반예매는 "경기 7일 전 오전 11시" 오픈이
# 일반적이지만, 구단 공지에 따라 8일 전으로 바뀌는 경우도 있었습니다.
# 100% 확정 규칙이 아니므로, ICS 이벤트 설명에 "예상 시각" 문구와
# 공식 확인 링크를 함께 넣습니다. 필요하면 아래 값을 조정하세요.
TICKET_OPEN_DAYS_BEFORE = 7
TICKET_OPEN_HOUR = 11
TICKET_OPEN_MINUTE = 0

TICKET_LINKS = {
    "티켓링크": "https://www.ticketlink.co.kr",
    "구단 홈페이지": "https://www.hanwhaeagles.co.kr/ticketInfo.do",
}

# ── 공공데이터포털 특일 정보 API ──────────────────────────
# https://www.data.go.kr/data/15012690/openapi.do 에서 발급
HOLIDAY_API_KEY = os.environ.get("HOLIDAY_API_KEY", "")
HOLIDAY_API_URL = (
    "http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo"
)

# ── 출력 경로 ────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "docs")
GAMES_JSON = os.path.join(OUTPUT_DIR, "_games.json")
ICS_PATH = os.path.join(OUTPUT_DIR, "hanwha.ics")

# 수집 대상 연도 (필요하면 여러 해로 확장 가능)
SEASON_YEAR = 2026
