# book_reporting.py 라우팅

대응 원본: [book_reporting.py](../book_reporting.py)

## 역할과 진입점

날짜별 주문 보고서 생성, 실행별 JSON 저장·읽기, 두 매장 보고서 결합을 제공하는 일반 Python 함수 모듈이다. [orders.py](orders.py.md)의 `read_orders`, `save_json`과 [reports.py](reports.py.md)의 `build_report`를 연결한다. 직접 실행용 진입점은 없고, 함수가 호출될 때만 파일 I/O가 발생한다.

### `make_report(report_date, source_path="data/bakery_orders.csv", min_revenue=10000)`

`orders.read_orders(source_path)`로 CSV를 읽어 `reports.build_report(rows, report_date, min_revenue)`에 전달한다. 날짜·결제 상태를 적용한 집계와 목표 달성 여부 사전을 반환한다. `write_report`, `bakery_book_operator.report_for_date`, `bakery_book_files.report_from_snapshot`이 호출한다.

### `run_path(run_id, filename="report.json")`

`urllib.parse.quote(run_id, safe="")`로 실행 ID를 URL 인코딩한 뒤 `outputs/practice/book/day05/<인코딩한 run_id>/<filename>` 문자열을 반환한다. `write_report`, 파일 복사 DAG의 Jinja 매크로, TaskFlow DAG의 `save` Task가 사용한다. 이 함수는 디렉터리를 만들지 않으며, `filename`은 가공 없이 붙인다.

### `write_report(report_date, run_id, min_revenue=10000, source_path="data/bakery_orders.csv")`

`make_report(report_date, source_path, min_revenue)` → `run_path(run_id)` → `orders.save_json(report, path)` 순서로 실행하고 저장 경로 문자열을 반환한다. 두 XCom DAG의 생성 함수 `produce_explicit`, `produce_return`이 호출한다. `make_report`와 비교하면 `source_path`와 `min_revenue`의 인자 위치가 다르다.

### `read_report(path)`

`Path(path).read_text(encoding="utf-8")` → `json.loads(...)`로 저장된 JSON을 Python 값으로 반환한다. 두 XCom DAG의 소비 함수 `consume_explicit`, `consume_return`이 사용한다. 보고서를 저장한 경로를 XCom으로 받은 뒤 이 함수로 내용을 읽는다.

### `join_shop_reports(cafe, bakery)`

TaskFlow DAG의 `join` Task가 호출한다. 매장별 `report_date`를 담은 `report_dates`, 두 입력 보고서를 담은 `shops`, 두 `revenue`의 합인 `total_revenue`를 반환한다. 날짜가 서로 달라도 결합하며 입력 보고서의 다른 필드나 목표 달성 여부를 계산하지 않는다. `shops`에는 전달된 사전 객체를 그대로 담는다.

## 실제 호출 흐름

```text
bakery_book_operator.make_report → report_for_date → make_report
bakery_book_files.make_report → report_from_snapshot → make_report
  make_report → orders.read_orders → reports.build_report → 보고서 사전

bakery_book_xcom_explicit / bakery_book_xcom_return
  make_report Task → write_report → make_report → run_path → orders.save_json
  경로 XCom → read_report Task → read_report → JSON 읽기

bakery_book_taskflow
  두 매장 summary → join → join_shop_reports
  → save → run_path(run_id, "combined.json") → orders.save_json
```

## 입출력과 수정 지점

상대 경로는 현재 작업 디렉터리를 기준으로 한다. Compose에서는 `/opt/airflow/workshop`이므로 결과가 호스트의 `outputs/practice/book/day05/`에도 나타난다. `save_json`이 부모 디렉터리를 만들고 같은 경로의 기존 파일을 덮어쓴다. 경로에는 DAG ID나 보고서 날짜가 추가되지 않으므로 같은 `run_id`와 `filename`을 전달하면 같은 파일을 가리킨다.

CSV·JSON 파일 오류, 잘못된 JSON, 필요한 보고서 키 누락과 잘못된 집계값은 별도 처리 없이 호출자에게 전달된다. 입력 기본 경로·보고서 연결은 `make_report`, 결과 위치는 `run_path`, 저장은 `write_report`, 읽기는 `read_report`, 매장 결합 구조는 `join_shop_reports`에서 변경한다.
