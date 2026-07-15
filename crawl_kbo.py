"""
KBO 공식 사이트에서 한화이글스 경기 일정을 가져옵니다.

주의: KBO 사이트는 자바스크립트(AJAX)로 일정을 불러오기 때문에 요청 형식이
구단/시즌 갱신 시 바뀔 수 있습니다. 이 스크립트가 빈 결과를 반환하면
아래 "요청 형식이 바뀐 경우" 안내를 참고해 파라미터를 다시 확인해주세요.

개인적/비상업적 용도로만 사용하고, 짧은 시간에 과도한 요청을 보내지 마세요.
"""
import json
import sys
import time
from datetime import datetime

import requests

import config

SCHEDULE_URL = "https://www.koreabaseball.com/ws/Schedule.asmx/GetScheduleList"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.koreabaseball.com/Schedule/Schedule.aspx",
}


def fetch_month(year: int, month: int) -> list[dict]:
    """해당 연/월의 전체 경기 목록을 가져옵니다 (실패 시 빈 리스트)."""
    payload = {
        "leId": 1,       # 1 = KBO 리그
        "srId": "0,1,3", # 시범경기(0), 정규시즌(1), 포스트시즌(3) — 필요없는 시리즈는 빼도 됨
        "seasonId": year,
        "gameMonth": f"{month:02d}",
    }
    try:
        res = requests.post(SCHEDULE_URL, data=payload, headers=HEADERS, timeout=10)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        print(f"[경고] {year}-{month:02d} 요청 실패: {e}", file=sys.stderr)
        return []

    rows = data.get("rows") or data.get("row") or data.get("d") or []
    if isinstance(rows, str):
        try:
            rows = json.loads(rows)
        except json.JSONDecodeError:
            rows = []
    if not rows:
        print(
            f"[안내] {year}-{month:02d} 응답에서 경기 데이터를 찾지 못했습니다. "
            "response 구조가 바뀐 것일 수 있습니다 — 아래 raw_response 파일을 확인하세요.",
            file=sys.stderr,
        )
        with open(f"/tmp/kbo_raw_{year}_{month:02d}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return rows


def filter_team_games(rows: list[dict], team_code: str) -> list[dict]:
    games = []
    for row in rows:
        game_id = row.get("G_ID") or row.get("gameId") or ""
        home = row.get("HOME_ID") or row.get("homeId") or ""
        away = row.get("AWAY_ID") or row.get("awayId") or ""
        if team_code not in (home, away) and team_code not in game_id:
            continue
        games.append(
            {
                "game_id": game_id,
                "date": row.get("G_DT") or row.get("gameDate"),
                "time": row.get("G_TM") or row.get("gameTime") or "18:30",
                "home": home,
                "away": away,
                "stadium": row.get("S_NM") or row.get("stadium") or "",
                "is_home": home == team_code,
            }
        )
    return games


def main():
    all_games = []
    for month in range(1, 13):
        rows = fetch_month(config.SEASON_YEAR, month)
        all_games.extend(filter_team_games(rows, config.TEAM_CODE))
        time.sleep(1)  # 서버 부하 방지용 딜레이

    with open(config.GAMES_JSON, "w", encoding="utf-8") as f:
        json.dump(all_games, f, ensure_ascii=False, indent=2)

    print(f"총 {len(all_games)}경기 저장됨 → {config.GAMES_JSON}")


if __name__ == "__main__":
    main()
