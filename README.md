# Airflow 주문 데이터 실습

카페·베이커리 주문 CSV를 읽고 결제 완료 주문의 건수·수량·매출을 집계하는 Python 및 Apache Airflow 실습 프로젝트입니다. Day 05에서는 업무 날짜 선택, 매출 목표 판정, 실행별 파일 저장, XCom 전달, 두 매장의 병렬 처리까지 다룹니다.

## 구성

```text
.
├── docker-compose.yaml             # Airflow 컨테이너 실행 설정
├── orders.py                       # 공통 읽기·결제 선택·집계·JSON 저장
├── bakery_practice.py              # 베이커리 Python 함수 실습
├── practice_day05.py               # 목표 비교·날짜 비교·요약 카드 실습
├── reports.py                      # 날짜 선택·결제 집계·목표 판정
├── workflow_day05.py               # 날짜 선택 결과와 건수 증거
├── book_reporting.py               # 보고서 생성·실행별 저장·매장 결과 결합
├── dags/
│   ├── cafe_orders_basic.py        # 읽기 → 결제 선택 → 집계 → JSON 저장
│   ├── bakery_orders_basic.py      # 읽기 → 결제 선택 → 집계
│   ├── bakery_day05_select.py      # 읽기 → 날짜 선택 → 증거 출력
│   ├── bakery_book_operator.py     # PythonOperator 보고서
│   ├── bakery_book_files.py        # CSV 복사 → 복사본 보고서 저장
│   ├── bakery_book_xcom.py         # 명시적 키·반환값 XCom 비교 (DAG 2개)
│   └── bakery_book_taskflow.py     # 매장별 병렬 집계 → 결합 → 저장
├── data/
│   ├── cafe_orders.csv
│   └── bakery_orders.csv
├── config/                     # 개발 도구 설정 예시
└── docs/                       # 코드 파일별 1:1 라우팅 문서
```

실행 중 생성되는 `outputs/`, Airflow 상태·로그, Python 캐시와 로컬 환경 파일은 Git에서 제외합니다.

`data/`의 CSV는 실습용 입력이므로 저장소에 포함합니다. 로컬 환경 변수는 `.env`에 두고, 공유할 환경 변수 예시는 실제 비밀값 없이 `.env.example`에 작성하세요.

## Airflow 실행

Docker와 Docker Compose가 필요합니다. 설정된 이미지는 `apache/airflow:3.1.8-python3.12`입니다.

```bash
git clone https://github.com/chaejh1009/airflow_class.git
cd airflow_class
docker compose up -d
docker compose logs -f airflow
```

브라우저에서 <http://localhost:8080>에 접속합니다. 로그인 정보는 최초 실행 로그를 확인하세요. 로그 확인을 마칠 때 `Ctrl+C`를 눌러도 백그라운드 컨테이너는 계속 실행됩니다.

7개 DAG 파일에서 8개 DAG를 정의하며, 모두 `schedule=None`입니다. 웹 UI에서 원하는 DAG를 활성화한 뒤 수동 실행합니다.

| DAG ID | Task 순서 | 결과 |
| --- | --- | --- |
| `cafe_orders_basic` | `read → keep_paid → total → save` | `outputs/day04-summary.json` 저장 |
| `bakery_orders_basic` | `read → keep_paid → total` | `total` Task의 반환값으로 집계 전달 |
| `bakery_day05_select` | `read_source → select → evidence` | 날짜 선택 건수·행 목록을 로그와 반환값으로 전달 |
| `bakery_book_operator` | `make_report` | 날짜별 보고서를 로그와 반환값으로 전달 |
| `bakery_book_files` | `snapshot → make_report` | 실행별 `orders.csv`와 `report.json` 저장 |
| `bakery_book_xcom_explicit` | `make_report → read_report` | 보고서 저장 경로를 `report_path` XCom 키로 전달 |
| `bakery_book_xcom_return` | `make_report → read_report` | 보고서 저장 경로를 반환값 XCom으로 전달 |
| `bakery_book_taskflow` | 매장별 `read_* → clean_* → summary_*`, 이후 `join → save` | 두 매장 결과를 `combined.json`으로 저장 |

Day 05 DAG의 실행 입력은 다음과 같습니다.

- `bakery_day05_select`, `bakery_book_operator`, `bakery_book_files`, 두 XCom DAG: `report_date` 기본값은 `2026-10-05`이며 `2026-10-05`, `2026-10-06`, `2026-10-07` 중 선택합니다. `bakery_day05_select`에는 첫 행을 복제하는 `duplicate_first`도 있으며 기본값은 `false`입니다.
- `bakery_book_taskflow`: `cafe_date` 기본값은 `2026-10-01`이고 `2026-10-01`·`2026-10-02`를 허용합니다. `bakery_date` 기본값은 `2026-10-05`이고 `2026-10-05`·`2026-10-06`을 허용합니다.
- Operator·Files·XCom DAG는 Airflow Variable `bakery_min_revenue`를 Task 실행 시 읽어 정수로 변환합니다. 설정하지 않으면 `10000`을 사용합니다. TaskFlow 결합 DAG는 목표 판정을 하지 않습니다.

