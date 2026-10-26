# workflow_day05.py 라우팅

대응 원본: [workflow_day05.py](../workflow_day05.py)

## 역할과 진입점

[reports.py](reports.py.md)의 `filter_date`로 주문 날짜를 선택한 뒤 선택 전후 건수와 증거 데이터를 묶는 일반 Python 모듈이다. `bakery_day05_select` DAG의 `select` Task가 호출한다. 직접 실행용 진입점이나 파일 I/O는 없다.

### `select_day(rows, report_date)`

`filter_date(rows, report_date)`로 날짜가 일치하는 행을 고른다. 선택 행을 순회하며 `row["order_id"]`가 `order_ids`에 이미 있으면 `ValueError("duplicate id: " + order_id)`를 발생시키도록 비교한 뒤 `order_ids.append(row)`를 수행한다.

반환값은 다음 키를 가진 사전이다.

| 키 | 현재 구현의 값 |
| --- | --- |
| `report_date` | 요청 날짜 |
| `source_count` | 전체 입력 행 수 `len(rows)` |
| `selected_count` | 날짜가 일치하는 행 수 `len(selected)` |
| `rejected_count` | 전체 행 수와 선택 행 수의 차이 |
| `order_ids` | 선택된 행 사전의 목록 |
| `rows` | 날짜가 일치하는 행 사전의 목록 |

## 실제 호출 흐름

```text
bakery_day05_select.read_source → orders.read_orders → 베이커리 CSV 행
  → select → select_day(rows, report_date)
      → reports.filter_date → 날짜 선택 행
      → 건수 계산·order_ids 구성 → packet
  → evidence → 날짜·건수·packet["order_ids"] 출력 및 반환
```

## 주석과 실제 구현의 차이

`order_ids`라는 이름과 실습 주석은 ID 목록을 안내하지만, 실제 코드는 ID 문자열 대신 행 사전을 추가한다. 일반 CSV 입력의 `order_id`는 문자열이므로 문자열을 행 사전 목록에서 찾는 중복 검사는 작동하지 않는다. 같은 ID가 여러 번 나와도 해당 행이 모두 결과에 들어간다. `bakery_day05_select`의 `duplicate_first=True`를 사용해도 첫 행의 날짜가 선택 날짜와 일치하면 중복 행이 포함된 채 성공한다.

이 문서는 현재 구현을 기록한다. 중복 검사를 구현하려면 추가 대상을 `order_id`로 바꾸는 지점과 DAG의 `evidence` 출력 계약을 함께 확인해야 한다.

## 경계 조건과 수정 지점

결제 상태는 선택 조건에 포함되지 않는다. 날짜가 일치하는 취소 주문도 `rows`와 건수에 포함되며 금액 집계나 파일 저장은 하지 않는다. 선택 행이 없으면 `selected_count=0`, `rejected_count=source_count`, 두 목록은 빈 목록이다. `rows`와 `order_ids`는 서로 다른 리스트이지만 내부의 행 사전은 원본과 같은 객체다.

입력은 반복뿐 아니라 `len`을 사용할 수 있는 행 목록이어야 한다. 날짜 키 누락은 `filter_date`, 선택 행의 ID 키 누락은 `select_day`에서 `KeyError`를 발생시킨다. 날짜 조건은 `reports.filter_date`, 중복 검사와 반환 구조는 `select_day`, 입력 복제·Task 연결·출력은 DAG 파일에서 변경한다.
