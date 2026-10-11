# game2 × 3-3game 픽셀 그래픽 이식 보고서

## 1. 작업 목적 및 소스

- 실행 및 수정 대상: 사용자가 업로드한 `game2-main(1).zip`
- 그래픽 제공원: 사용자가 업로드한 `3-3game-main.zip`
- 접근 범위: 그래픽 리소스, Canvas 바닥·장식 렌더링, 이미지 매니페스트 및 UI 장식
- 수정하지 않은 핵심 코드: `app.py`, `engine.py`, `content.py`, `school.py`, `storage.py`, 저장·선택 데이터와 이벤트 ID
- 학교 좌표·교실 목록·마을 6개 구역·충돌·출입·길찾기 로직은 기존 game2를 유지함

## 2. 실제 교체 결과

| 종류 | 변환 수 | 구현 방식 |
|---|---:|---|
| 플레이어 | 6 | donor `avatars.png`에서 4방향 × 4프레임 크롭 |
| 교사 | 19 | donor `npcs.png` 19개 스타일을 game2 4×4 시트 계약에 맞게 배치 |
| 건물 | 13 | donor `buildings.png` 및 `school.png`의 대응 장면을 추출·리사이즈 |
| 실내 | 13 | donor `terrain.png`, `furniture.png`, `facilities.png`, `details.png`, `environment.png`의 합성 |
| 학교 복도 | 4 | 타일 텍스처와 donor 소품으로 복도 배경 제작 |
| 학교 교실 및 특별실 | 12 | donor 가구·시설·칠판·창문 등 합성 |
| 학교 외관 | 1 | donor ㄱ자 붉은 벽돌 학교 일러스트로 교체 |
| 나무 | 3 | donor 환경 아틀라스의 나무 추출 및 변형 |
| **기존 그래픽 이미지 합계** | **71** | **활성 원본 PNG 전수 교체, 이름·규격 그대로 유지** |

추가로 런타임 donor 리소스 7종을 연결했습니다: 32px 타일 시트, 분수, 벤치, 화단, 가로등, 다이어리 UI 장식, UI 아이콘. 생성 매핑 원장: `docs/3-3game_에셋_매핑.json`.

기존 PNG 71개는 `frontend/assets/legacy_game2/`에 보관하여 롤백할 수 있습니다. 현재 게임 렌더러에서는 활성 파일의 새 에셋을 참조합니다. 특히 마을 잔디·도로·강 수면을 donor의 `terrain.png` 타일로 변경했고, 광장 분수·가로등·벤치·화단은 donor 오브젝트를 사용합니다. 대화창·브랜드 문양은 donor의 UI 시트를 활용했습니다.

## 3. 검증

- `python tools/audit_asset_migration.py`: **통과**. 원본 보관 71개, 활성 변환 71개, 크기 및 SHA 검사 이상 없음.
- `python tools/test_donor_integration.py`: **Chromium Canvas 시뮬레이션 통과**. 마을 광장·상점가·일터·1층 학교 복도·교실·실내 6종 화면과 768px 가로폭 태블릿 화면. 브라우저 렌더링 중 JS pageerror 및 HTTP 응답 오류 없음. 스크린샷은 `docs/asset_migration_screenshots/` 참조.
- `node --check frontend/game.js`: **통과**.
- `python -m compileall -q app.py engine.py content.py school.py storage.py`: **통과**.
- 활성 테스트 4종(`test_engine.py`, `test_school.py`, `test_storage.py`, `test_l_school_layout.py`): **22개 통과**.
- `python -m unittest discover -s tests -v`: **25개 중 22개 통과, 3개 불러오기 오류**. 오래된 `test_classroom.py`, `test_journey.py`, `test_renewal.py`가 현재 `engine.py`에 없는 `handle`, `NPC`, `CHECKLIST` 이름을 가져오므로 테스트 자체가 실행되지 않습니다. 변경 대상이 아닌 기존 테스트·엔진 호환성 문제이며 이번 그래픽 이식에서 수정하지 않았습니다.

**검증 방식 주의:** 현재 실행 환경은 localhost/file URL 브라우저 탐색이 차단되어 있습니다. Chromium 테스트에서는 실제 HTML/CSS/JS를 주입하고 업로드 ZIP에서 만든 PNG 바이트를 `Image.src`에 data URI로 주입했습니다. Canvas 렌더링은 실제 Chromium이 실행했지만 Streamlit의 HTTP 정적 파일 제공 기능은 직접 검증하지 않았습니다.

## 4. 미완료 및 한계

- `3-3game/npcs.png`는 **전면 대기 표정만** 있습니다. 교사 19종은 전체 교체되었으나 4방향의 실제 고유 측면/후면 애니메이션은 없고, 좌우 반전 및 약한 프레임 위치 차이로 호환성만 맞췄습니다.
- 건물과 실내는 3-3game 에셋을 재조합한 게임용 레이아웃입니다. 실제 서라벌여중의 층별 도면과 1:1 실측은 검증하지 않았습니다.
- UI의 기능·정보 배치를 유지하도록 donor 다이어리 테두리 및 아이콘만 적용했습니다. 모든 글자 UI를 별도 PNG 이미지로 대체한 것은 아닙니다.
- 실제 iPad Safari/Android Chrome, Streamlit Cloud 배포, 실 Google Sheets 인증 및 동시 다중 학급 환경은 테스트하지 않았습니다.
- donor 에셋 원본의 외부 배포 라이선스는 ZIP에 명시적으로 확인되는 조건만을 기준으로 판단할 수 있습니다. 공개 배포 전에 에셋 사용 권한을 재확인해야 합니다.
- 학생 20분 전체 플레이 및 선택지 전체 종단 간 검증은 이 그래픽 이식 검사 범위 밖입니다. Python 엔진과 저장 코드는 수정하지 않았습니다.

## 5. 실행 및 재생성

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

별도 보유한 donor 저장소를 사용해 그래픽 이미지를 다시 만들려면 (위 두 저장소의 폴더가 나란히 있는 경우):

```bash
python tools/migrate_3_3_assets.py ../3-3game-main
python tools/audit_asset_migration.py
python tools/test_donor_integration.py
```

`test_donor_integration.py`는 Playwright/Chromium/Pillow가 필요합니다. 실제 브라우저 탐색이 불가능할 때에도 PNG 이미지를 내장하여 Canvas 렌더링을 점검합니다. 이 테스트는 Streamlit 실행을 대신하지 않습니다.

**중요:** 기존 `tools/generate_school_assets.py` 등 게임2의 예전 에셋 생성기를 실행하면 이번 그래픽이 덮어써질 수 있습니다. 반드시 백업·변환 전후를 비교하세요.
