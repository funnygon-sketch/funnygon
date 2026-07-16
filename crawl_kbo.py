"""
KBO 공식 사이트에서 한화이글스 경기 일정을 가져옵니다.

핵심 포인트 (브라우저 devtools로 확인된 실제 요청 형식):
- 먼저 Schedule.aspx 페이지에 접속해 세션 쿠키(ASP.NET_SessionId)를 받아야 함
- srIdList는 "0,9,6" 처럼 콤마로 묶은 문자열 하나로 보냄 (여러 번 나눠 보내면 안 됨)
- teamId는 빈 문자열로 보내면 전체 팀 데이터가 옴 (우리 쪽에서 한화만 필터링)
"""
import json
import os
import sys
import time

import requests

import config

SCHEDULE_PAGE = "https://www.koreabaseball.com/Schedule/Schedule.aspx"
SCHEDULE_URL = "https://www.koreabaseball.com/ws/Schedule.asmx/GetScheduleList"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": SCHEDULE_PAGE,
    "Origin": "https://www.koreabaseball.com",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

SR_ID_LIST = "0,9,6"  # devtools로 확인된 실제 값 (시범/정규/포스트시즌 통합)


def get_session() -> requests.Session:
    """세션 쿠키를 먼저 받아온다."""
    s = requests.Session()
    s.headers.update({"User-Agent": HEADERS["User-Agent"]})
    res = s.get(SCHEDULE_PAGE, timeout=10)
    res.raise_for_status()
    print(f"[디버그] 세션 쿠키 획득: {dict(s.cookies)}", file=sys.stderr)
    return s


def fetch_month(session: requests.Session, year: int, month: int) -> list[dict]:
    payload = {
        "leId": 1,
        "srIdList": SR_ID_LIST,
        "seasonId": year,
        "gameMonth": f"{month:02d}",
        "teamId": "",
    }
    try:
        res = session.post(SCHEDULE_URL, data=payload, headers=HEADERS, timeout=10)
        print(f"[디버그] {year}-{month:02d} status={res.status_code}", file=sys.stderr)
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
        print(f"[디버그] 응답 전체({year}-{month:02d}): {json.dumps(data, ensure_ascii=False)[:500]}", file=sys.stderr)
    return rows


def filter_team_games(rows: list[dict], team_code: str) -> list[dict]:
    games = []
    for row in rows:
        # 실제 필드명은 응답 구조를 봐야 정확히 알 수 있어 여러 후보를 시도합니다.
        game_id = row.get("G_ID") or row.get("gameId") or row.get("gameid") or ""
        home = row.get("HOME_ID") or row.get("homeId") or row.get("home") or ""
        away = row.get("AWAY_ID") or row.get("awayId") or row.get("away") or ""
        if team_code not in (home, away) and team_code not in game_id:
            continue
        games.append(
            {
                "game_id": game_id,
                "date": row.get("G_DT") or row.get("gameDate") or row.get("gamedate"),
                "time": row.get("G_TM") or row.get("gameTime") or row.get("gametime") or "18:30",
                "home": home,
                "away": away,
                "stadium": row.get("S_NM") or row.get("stadium") or "",
                "is_home": home == team_code,
            }
        )
    return games


def main():
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    session = get_session()

    all_games = []
    raw_rows_sample_printed = False
    for month in range(1, 13):
        rows = fetch_month(session, config.SEASON_YEAR, month)
        if rows and not raw_rows_sample_printed:
            # 실제 데이터 1건을 로그에 남겨서 필드명을 확인할 수 있게 함
            print(f"[디버그] rows 샘플 1건: {json.dumps(rows[0], ensure_ascii=False)}", file=sys.stderr)
            raw_rows_sample_printed = True
        all_games.extend(filter_team_games(rows, config.TEAM_CODE))
        time.sleep(1)

    with open(config.GAMES_JSON, "w", encoding="utf-8") as f:
        json.dump(all_games, f, ensure_ascii=False, indent=2)

    print(f"총 {len(all_games)}경기 저장됨 → {config.GAMES_JSON}")


if __name__ == "__main__":
    main()
