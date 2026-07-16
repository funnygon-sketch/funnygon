"""
mykbostats.com (비공식 KBO 정보 사이트)에서 한화이글스 경기 일정을 가져옵니다.
KBO 공식 사이트는 세션/파라미터가 복잡하고 응답 구조도 파싱이 까다로워서,
더 단순한 형식으로 제공하는 이 사이트를 대신 사용합니다.

주의: 비공식 팬 사이트이므로 100% 정확하다는 보장은 없습니다.
경기 취소/시간 변경 등 중요한 건 공식 채널로 재확인하세요.
"""
import json
import os
import re
import sys
import time
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

import config

BASE_URL = "https://mykbostats.com/schedule/week_of/{date}"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; personal-calendar-script/1.0)"}

GAME_LINK_RE = re.compile(r"^/games/(\d+)-([A-Za-z]+)-vs-([A-Za-z]+)-(\d{8})$")
TIME_RE = re.compile(r"(\d{1,2}):(\d{2})(am|pm)", re.IGNORECASE)

TEAM_NAME_HANWHA = "Hanwha"


def fetch_week(monday: date) -> list[dict]:
    url = BASE_URL.format(date=monday.isoformat())
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"[경고] {monday} 주간 조회 실패: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    games = []
    for a in soup.find_all("a", href=GAME_LINK_RE):
        m = GAME_LINK_RE.match(a["href"])
        game_id, away, home, date_str = m.groups()
        if TEAM_NAME_HANWHA not in (away, home):
            continue

        text = a.get_text(" ", strip=True)
        tm = TIME_RE.search(text)
        if tm:
            hour, minute, ampm = int(tm.group(1)), tm.group(2), tm.group(3).lower()
            if ampm == "pm" and hour != 12:
                hour += 12
            if ampm == "am" and hour == 12:
                hour = 0
            time_str = f"{hour:02d}:{minute}"
        else:
            time_str = "18:30"

        location = ""
        if tm:
            after = text[tm.end():].strip()
            location = after.split("Chance of")[0].strip()

        games.append(
            {
                "game_id": game_id,
                "date": date_str,
                "time": time_str,
                "home": home,
                "away": away,
                "stadium": location,
                "is_home": home == TEAM_NAME_HANWHA,
            }
        )
    return games


def main():
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    start = date(config.SEASON_YEAR, 1, 1)
    start += timedelta(days=(7 - start.weekday()) % 7)  # 그 해 첫 월요일부터 시작

    all_games = {}
    d = start
    while d.year == config.SEASON_YEAR:
        week_games = fetch_week(d)
        for g in week_games:
            all_games[g["game_id"]] = g  # 중복 제거
        if week_games:
            print(f"[디버그] {d} 주간: {len(week_games)}건 발견", file=sys.stderr)
        d += timedelta(days=7)
        time.sleep(1)  # 서버 부하 방지

    games_list = sorted(all_games.values(), key=lambda g: (g["date"], g["time"]))
    with open(config.GAMES_JSON, "w", encoding="utf-8") as f:
        json.dump(games_list, f, ensure_ascii=False, indent=2)

    print(f"총 {len(games_list)}경기 저장됨 → {config.GAMES_JSON}")


if __name__ == "__main__":
    main()
