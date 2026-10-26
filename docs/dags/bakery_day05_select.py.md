# dags/bakery_day05_select.py 라우팅

대응 원본: [dags/bakery_day05_select.py](../../dags/bakery_day05_select.py)

## 역할과 진입점

베이커리 주문을 업무 날짜로 선택하고 전체·선택·제외 건수와 선택 내역을 확인하는 TaskFlow DAG다. 마지막의 `bakery_day05_select()` 호출이 Task 관계를 구성한다.

| 설정 | 값 |
| --- | --- |
| DAG ID | `bakery_day05_select` |
| schedule / catchup / max_active_runs | `None` / `False` / `1` |
| start_date | `2026-01-01`, `Asia/Seoul` |
| tags | `bakery`, `day05` |
| Param `report_date` | 기본 `2026-10-05`, 허용값 `2026-10-05`, `2026-10-06`, `2026-10-07` |
| Param `duplicate_first` | 기본 `False`, 타입 `boolean` |

## bakery_day05_select()

내부 Task를 정의하고 `evidence(select(read_source()))`로 `read_source → select → evidence`를 연결한다. TaskFlow 반환값이 XCom으로 전달된다.

## read_source()

`orders.read_orders("data/bakery_orders.csv")`로 전체 주문을 읽는다. 실행 컨텍스트의 `params.duplicate_first`가 참이면 `rows[0].copy()`를 마지막에 추가한다. 빈 CSV에서 복제를 활성화하면 `IndexError`가 발생한다.

## select(rows)

컨텍스트에서 `report_date`를 읽고 `workflow_day05.select_day(rows, report_date)`의 packet을 반환한다. 날짜만 선택하므로 대상 날짜의 취소 주문도 포함한다. 집계·JSON 저장은 하지 않는다.

## evidence(packet)

`report_date`, `source_count`, `selected_count`, `rejected_count`와 `order_ids`를 로그에 출력하고 `packet["order_ids"]`를 반환한다. 최종 결과는 현재 구현에서 주문 행 사전의 리스트다. `order_ids`라는 이름과 달리 ID 문자열만 담지 않는다.

## 현재 결과와 주의점

기본 날짜 `2026-10-05`에서는 전체 8행, 선택 4행, 제외 4행이다. `duplicate_first=True`에서는 전체 9행, 선택 5행, 제외 4행이지만 현재 중복 오류가 발생하지 않는다.

[workflow_day05.py](../workflow_day05.py.md)는 ID 문자열을 `order_ids` 안의 행 사전과 비교하고 `order_ids.append(row)`로 행을 추가한다. 따라서 일반 CSV 문자열 ID의 중복을 감지하지 못한다. 중복 거부를 안내하는 실습 주석과 실제 구현에 차이가 있다.

입력은 `read_source`, 허용 날짜·복제 설정은 `Param`, 선택 처리와 packet 구조는 `workflow_day05.select_day`, 확인 로그와 최종 반환값은 `evidence`에서 변경한다. 파일·필수 키 오류는 별도 처리 없이 Task 실패로 전달된다.
