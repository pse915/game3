# 사건·선택 변경표

기존 사건·선택 ID를 유지했습니다. 원문과 수정 대사는 `V5_STORY_DATA.json`에서 전체 확인할 수 있습니다. 선택 결과는 `education.py`와 서버의 `apply`에서 계산하고, 화면·일지·엔딩에 반영합니다.

| ID | 기존 선택 | 수정 선택 | 학습 주제 | 즉시 마을 지표 | 다음 생애 지표 |
|---|---|---|---|---|---|
| `care/share` | 돌봄을 함께 나누는 당번 제안 | 돌봄을 함께 나누는 당번 제안 | workcare, elder_care, aging | {"care": 1, "exchange": 2, "budget": -1} | {} |
| `care/flex` | 근무시간 조정을 요청 | 근무시간 조정을 요청 | workcare, aging, elder_care | {"care": 1, "jobs": 2, "budget": -2} | {} |
| `care/service` | 공공 돌봄서비스 신청을 돕는다 | 공공 돌봄서비스 신청을 돕는다 | elder_care, policy, aging, workcare | {"care": 3, "budget": -3} | {} |
| `nursery/together` | 어린이·어르신 교류 공간 제안 | 어린이·어르신 교류 공간 제안 | low_birth, generations, education_cost, housing, employment | {"learning": 1, "exchange": 2, "budget": -3} | {"learning": 1} |
| `nursery/retrain` | 교직원 전환 교육을 알아본다 | 교직원 전환 교육을 알아본다 | low_birth, labor, education_cost, housing, employment | {"jobs": 1, "budget": -2} | {"jobs": 2} |
| `nursery/expense` | 가정의 양육비 부담을 조사 | 양육·교육비 조사와 지원 시범사업 | education_cost, low_birth, housing, employment | {"learning": 1, "budget": -2} | {"learning": 2} |
| `labor/retrain` | 세대별 기술 교육을 연결 | 세대별 기술 교육을 연결 | labor, generations, aging | {"jobs": 1, "budget": -2} | {"economy": 2, "jobs": 1} |
| `labor/hire` | 고령 친화 일자리를 제안 | 고령 친화 일자리를 제안 | aging, labor, generations | {"jobs": 2, "exchange": 1, "budget": -2} | {} |
| `labor/rest` | 안전하고 쉬기 좋은 공간 마련 | 안전하고 쉬기 좋은 공간 마련 | aging, labor, generations | {"jobs": 2, "care": 1, "budget": -2} | {"economy": 1} |
| `policy/youth` | 청년 주거·일자리 지원 | 청년 주거·일자리 지원 | employment, housing, policy | {"jobs": 1, "learning": 1, "budget": -3} | {"economy": 2} |
| `policy/balance` | 돌봄·일가정 양립 지원 | 돌봄·일가정 양립 지원 | workcare, education_cost, policy | {"care": 2, "learning": 1, "budget": -3} | {} |
| `policy/aging` | 고령자 의료·여가·안전 지원 | 고령자 의료·여가·안전 지원 | aging, elder_care, policy | {"care": 2, "exchange": 1, "budget": -3} | {} |
| `policy/together` | 세대 협력·공동체 사업 | 세대 협력·공동체 사업 | generations, policy | {"exchange": 3, "budget": -2} | {"economy": 1} |

핵심 세 사건에는 주민 3명의 관점을 추가했습니다. `test_education.py`는 모든 핵심 선택 조합 108개, 노후 조합 81개에서 필수 학습·결과·엔딩·복원을 검증합니다. `browser_qa.cjs interaction`은 세 입장을 듣기 전 선택 잠금과 화면 선택 후 엔진·저장·화면 복원을 검증합니다.
