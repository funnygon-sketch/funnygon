"""
공공데이터포털 '특일 정보' API(한국천문연구원 제공)로 공휴일 목록을 가져옵니다.
API 키는 data.go.kr에서 무료로 발급받아 환경변수 HOLIDAY_API_KEY로 넘겨주세요.
"""
import json
import sys

import requests

import config


def fetch_holidays(year: int) -> list[dict]:
    holidays = []
    for month in range(1, 13):
        params = {
            "serviceKey": config.HOLIDAY_API_KEY,
            "solYear": year,
            "solMonth": f"{month:02d}",
            "_type": "json",
            "numOfRows": 30,
        }
        try:
            res = requests.get(config.HOLIDAY_API_URL, params=params, timeout=10)
            res.raise_for_status()
            body = res.json()["response"]["body"]
            items = body.get("items", {})
            if not items:
                continue
            item = items.get("item", [])
            if isinstance(item, dict):
                item = [item]
            for it in item:
                holidays.append(
                    {
                        "date": str(it["locdate"]),  # YYYYMMDD
                        "name": it["dateName"],
                        "is_holiday": it.get("isHoliday") == "Y",
                    }
                )
        except Exception as e:
            print(f"[경고] {year}-{month:02d} 공휴일 조회 실패: {e}", file=sys.stderr)
    return holidays


def main():
    if not config.HOLIDAY_API_KEY:
        print("HOLIDAY_API_KEY 환경변수가 없습니다. data.go.kr에서 키를 발급받아 설정하세요.", file=sys.stderr)
        sys.exit(1)

    holidays = fetch_holidays(config.SEASON_YEAR)
    out_path = config.GAMES_JSON.replace("_games.json", "_holidays.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(holidays, f, ensure_ascii=False, indent=2)
    print(f"총 {len(holidays)}개 공휴일 저장됨 → {out_path}")


if __name__ == "__main__":
    main()
