# book_operations.py 라우팅

대응 원본: [book_operations.py](../book_operations.py)

## 역할과 진입점

Day 06의 재시도·실패 콜백·분기·조건·동적 DAG가 공유하는 함수 모듈이다. `orders.read_orders`와 `reports.build_report`로 보고서를 만들며, 모듈 import에 `requests`가 필요하다. 직접 실행용 진입점은 없다.

### `first_attempt(try_number)`

시도 번호가 `1`인지 반환한다. `attempt_report`의 일시 실패 조건에 사용한다.

### `make_daily_report(report_date, input_path="data/bakery_orders.csv", min_revenue=10000)`

`read_orders(input_path)` → `build_report(rows, report_date, min_revenue)`로 날짜·결제 상태를 적용한 보고서를 반환한다. `attempt_report`, Branch·Join DAG의 `read_day`, Condition DAG의 `check_delivery`, 동적 DAG의 `run_store`가 호출한다.

### `attempt_report(report_date, simulate_failure, try_number, always_fail=False)`

`always_fail`이 참이거나 `simulate_failure`가 참이고 첫 시도이면 `RuntimeError("temporary order error.")`를 발생시킨다. 나머지는 `make_daily_report(report_date)`를 반환한다. 재시도 자체는 Retry·Alert DAG의 Operator가 담당한다.

### `notice_text(dag_id, task_id)`

`<dag_id>/<task_id> failed` 문자열을 만들어 `failure_notice`에 제공한다.

### `failure_notice(context)`

`context["task_instance"]`의 DAG·Task·실행 ID와 `context.get("exception", "unknown error")`의 문자열을 읽는다. `text`, `run_id`, `error`, `callback_test` 사전을 구성하고 안내 문자열 및 `FAILURE_NOTICE <JSON>`을 출력한 뒤 사전을 반환한다.

### `discord_failure_notice(context)`

먼저 `failure_notice(context)`로 실패 정보를 로그에 남긴다. 현재 `webhook_url`은 빈 문자열이므로 `ValueError`가 발생하고 외부 전송은 이루어지지 않는다. URL을 설정하면 `requests.post(webhook_url, json={"content": JSON 문자열}, timeout=10)` → `raise_for_status()` 후 payload를 반환한다. 현재 Alert DAG의 `on_failure_callback`에 이 함수가 연결되어 있다. 실제 웹훅 비밀값을 저장소에 커밋하지 않는다.

### `choose_report_task(report)`

`order_count > 0`이면 `write_report`, 아니면 `no_orders` Task ID를 반환한다. Branch·Join DAG의 `pick_path`가 호출하며 목표 달성 여부는 검사하지 않는다.

### `finish_payload(report_date)`

`{"report_date": report_date, "status": "finished"}`를 반환한다. Join DAG의 `finish`가 사용한다.

### `can_deliver(report)`

`order_count > 0 and target_met`을 반환한다. Condition DAG가 거짓인 결과를 `AirflowSkipException`으로 바꾼다.

### `dag_name(store)`

`<store>_book_daily` 문자열을 반환한다. 동적 DAG의 ID와 모듈 전역 등록 이름을 구성한다.

## 입출력과 수정 지점

보고서 함수는 파일을 저장하지 않으며 CSV·열·수치 변환 오류를 호출자에게 전달한다. 재시도 조건은 `attempt_report`, 알림 내용은 `failure_notice`, 전송은 `discord_failure_notice`, 분기 조건은 `choose_report_task`·`can_deliver`에서 변경한다. 저장 경로와 Task 재시도·연결은 각 DAG에서 정의한다.
