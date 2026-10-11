# game3 v5 실행 및 검증

이 버전은 기존 학교·마을·캐릭터·그래픽과 Streamlit 실행 방식을 유지합니다. 초기 에셋 지연 로딩, 프레임에 따른 이동 간격 보정, 저출산·고령화 필수 사건과 선택 결과를 추가했습니다.

## 실행

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

교사용 화면은 `?mode=teacher`를 붙여 엽니다. 기존 `teacher_password` 설정을 사용합니다. Google Sheets는 기존 `sheet_id`, `gcp_service_account` 설정과 `sewol_port_v1` 워크시트를 그대로 사용합니다. 두 설정 중 하나만 있으면 오류를 표시하며 SQLite로 자동 전환하지 않습니다.

## 학생용 약 20분 운영안

| 시간 | 활동 |
|---|---|
| 0~2분 | 학교 정문에서 조작·지도 익히기, 학교 탐험은 선택 |
| 2~5분 | 직업과 주거 설계, 성인기로 이동 |
| 5~9분 | 보람의 저출산 사건: 세 주민의 입장과 대응 선택 |
| 9~13분 | 연주의 돌봄 사건: 독립 생활·노동·돌봄 관점 비교 |
| 13~16분 | 도준의 일손 부족 사건 및 하린의 예산안 |
| 16~20분 | 노년기 네 영역, 마을 후속 변화와 엔딩 확인 |

소감문 작성 시간은 위 20분과 별도입니다. 이 시간표는 수업 운영 제안이며, 실제 중학생의 소요 시간을 측정한 결과가 아닙니다. 이동이 오래 걸리면 지도에서 구역을 터치해 이동하세요. 사건 자체는 자동으로 건너뛰지 않습니다.

## 저장 호환성

스키마 번호 1, 사건·선택 ID, 학생·게임 식별자, 암호 정보, 리비전을 유지합니다. 새 지표는 기존 선택을 재생해 계산합니다. 기존 노년기 저장에서 빠진 `nursery`, `labor` 사건은 같은 주민에게 추가로 경험할 수 있습니다. 이미 완료한 옛 엔딩은 취소하지 않으며 사건을 추가 탐험할 수 있습니다. 자동 마이그레이션은 원본을 복제해 적용하므로 예전 JSON은 따로 보관할 수 있습니다.

수업 중 저장 오류가 나면 현재 상태는 세션에 남습니다. **현재 기록 저장 다시 시도**를 누르거나 JSON을 내려받으세요. 복원은 해당 학생·게임의 동일하거나 새로운 리비전만 허용합니다. 동일 학생이 여러 기기에서 동시에 같은 생애를 진행하는 상황은 지원을 보장하지 않습니다.

## 자동 검증

```bash
python -m unittest discover -s tests -v
python -m compileall -q app.py content.py education.py engine.py school.py storage.py
node --check frontend/game.js
python tools/build_qa_payload.py
node tools/browser_qa.cjs interaction
node tools/browser_qa.cjs final --soak
```

브라우저 검증은 설치된 Chrome과 Node.js를 사용합니다. 다른 환경에서는 `CHROME_PATH`, `QA_PYTHON`에 실행 파일의 절대 경로를 지정하세요. 예제의 기본 경로는 작업 당시 Windows 환경 경로입니다. Canvas는 실제 Chrome으로 실행하지만 HTTP 대신 테스트용 페이지와 원본 PNG 데이터로 주입합니다. `qa.invalid`는 테스트가 응답을 직접 제공하는 가상 주소로, 외부 서버가 아닙니다. 결과는 프로젝트 상위의 `work` 폴더에 기록됩니다.

`test_app.py`는 실제 Streamlit AppTest·엔진·SQLite를 사용하고, iframe 메시지 전달만 테스트 브리지로 대체합니다. 네트워크 제한 환경에서는 `QA_FAKE_EVENT_LOOP=1`로 AppTest의 사용하지 않는 이벤트 루프를 대체할 수 있습니다. 실제 HTTP/WebSocket 및 Google Sheets의 통신을 검증하는 설정은 아닙니다.

이전 엔진 API를 전제로 한 테스트 3개는 `docs/legacy_tests`에 보관했습니다. 현재 사건 엔진에 맞는 분기·저장·호스트 검증으로 대체했습니다.

## 추가 현장 확인

- 실제 iPad Safari·Android Chrome에서 길게 누르기, 회전, 이어하기
- 실제 Google Sheets 인증·할당량·네트워크 장애·30명 수업 접속
- 중학생 플레이 시간과 소감문의 개념 이해 확인

상세 근거와 측정값은 `V5_REPORT.md`, `qa_results`를 확인하세요.
