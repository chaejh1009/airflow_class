# practice_day05.py 라우팅

대응 원본: [practice_day05.py](../practice_day05.py)

## 역할과 진입점

매출 기준 비교, 날짜 비교, 요약 사전 구성을 연습하는 독립 Python 함수 모듈이다. import나 직접 실행만으로 함수를 호출하지 않으며, 현재 다른 모듈이나 DAG에서 사용하지 않는다. 외부에서 함수를 호출해야 결과나 출력이 생긴다.

### `meets_target(revenue, limit_text)`

`int(limit_text)`로 기준 문자열을 정수로 변환하고 `revenue >= limit`을 반환한다. 기준과 같은 매출도 달성으로 판단한다. 파일 내부에서는 `show_targets`가 호출한다.

### `show_targets(limit_text)`

`meets_target(14000, limit_text)`와 `meets_target(8500, limit_text)`를 각각 호출하여 매출과 비교 결과를 두 줄로 출력한다. 명시적 반환값은 없어 `None`을 반환한다. 예를 들어 `show_targets("10000")`은 `14000 True`, `8500 False`를 출력한다.

### `date_matches(row, report_date)`

`row["order_date"] == report_date`의 비교 결과를 반환한다. 날짜 문자열을 그대로 비교하며, [reports.py](reports.py.md)의 `filter_date`가 이 함수를 호출하는 것은 아니다.

### `summary_card(report_date, totals)`

입력 날짜와 `totals`의 `order_count`, `quantity`, `revenue`를 새 사전에 담아 반환한다. 필터링이나 합산은 수행하지 않고, 입력에 있는 다른 키는 복사하지 않는다.

## 호출 흐름과 수정 지점

```text
외부 호출자 → show_targets(limit_text)
              → meets_target(14000, limit_text) → print
              → meets_target(8500, limit_text) → print

외부 호출자 → date_matches(row, report_date) → bool
외부 호출자 → summary_card(report_date, totals) → 요약 사전
```

기준 문자열 변환이 불가능하면 `ValueError`, 비교할 수 없는 매출 타입이면 `TypeError`, 날짜나 요약 키가 없으면 `KeyError`가 호출자에게 전달된다. 기준 비교는 `meets_target`, 예제 매출·출력은 `show_targets`, 날짜 비교는 `date_matches`, 요약 키 구성은 `summary_card`에서 변경한다. 보고서 모듈은 별도 구현을 사용하므로 이 실습 함수를 고쳐도 DAG의 보고서 동작은 바뀌지 않는다.
