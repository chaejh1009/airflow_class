# dags/bakery_book_branch.py 라우팅

대응 원본: [dags/bakery_book_branch.py](../../dags/bakery_book_branch.py)

## 역할과 진입점

결제 주문 유무에 따라 저장과 빈 주문 경로 중 하나를 선택한다. 모듈의 `with DAG(...)`로 `bakery_book_branch`를 생성한다. `schedule=None`, `catchup=False`, 시작은 `2026-01-01 Asia/Seoul`이며 `max_active_runs`는 명시하지 않는다. 문자열 Param `report_date`의 기본값은 `2026-10-05`이며 enum 제한은 없다.

### `read_day(**context)`

`make_daily_report(params["report_date"])`를 반환한다. Task ID는 `read_report`다.

### `pick_path(**context)`

`read_report`의 반환값 XCom을 `choose_report_task`에 넘겨 `write_report` 또는 `no_orders`를 반환한다. Task ID `choose`의 `BranchPythonOperator`가 선택하지 않은 분기를 skip한다.

### `write_report(**context)`

`read_report` XCom을 읽어 `orders.save_json`으로 `outputs/book/day06/branch/<report_date>.json`에 저장하고 경로를 반환한다.

### `no_orders(**context)`

날짜와 `status="no_orders"`를 담은 사전을 출력하고 반환한다. 파일을 만들지 않는다.

```text
read_report → choose → write_report → 날짜별 JSON
                     → no_orders → 상태 사전
```

## 결과와 수정 지점

기본 날짜는 결제 3건·매출 `14000`으로 저장 분기를 선택한다. `2026-10-07`은 빈 주문 분기다. 목표 미달인 `2026-10-06`도 결제 주문이 있어 저장한다. 같은 날짜로 재실행하면 파일을 덮어쓴다. 분기 기준은 [book_operations.choose_report_task](../book_operations.py.md), 경로는 `write_report`, Task 연결은 모듈 수준 정의에서 변경한다.
