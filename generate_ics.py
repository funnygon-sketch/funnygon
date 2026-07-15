"""
_games.json + _holidays.json 을 읽어 하나의 ICS 파일로 합칩니다.
- 경기 이벤트 (홈/원정)
- 홈경기 티켓팅 오픈 예상 이벤트 (경기 N일 전, 예상 시각 안내)
- 공휴일 이벤트 (종일)
"""
import json
import os
from datetime import datetime, timedelta

from icalendar import Calendar, Event, Alarm

import config


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def add_game_event(cal: Calendar, game: dict):
    date_str = game["date"]  # YYYYMMDD
    time_str = game.get("time", "18:30").replace(":", "")
    dt = datetime.strptime(date_str + time_str[:4], "%Y%m%d%H%M")

    ev = Event()
    label = "홈" if game["is_home"] else "원정"
    ev.add("summary", f"[한화이글스] {label}경기 ({game.get('stadium','')})")
    ev.add("dtstart", dt)
    ev.add("dtend", dt + timedelta(hours=3, minutes=30))
    ev.add("uid", f"game-{game['game_id']}@kbo-calendar")
    ev.add("description", f"경기 ID: {game['game_id']}")

    alarm = Alarm()
    alarm.add("action", "DISPLAY")
    alarm.add("trigger", timedelta(hours=-2))
    ev.add_component(alarm)

    cal.add_component(ev)


def add_ticket_event(cal: Calendar, game: dict):
    if not game["is_home"]:
        return  # 원정 경기는 상대 구단 규정이 달라 제외

    date_str = game["date"]
    game_date = datetime.strptime(date_str, "%Y%m%d")
    open_dt = game_date - timedelta(days=config.TICKET_OPEN_DAYS_BEFORE)
    open_dt = open_dt.replace(
        hour=config.TICKET_OPEN_HOUR, minute=config.TICKET_OPEN_MINUTE
    )

    links = "\n".join(f"{name}: {url}" for name, url in config.TICKET_LINKS.items())
    ev = Event()
    ev.add("summary", f"[티켓팅 예상] {game_date.strftime('%m/%d')} 한화 홈경기 예매 오픈")
    ev.add("dtstart", open_dt)
    ev.add("dtend", open_dt + timedelta(minutes=30))
    ev.add("uid", f"ticket-{game['game_id']}@kbo-calendar")
    ev.add(
        "description",
        f"예상 오픈 시각입니다 (경기 {config.TICKET_OPEN_DAYS_BEFORE}일 전 기준). "
        f"구단 공지에 따라 하루 정도 차이가 날 수 있으니 예매 전 공식 채널에서 "
        f"최종 확인하세요.\n\n{links}",
    )

    alarm = Alarm()
    alarm.add("action", "DISPLAY")
    alarm.add("trigger", timedelta(minutes=-30))
    ev.add_component(alarm)

    cal.add_component(ev)


def add_holiday_event(cal: Calendar, holiday: dict):
    d = datetime.strptime(holiday["date"], "%Y%m%d").date()
    ev = Event()
    ev.add("summary", holiday["name"])
    ev.add("dtstart", d)
    ev.add("dtend", d + timedelta(days=1))
    ev.add("uid", f"holiday-{holiday['date']}-{holiday['name']}@kbo-calendar")
    cal.add_component(ev)


def main():
    games = load_json(config.GAMES_JSON)
    holidays_path = config.GAMES_JSON.replace("_games.json", "_holidays.json")
    holidays = load_json(holidays_path)

    cal = Calendar()
    cal.add("prodid", "-//kbo-calendar//github.io//")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", f"{config.TEAM_NAME} 일정 + 공휴일")
    cal.add("x-wr-timezone", "Asia/Seoul")

    for game in games:
        add_game_event(cal, game)
        add_ticket_event(cal, game)

    for holiday in holidays:
        add_holiday_event(cal, holiday)

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    with open(config.ICS_PATH, "wb") as f:
        f.write(cal.to_ical())

    print(f"ICS 생성 완료 → {config.ICS_PATH} (경기 {len(games)}건, 공휴일 {len(holidays)}건)")


if __name__ == "__main__":
    main()
