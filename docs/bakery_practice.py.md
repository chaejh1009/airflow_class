# bakery_practice.py 라우팅

대응 원본: [bakery_practice.py](../bakery_practice.py)

## 역할과 진입점

표준 라이브러리 `csv`를 사용하는 베이커리 실습 함수 모듈이다. 현재 프로젝트 안에서 이 모듈을 import하는 코드는 없으며, DAG와 연결되어 있지 않다. 최상위 함수 호출이나 `__main__` 진입점이 없으므로 외부에서 함수를 호출해야 데이터 처리가 시작된다.

## 함수별 경로

| 함수 서명 | 현재 파일 내 호출자 | 처리·하위 호출 | 반환값 |
| --- | --- | --- | --- |
| `read_first_order(path)` | 없음 | 고정 경로 CSV 열기 → `csv.DictReader` → 전체 행 리스트 → `rows[0]` | 첫 행 사전 |
| `read_bakery_orders(path="data/bakery_orders.csv")` | 없음 | 고정 경로 CSV 열기 → `csv.DictReader` → `list` | 전체 행 사전 리스트 |
| `is_paid_order(row)` | 없음 | `row["status"] == "paid"` | `bool` |
| `select_paid_orders(rows)` | `summarize_bakery(rows)` | `status == "paid"`를 직접 검사 → 새 리스트에 추가 | 결제 행 리스트 |
| `order_amount(row)` | `summarize_bakery(rows)` | 수량·단가를 `int`로 변환한 뒤 곱함 | 주문 금액 정수 |
| `summarize_bakery(rows)` | 없음 | `select_paid_orders` → 수량 누적·`order_amount` 누적 | `{"order_count": len(selected), "quantity": 정수, "revenue": 정수}` |

## 실제 호출 흐름

외부 호출자가 읽기와 집계를 연결하면 다음 경로를 따른다. 아래 최상위 연결은 현재 파일에서 자동 실행되는 코드는 아니다.

```text
외부 호출자
  → read_bakery_orders() → data/bakery_orders.csv → rows
  → summarize_bakery(rows)
      → select_paid_orders(rows) → selected
      → selected 각 행의 quantity를 정수로 누적
      → order_amount(row) → 매출 누적
      → 집계 사전 반환

별도 호출 가능: read_first_order(path), is_paid_order(row)
```

현재 CSV를 연결하면 `{"order_count": 6, "quantity": 10, "revenue": 22500}`을 반환한다. JSON 저장 함수나 파일 출력 동작은 없다.

## 주석·서명과 실제 구현의 차이

- `read_first_order(path)`와 `read_bakery_orders(path=...)`는 전달받은 `path`를 사용하지 않는다. 두 함수 모두 `data/bakery_orders.csv`를 직접 연다. 다른 경로를 전달해도 읽는 파일은 바뀌지 않는다.
- `select_paid_orders`의 실습 주석은 판단 함수 사용을 안내하지만, 실제로는 상태 문자열을 직접 비교한다. 따라서 `is_paid_order`를 변경해도 현재 선택·집계 결과에는 반영되지 않는다.
- 취소 주문 집계를 요청하는 주석이 있지만, 취소 건수·목록을 집계하는 함수는 구현되어 있지 않다.

## 경계 조건과 수정 지점

CSV는 현재 작업 디렉터리 기준으로 열고 `utf-8-sig`, `newline=""`를 사용한다. 빈 데이터의 첫 행 조회는 `IndexError`를 일으키며, 빈 목록 집계는 모든 항목이 `0`이다. 누락된 키·잘못된 정수·파일 오류는 별도 처리 없이 호출자에게 전달된다.

읽기 경로를 바꾸려면 두 읽기 함수의 `open` 인자를 확인한다. 실제 결제 필터는 `select_paid_orders`, 금액 계산은 `order_amount`, 최종 결과 구조는 `summarize_bakery`에서 변경한다. 이 변경은 현재 두 Airflow DAG에 영향을 주지 않는다.
