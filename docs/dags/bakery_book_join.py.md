# dags/bakery_book_join.py 라우팅

대응 원본: [dags/bakery_book_join.py](../../dags/bakery_book_join.py)

## 역할과 진입점

주문 유무로 분기한 뒤 완료 Task로 합류한다. 모듈의 `with DAG(...)`로 `bakery_book_join`을 생성한다. `schedule=None`, `catchup=False`, 시작은 `2026-01-01 Asia/Seoul`이며 `max_active_runs`는 명시하지 않는다. 문자열 Param `report_date`는 기본 `2026-10-05`이며 enum 제한은 없다.

### `read_day(**context)`

`make_daily_report(params["report_date"])`를 반환한다. Task ID는 `read_report`다.

### `pick_path(**context)`

`read_report` XCom을 `choose_report_task`에 넘긴다. `choose` Task는 `BranchPythonOperator`이며 반환된 Task ID의 분기를 선택한다.

### `write_report(**context)`

`read_report` XCom을 `outputs/book/day06/join/<report_date>.json`에 `orders.save_json`으로 저장하고 경로를 반환한다.

### `no_orders(**context)`

날짜와 `status="no_orders"` 사전을 반환한다. 파일 저장은 없다.

### `finish(**context)`

`finish_payload(params["report_date"])`가 만든 날짜·`status="finished"` 사전을 출력하고 반환한다.

```text
read_report → choose → write_report ─┐
                     → no_orders ────┴→ finish
```

## 결과와 수정 지점

`finish`의 `trigger_rule="none_failed_min_one_success"`는 상위 두 분기에 실패가 없고 하나 이상 성공하면 합류를 허용한다. 선택하지 않은 분기가 skipped여도 선택된 분기 성공 후 실행한다. 기본 날짜는 저장 분기, `2026-10-07`은 빈 주문 분기다. 같은 날짜 파일은 덮어쓴다. 분기·완료 내용은 [book_operations.py](../book_operations.py.md), 파일 위치는 `write_report`, 합류 규칙은 `finish` Operator에서 변경한다.