프로젝트 루트는 컨테이너의 `/opt/airflow/workshop`에 마운트되며, 결과 파일은 호스트의 `outputs/`에도 나타납니다. 기본 카페 DAG는 고정 경로를 덮어씁니다. Book 계열의 실행별 파일 경로는 `outputs/practice/book/day05/<URL 인코딩한 run_id>/` 아래입니다. Files DAG는 원본 CSV를 `orders.csv`로 복사하고 이 복사본으로 `report.json`을 만듭니다. 두 XCom DAG도 `report.json`을 만들며, TaskFlow DAG는 `combined.json`을 만듭니다. 경로에 DAG ID는 포함되지 않으므로 같은 `run_id`와 파일명을 사용하면 같은 파일을 덮어씁니다.

`bakery_orders_basic`, `bakery_day05_select`, `bakery_book_operator`에는 파일 저장 단계가 없습니다. 파일을 넘겨받는 Task는 해당 경로를 읽을 수 있어야 하며, 현재 Compose 구성은 프로젝트 전체를 한 컨테이너에 마운트합니다.

종료할 때는 다음 명령을 사용합니다. Airflow 상태는 명명 볼륨 `airflow-state`에 보존됩니다.

```bash
docker compose down
```

## Python 함수만 실행

공통 함수는 Python 표준 라이브러리만 사용합니다. 프로젝트 루트에서 실행하세요.

```bash
python3 - <<'PY'
from orders import paid_orders, read_orders, save_json, summarize

summary = summarize(paid_orders(read_orders()))
print(summary)
print(save_json(summary, "outputs/day04-summary.json"))
PY
```

베이커리 실습 함수도 별도로 호출할 수 있습니다.

```bash
python3 - <<'PY'
from bakery_practice import read_bakery_orders, summarize_bakery

print(summarize_bakery(read_bakery_orders()))
PY
```

Day 05의 날짜별 보고서와 목표 비교도 Airflow 없이 실행할 수 있습니다.

```bash
python3 - <<'PY'
from book_reporting import make_report
from practice_day05 import show_targets

print(make_report("2026-10-05"))
print(make_report("2026-10-06"))
show_targets("10000")
PY
```

첫 보고서는 매출 `14000`, `target_met=True`이고 둘째는 매출 `8500`, `target_met=False`입니다. `show_targets`도 `14000 True`, `8500 False`를 출력합니다. 파일 저장·재읽기는 다음처럼 확인합니다.

```bash
python3 - <<'PY'
from book_reporting import read_report, write_report

path = write_report("2026-10-05", "local-demo")
print(path)
print(read_report(path))
PY
```

이 예제는 `outputs/practice/book/day05/local-demo/report.json`을 생성하며, 다시 실행하면 덮어씁니다. 루트의 Python 모듈 6개에는 자동 실행 진입점이 없으므로 파일만 직접 실행하면 집계가 출력되지 않습니다. DAG는 `bakery_practice.py`와 `practice_day05.py`를 호출하지 않습니다.

## 데이터와 예상 결과

CSV 열은 `order_id`, `order_date`, `menu`, `quantity`, `unit_price`, `status`입니다. 집계 경로는 `status`가 `paid`인 주문만 선택하고, 수량과 단가를 정수로 바꿔 합산합니다. 기본 DAG와 `bakery_practice.py`는 날짜 구분 없이 전체 결제 주문을 집계합니다.

| 데이터 | 결제 주문 건수 | 총수량 | 총매출 |
| --- | ---: | ---: | ---: |
| 카페 | 6 | 10 | 32500 |
| 베이커리 | 6 | 10 | 22500 |

기본 집계 사전의 키는 `order_count`, `quantity`, `revenue`입니다. Day 05 보고서는 요청 날짜와 정확히 일치하는 행을 먼저 선택합니다.

| 매장·업무 날짜 | 결제 주문 건수 | 총수량 | 총매출 | 목표 `10000` 달성 |
| --- | ---: | ---: | ---: | --- |
| 카페 `2026-10-01` | 3 | 4 | 13000 | `True` |
| 카페 `2026-10-02` | 3 | 6 | 19500 | `True` |
| 베이커리 `2026-10-05` | 3 | 6 | 14000 | `True` |
| 베이커리 `2026-10-06` | 3 | 4 | 8500 | `False` |
| 베이커리 `2026-10-07` | 0 | 0 | 0 | `False` |

`reports.build_report`는 기본 집계에 `report_date`, `min_revenue`, `target_met`를 더합니다. `bakery_book_taskflow`는 각 집계에 `report_date`만 붙이고 `report_dates`, `shops`, `total_revenue`로 결합합니다. 기본 날짜 조합의 합산 매출은 `27000`입니다.

`bakery_day05_select`는 결제 상태를 검사하지 않으므로 기본 날짜에서 전체 8행 중 4행을 선택하고 4행을 제외합니다. 현재 `workflow_day05.select_day`는 `order_ids`에 ID 문자열 대신 행 사전을 넣습니다. 따라서 `duplicate_first=true`여도 중복 ID를 거부하지 않고 전체 9행·선택 5행·제외 4행을 반환합니다.

## 코드 라우팅 문서

[문서 색인](docs/README.md)에서 각 파일의 함수 서명, 호출 관계, Task 연결, 입출력 경로와 수정 지점을 확인할 수 있습니다.

베이커리 실습 코드의 현재 구현에는 다음 특징이 있습니다.

- 두 읽기 함수는 `path` 인자 대신 고정된 `data/bakery_orders.csv` 경로를 사용합니다.
- `select_paid_orders`는 `is_paid_order`를 호출하지 않고 상태를 직접 비교합니다.
- 취소 주문 집계를 안내하는 주석은 있지만 해당 집계는 구현되어 있지 않습니다.
