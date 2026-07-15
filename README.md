# 한화이글스 일정 + 티켓팅 + 공휴일 자동 캘린더

경기 일정, 홈경기 티켓팅 예상 오픈 시각, 공휴일을 매일 자동으로 갱신해서
`.ics` 구독 캘린더로 아이폰에 제공하는 프로젝트입니다.

## 폴더 구조
```
kbo-calendar/
├── scripts/
│   ├── config.py          # 팀 코드, API 키, 티켓팅 규칙 설정
│   ├── crawl_kbo.py       # KBO 경기 일정 수집
│   ├── fetch_holidays.py  # 공휴일 수집 (공공데이터포털)
│   └── generate_ics.py    # 위 데이터를 .ics 파일로 합침
├── docs/                  # GitHub Pages로 서빙되는 출력 폴더 (ics 파일 위치)
└── .github/workflows/update-calendar.yml   # 매일 자동 실행
```

## 처음 설정하는 방법

### 1. GitHub 저장소 만들기
이 폴더를 새 GitHub 저장소로 올리세요 (public 이어야 GitHub Pages 무료 사용 가능).

```bash
cd kbo-calendar
git init
git add .
git commit -m "init"
git remote add origin https://github.com/<본인아이디>/kbo-calendar.git
git push -u origin main
```

### 2. 공휴일 API 키 발급
1. https://www.data.go.kr/data/15012690/openapi.do 에서 **특일 정보** API 활용 신청 (즉시 승인)
2. 발급받은 서비스키를 저장소 **Settings → Secrets and variables → Actions → New repository secret**에
   이름 `HOLIDAY_API_KEY`로 등록

### 3. GitHub Pages 켜기
저장소 **Settings → Pages → Source**에서 `main` 브랜치의 `/docs` 폴더를 선택하세요.
잠시 후 `https://<본인아이디>.github.io/kbo-calendar/hanwha.ics` 로 파일이 공개됩니다.

### 4. 수동으로 한 번 실행해보기
**Actions** 탭 → `Update KBO calendar` → `Run workflow` 버튼으로 즉시 실행해서
정상적으로 `docs/hanwha.ics`가 생성/커밋되는지 확인하세요.

### 5. 아이폰에서 구독하기
설정 → 캘린더 → 계정 → 계정 추가 → 기타 → **구독 캘린더 추가**
→ 위 URL 입력 → 저장

이제 매일 자동으로 갱신된 일정이 아이폰 캘린더에 반영됩니다.

## KBO 크롤러가 빈 결과를 반환할 경우 (중요)

`scripts/crawl_kbo.py`는 KBO 사이트의 비공식 AJAX 엔드포인트
(`/ws/Schedule.asmx/GetScheduleList`)를 호출합니다. 이 요청 형식은
제가 실제 KBO 서버에 접근해 검증한 것이 아니라 공개된 참고 자료를 바탕으로
작성했습니다 — KBO가 파라미터를 바꾸거나 세션/쿠키를 요구하면 빈 결과가 나올 수 있습니다.

**직접 확인하는 방법**:
1. 크롬에서 https://www.koreabaseball.com/Schedule/Schedule.aspx 접속
2. 개발자 도구(F12) → Network 탭 → 월 이동 버튼 클릭
3. `GetScheduleList` 요청을 찾아서 **Payload**(요청 파라미터)와 **Response**(응답 형식)를 확인
4. `scripts/crawl_kbo.py`의 `payload` 딕셔너리와 `fetch_month()`의 파싱 부분을
   실제 응답 구조에 맞게 수정

응답 구조를 캡처해서 보여주시면 파싱 코드를 정확히 맞춰드릴 수 있습니다.

## 주의사항
- KBO 데이터는 개인적/비상업적 용도로만 사용하세요. 짧은 시간에 과도한 요청을 보내지 않도록
  월별 요청 사이에 1초 딜레이를 넣어뒀습니다.
- 티켓팅 오픈 시각은 "경기 7일 전 오전 11시" 규칙으로 **예측**한 값입니다.
  실제 공지와 하루 정도 차이가 날 수 있으니 예매 직전엔 반드시 공식 채널을 확인하세요
  (`scripts/config.py`의 `TICKET_OPEN_DAYS_BEFORE` 값으로 조정 가능).
- 아이폰 구독 캘린더는 실시간 동기화가 아니라 iOS가 자체적으로 몇 시간~하루 주기로 갱신합니다.
