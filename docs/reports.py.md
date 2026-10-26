# reports.py 라우팅

대응 원본: [reports.py](../reports.py)

## 역할과 진입점

주문 목록에서 요청 날짜와 결제 상태를 선택하고 매출 목표 달성 여부를 붙이는 일반 Python 함수 모듈이다. [orders.py](orders.py.md)의 `paid_orders`, `summarize`를 사용한다. 파일 읽기·저장이나 직접 실행용 진입점은 없으며, import만으로 집계하지 않는다.

### `filter_date(rows, report_date)`

`book_reporting.make_report`가 호출하는 `build_report`, `workflow_day05.select_day`, `bakery_book_taskflow` DAG의 `clean` Task가 사용한다. 각 행의 `order_date`가 `report_date`와 같은 행만 새 리스트에 추가하여 반환한다. 날짜 문자열을 그대로 비교하므로 날짜 형식 변환이나 범위 조회는 하지 않는다.

### `build_report(rows, report_date, min_revenue)`

[book_reporting.py](book_reporting.py.md)의 `make_report`가 호출한다. `filter_date(rows, report_date)` → `orders.paid_orders(selected)` → `orders.summarize(...)` 순서로 처리한다.

반환 사전은 `report_date`, `order_count`, `quantity`, `revenue`, `min_revenue`, `target_met`을 담는다. `target_met`은 집계 매출이 `min_revenue` 이상이면 `True`다. 기준값을 정수로 변환하지 않으므로 호출자가 숫자로 전달해야 한다.

## 실제 호출 흐름

```text
book_reporting.make_report(report_date, source_path, min_revenue)
  → orders.read_orders(source_path) → rows
  → build_report(rows, report_date, min_revenue)
      → filter_date(rows, report_date)
      → orders.paid_orders(selected)
      → orders.summarize(paid_rows)
      → 날짜·집계·목표 달성 여부 사전

workflow_day05.select_day → filter_date → 날짜 선택 행
bakery_book_taskflow.clean → filter_date → orders.paid_orders
```

## 입력·출력 계약과 수정 지점

`rows`는 CSV 열 이름을 키로 갖는 행 사전 목록이다. 날짜 선택은 원본 목록을 수정하지 않으며, 반환 목록의 행 사전은 원본과 같은 객체다. 날짜가 맞는 행이 없으면 집계 세 항목은 `0`이고, 목표 달성 여부는 `0 >= min_revenue`로 계산한다. 날짜 선택 후 결제 상태를 검사하므로 날짜가 다른 행은 결제·수량·단가 집계 대상에서 제외된다.

누락된 키는 `KeyError`, 정수로 바꿀 수 없는 수량·단가는 `ValueError`, 숫자와 비교할 수 없는 기준값은 `TypeError`를 호출자에게 전달한다. 날짜 선택 규칙은 `filter_date`, 보고서 키와 목표 비교는 `build_report`, 결제 판단·합산 공식은 `orders.py`에서 변경한다.
