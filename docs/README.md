# 코드 라우팅 문서

이 문서에서 라우팅은 실행 진입점부터 함수·Task 호출, 데이터 입력, 결과 출력까지 이어지는 경로를 뜻한다. HTTP URL 라우팅을 구현한 프로젝트는 아니다.

코드 파일별로 원본 경로를 유지하여 `docs/<원본 파일 경로>.md`에 1:1 대응 문서를 둔다. Python 코드 13개와 실행 설정 1개가 대상이며, CSV 입력·JSON 결과·캐시 파일은 별도 코드 문서를 만들지 않는다. 2026-10-26 추가된 Day 05 파일 9개를 포함한다.

| 원본 | 대응 문서 | 역할 |
| --- | --- | --- |
| [orders.py](../orders.py) | [orders.py.md](orders.py.md) | 공통 CSV 읽기·결제 선택·집계·JSON 저장 |
| [bakery_practice.py](../bakery_practice.py) | [bakery_practice.py.md](bakery_practice.py.md) | 베이커리 함수 실습 |
| [practice_day05.py](../practice_day05.py) | [practice_day05.py.md](practice_day05.py.md) | 목표·날짜 비교와 요약 카드 실습 |
| [reports.py](../reports.py) | [reports.py.md](reports.py.md) | 날짜 선택·결제 집계·목표 판정 |
| [workflow_day05.py](../workflow_day05.py) | [workflow_day05.py.md](workflow_day05.py.md) | 날짜별 선택 패킷과 건수·행 목록 |
| [book_reporting.py](../book_reporting.py) | [book_reporting.py.md](book_reporting.py.md) | 보고서 생성·실행별 저장·재읽기·매장 결합 |
| [dags/cafe_orders_basic.py](../dags/cafe_orders_basic.py) | [cafe_orders_basic.py.md](dags/cafe_orders_basic.py.md) | 카페 읽기 → 선택 → 집계 → 저장 DAG |
| [dags/bakery_orders_basic.py](../dags/bakery_orders_basic.py) | [bakery_orders_basic.py.md](dags/bakery_orders_basic.py.md) | 베이커리 읽기 → 선택 → 집계 DAG |
| [dags/bakery_day05_select.py](../dags/bakery_day05_select.py) | [bakery_day05_select.py.md](dags/bakery_day05_select.py.md) | 읽기 → 날짜 선택 → 증거 출력 DAG |
| [dags/bakery_book_operator.py](../dags/bakery_book_operator.py) | [bakery_book_operator.py.md](dags/bakery_book_operator.py.md) | PythonOperator·Param·Variable 보고서 DAG |
| [dags/bakery_book_files.py](../dags/bakery_book_files.py) | [bakery_book_files.py.md](dags/bakery_book_files.py.md) | BashOperator 복사 → PythonOperator 보고서 저장 DAG |
| [dags/bakery_book_xcom.py](../dags/bakery_book_xcom.py) | [bakery_book_xcom.py.md](dags/bakery_book_xcom.py.md) | 명시적 키·반환값 XCom으로 파일 경로를 전달하는 DAG 2개 |
| [dags/bakery_book_taskflow.py](../dags/bakery_book_taskflow.py) | [bakery_book_taskflow.py.md](dags/bakery_book_taskflow.py.md) | 매장별 병렬 집계 → 결합 → 실행별 저장 DAG |
| [docker-compose.yaml](../docker-compose.yaml) | [docker-compose.yaml.md](docker-compose.yaml.md) | Airflow 실행 환경과 경로 연결 |

## 전체 흐름

```text
docker-compose.yaml → airflow standalone → dags/의 DAG 정의
  cafe_orders_basic    → orders.py → data/cafe_orders.csv
                                  → outputs/day04-summary.json
  bakery_orders_basic  → orders.py → data/bakery_orders.csv
                                  → 집계 반환값 (저장 Task 없음)
  bakery_day05_select  → read_source → select → evidence
                         orders.py → workflow_day05.select_day → reports.filter_date
  bakery_book_operator → make_report Task → book_reporting.make_report
                         → reports.build_report → orders.py → 보고서 반환값
  bakery_book_files    → snapshot (CSV 복사) → make_report Task
                         → book_reporting.make_report(복사본) → orders.save_json
  bakery_book_xcom_explicit / bakery_book_xcom_return
                       → make_report Task → book_reporting.write_report
                         → 경로 XCom → read_report Task → book_reporting.read_report
  bakery_book_taskflow → read_cafe → clean_cafe → summary_cafe ─────┐
                       → read_bakery → clean_bakery → summary_bakery ┤
                         → join → book_reporting.join_shop_reports → save

외부 호출자 → bakery_practice.py → data/bakery_orders.csv → 집계 반환값
외부 호출자 → practice_day05.py → 목표 비교·날짜 비교·요약 카드 반환
외부 호출자 → book_reporting.py → reports.py / orders.py → 보고서·파일
```

