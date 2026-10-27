# orders.py 라우팅

대응 원본: [orders.py](../orders.py)

## 역할과 진입점

기본 카페·베이커리 DAG와 Day 05·06 실습·보고서가 공유하는 일반 Python 함수 모듈이다. 표준 라이브러리 `csv`, `json`, `pathlib.Path`만 사용하며, import 시 파일을 읽거나 결과를 저장하지 않는다. 직접 실행해도 함수 정의만 이루어진다.

## 함수별 경로

| 함수 서명 | 호출자 | 처리·하위 호출 | 반환값 |
| --- | --- | --- | --- |
| `read_orders(path="data/cafe_orders.csv")` | 기본 두 DAG의 `read()`, `bakery_day05_select.read_source()`, `bakery_book_taskflow.read(source_path)`, `book_reporting.make_report(...)`, `book_operations.make_daily_report(...)` | `open(path, encoding="utf-8-sig", newline="")` → `csv.DictReader` → `list` | CSV 행 사전의 리스트 |
| `paid_orders(rows)` | 기본 두 DAG의 `keep_paid(rows)`, `reports.build_report(...)`, `bakery_book_taskflow.clean(...)` | 각 행의 `status == "paid"` 검사 → 새 리스트에 추가 | 결제된 행 리스트 |
| `summarize(rows)` | 기본 두 DAG의 `total(rows)`, `reports.build_report(...)`, `bakery_book_taskflow.summary(...)` | `int(quantity)`, `int(unit_price)` → 수량·수량×단가 누적 | `{"order_count": len(rows), "quantity": 정수, "revenue": 정수}` |
| `save_json(value, path)` | 카페 DAG `save(summary)`, `book_reporting.write_report(...)`, `bakery_book_files.report_from_snapshot(...)`, `bakery_book_taskflow.save(...)`, Day 06 Branch·Join의 `write_report`, Condition의 `deliver`, 동적 DAG의 `run_store` | `Path` → 부모 폴더 생성 → JSON 직렬화 → UTF-8 파일 쓰기 | 대상 경로 문자열 |

이 모듈의 함수들은 서로를 호출하지 않는다. 호출 순서는 DAG 또는 보고서 모듈이 결정한다.

```text
카페 read() ───────→ read_orders() ─────────────────────→ 카페 CSV
베이커리 read() ──→ read_orders("data/bakery_orders.csv") → 베이커리 CSV
각 keep_paid(rows) → paid_orders(rows)
각 total(rows) ────→ summarize(rows)
카페 save(summary) → save_json(summary, "outputs/day04-summary.json")

day05 select.read_source() → read_orders("data/bakery_orders.csv")
book_operations.make_daily_report(...) → read_orders(input_path) → reports.build_report
Day 06 branch / join / delivery / dynamic → save_json → 날짜별 JSON
book_reporting.make_report(...) → read_orders(source_path)
  → reports.build_report(...) → paid_orders(...) → summarize(...)
book_reporting.write_report(...) → save_json(..., run_path(run_id))
book_files.report_from_snapshot(...) → save_json(..., output_path)
book_taskflow의 read / clean / summary / save → 해당 공통 함수
```

## 입력·출력 계약

- 상대 경로는 현재 작업 디렉터리를 기준으로 한다. Compose에서는 `/opt/airflow/workshop`이다.
- `paid_orders`는 원본 리스트를 수정하지 않지만, 새 리스트 안의 행 사전은 원본과 같은 객체다.
- `summarize`는 결제 상태를 검사하지 않는다. 결제 매출을 얻으려면 먼저 `paid_orders`를 적용해야 한다. 반복과 `len`을 모두 사용하므로 일반 사용 경로의 입력은 리스트다.
- 빈 리스트의 집계는 세 항목 모두 `0`이다.
- `save_json`은 부모 폴더를 생성하고 기존 파일이 있으면 덮어쓴다. 한글을 그대로 보존하고, 들여쓰기 2칸과 마지막 줄바꿈을 사용한다.

## 예외와 수정 지점

별도 예외 처리는 없다. 파일 경로·권한 문제는 파일 I/O 예외로, 누락된 필수 열은 `KeyError`로, 정수로 변환할 수 없는 값은 `ValueError`로 호출자에게 전달된다.

CSV 읽기 방식은 `read_orders`, 결제 기준은 `paid_orders`, 합산 공식·결과 키는 `summarize`, 파일 형식은 `save_json`에서 변경한다. 카페·베이커리 DAG와 보고서 모듈에 영향을 주는 공통 코드다. 저장 목적지는 호출하는 DAG나 [book_reporting.py](book_reporting.py.md)에서 지정한다. 날짜 선택·목표 비교는 [reports.py](reports.py.md), 실행별 경로 생성은 `book_reporting.run_path`의 책임이다.
