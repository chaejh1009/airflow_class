# dags/bakery_book_condition.py 라우팅

대응 원본: [dags/bakery_book_condition.py](../../dags/bakery_book_condition.py)

## 역할과 진입점

결제 주문이 있고 목표 매출을 달성한 경우에만 보고서를 저장한다. 모듈의 `with DAG(...)`로 `bakery_book_condition`을 생성한다. `schedule=None`, `catchup=False`, 시작은 `2026-01-01 Asia/Seoul`, tags는 `day6`, `bakery`이며 `max_active_runs`는 명시하지 않는다. 문자열 Param `report_date`는 기본 `2026-10-05`이며 enum 제한은 없다.

### `check_delivery(**context)`

`make_daily_report(params["report_date"])`로 보고서를 만든다. `can_deliver(report)`가 거짓이면 `AirflowSkipException("delivery condition not met")`을 발생시키고, 참이면 보고서를 반환한다. 기본 목표는 `10000`이다.

### `deliver(**context)`

`check_delivery`의 반환값 XCom을 읽어 `orders.save_json`으로 `outputs/book/day06/delivery/<report_date>.json`에 저장하고 경로를 반환한다.

```text
check_delivery → deliver → observed (EmptyOperator, none_failed)
```

## 결과와 수정 지점

`2026-10-05`는 매출 `14000`으로 저장한다. `2026-10-06`은 매출 `8500`, `2026-10-07`은 주문 0건이므로 검사와 후속 `deliver`가 skipped다. `observed`는 `trigger_rule="none_failed"`이어서 상위 `deliver`가 skipped여도 실행할 수 있다. 실제 실패가 전파되는 경우와 구분한다. 같은 날짜 파일은 덮어쓴다. 조건은 [book_operations.can_deliver](../book_operations.py.md), skip은 `check_delivery`, 저장 위치는 `deliver`, 관찰 규칙은 `observed`에서 변경한다.