7개 DAG 파일은 DAG 8개를 정의한다. `bakery_practice.py`와 `practice_day05.py`는 DAG에서 호출하지 않는 별도 실습 모듈이다. 루트 Python 모듈 6개에는 직접 실행용 진입점이 없다. TaskFlow 방식의 DAG 파일은 마지막 생성 호출로, Operator 방식의 DAG 파일은 모듈 수준 `with DAG(...)`로 DAG를 구성한다.

## 실행 입력과 파일 경로

모든 DAG는 수동 실행이며 `start_date`는 `2026-01-01`·`Asia/Seoul`, `catchup=False`, `max_active_runs=1`이다. Day 05의 업무 날짜는 실행 날짜가 아니라 Param으로 선택한다.

| DAG | 입력·설정 | 결과 경로 또는 전달 방식 |
| --- | --- | --- |
| `bakery_day05_select` | `report_date` 기본 `2026-10-05`, `duplicate_first` 기본 `false` | 건수와 행 목록을 로그·반환값으로 전달 |
| `bakery_book_operator` | `report_date`, Variable `bakery_min_revenue` | 보고서 로그·반환값, 파일 저장 없음 |
| `bakery_book_files` | `report_date`, Variable `bakery_min_revenue` | `orders.csv` 복사 후 `report.json` 저장 |
| `bakery_book_xcom_explicit` | `report_date`, Variable `bakery_min_revenue` | `report.json` 저장, `report_path` XCom 키로 경로 전달 |
| `bakery_book_xcom_return` | `report_date`, Variable `bakery_min_revenue` | `report.json` 저장, `return_value` XCom 키로 경로 전달 |
| `bakery_book_taskflow` | `cafe_date` 기본 `2026-10-01`, `bakery_date` 기본 `2026-10-05` | `combined.json` 저장, 목표 판정 없음 |

`report_date`는 `2026-10-05`·`2026-10-06`·`2026-10-07`, `cafe_date`는 `2026-10-01`·`2026-10-02`, `bakery_date`는 `2026-10-05`·`2026-10-06` 중 선택한다. Variable을 읽는 Task는 값을 `int`로 바꾸며 미설정 시 `10000`을 사용한다.

Book 파일은 `book_reporting.run_path(run_id, filename)`으로 `outputs/practice/book/day05/<URL 인코딩한 run_id>/<filename>`에 저장한다. `run_id`에 DAG ID를 더하지 않으므로 같은 실행 ID와 파일명은 경로를 공유하고 덮어쓴다. XCom에는 파일 내용 대신 경로를 전달하며 후속 Task는 그 파일을 직접 읽는다. 현재 Compose의 프로젝트 전체 마운트가 상대 경로와 공유 파일의 기반이다.

## 데이터와 현재 결과

CSV의 공통 열은 `order_id`, `order_date`, `menu`, `quantity`, `unit_price`, `status`다. 읽을 때 모든 값은 문자열이며, 집계 시 수량과 단가를 정수로 변환한다. 기본 DAG는 날짜를 구분하지 않는다.

| 입력 | 전체 행 | paid 행 | paid 수량 | paid 매출 |
| --- | ---: | ---: | ---: | ---: |
| `data/cafe_orders.csv` | 8 | 6 | 10 | 32500 |
| `data/bakery_orders.csv` | 8 | 6 | 10 | 22500 |

Day 05의 `reports.build_report`는 날짜 선택 → 결제 선택 → 집계 후 `report_date`, `min_revenue`, `target_met`를 붙인다.

| 입력·요청 날짜 | paid 행 | paid 수량 | paid 매출 | 목표 `10000` 달성 |
| --- | ---: | ---: | ---: | --- |
| 카페 `2026-10-01` | 3 | 4 | 13000 | `True` |
| 카페 `2026-10-02` | 3 | 6 | 19500 | `True` |
| 베이커리 `2026-10-05` | 3 | 6 | 14000 | `True` |
| 베이커리 `2026-10-06` | 3 | 4 | 8500 | `False` |
| 베이커리 `2026-10-07` | 0 | 0 | 0 | `False` |

TaskFlow 결합 DAG는 각 집계에 `report_date`만 붙이고 `report_dates`, `shops`, `total_revenue`로 결합한다. 기본 날짜 조합의 합산 매출은 `27000`이다.

`workflow_day05.select_day`는 결제 상태를 검사하지 않는다. 기본 날짜에서는 원본 8행 중 4행을 선택하고 4행을 제외한다. 현재 `order_ids.append(row)` 구현으로 `order_ids`에는 ID 대신 행 사전이 들어가며 중복 ID를 검출하지 못한다. `duplicate_first=true`에서는 원본 9행·선택 5행·제외 4행이 되고 중복 행도 반환한다.

`outputs/practice/day04-summary.json`을 작성하는 호출은 현재 코드에 없다. 기존 결과 파일의 존재를 자동 생성 경로의 증거로 해석하지 않는다.

## 문서 유지 규칙

코드 추가·이동·삭제 시 대응 문서와 위 표를 함께 변경한다. 함수 서명, 내부 함수, 호출 대상, Task 연결, 입출력 경로가 바뀌면 해당 문서를 갱신한다. 설명은 주석의 의도보다 실제 실행 코드를 기준으로 한다.
