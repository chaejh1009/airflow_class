# Airflow 주문 데이터 실습

카페·베이커리 주문 CSV를 읽고 결제 완료 주문의 건수·수량·매출을 집계하는 Python 및 Apache Airflow 실습 프로젝트입니다. Day 05에서는 날짜 선택·파일 저장·XCom·병렬 처리를, Day 06에서는 재시도·실패 알림·분기·합류·조건 실행·동적 DAG 생성과 수요 예측 모델의 학습·승인을 다룹니다.

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
├── book_operations.py              # 재시도·알림·분기·조건·매장별 보고서
├── bakery_ml.py                    # 수요 데이터 준비·학습·평가·모델 등록·예측
├── predict_bakery_demand.py         # 활성 모델 예측 CLI
├── dags/
│   ├── cafe_orders_basic.py        # 읽기 → 결제 선택 → 집계 → JSON 저장
│   ├── bakery_orders_basic.py      # 읽기 → 결제 선택 → 집계
│   ├── bakery_day05_select.py      # 읽기 → 날짜 선택 → 증거 출력
│   ├── bakery_book_operator.py     # PythonOperator 보고서
│   ├── bakery_book_files.py        # CSV 복사 → 복사본 보고서 저장
│   ├── bakery_book_xcom.py         # 명시적 키·반환값 XCom 비교 (DAG 2개)
│   ├── bakery_book_taskflow.py     # 매장별 병렬 집계 → 결합 → 저장
│   ├── bakery_book_retry.py        # 일시·지속 실패와 재시도
│   ├── bakery_book_alert.py        # 최종 실패 콜백
│   ├── bakery_book_branch.py       # 주문 유무로 분기
│   ├── bakery_book_join.py         # 분기 후 합류
│   ├── bakery_book_condition.py    # 조건 미달 skip과 관찰 Task
│   ├── book_dynamic_reports.py    # 설정 목록으로 매장 DAG 2개 생성
│   └── bakery_book_ml.py           # 데이터 준비 → 학습 → 평가 → 승인 → 예측
├── data/
│   ├── cafe_orders.csv
│   ├── bakery_orders.csv
│   └── bakery_demand.csv           # 날짜·예상 방문객 수·판매량
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

14개 DAG 파일에서 16개 DAG를 정의합니다. `bakery_book_ml`은 `schedule="*/1 * * * *"`로 활성화하면 매분 실행합니다. 나머지 15개는 `schedule=None`이며 웹 UI에서 수동 실행합니다. 모두 `catchup=False`입니다.

Day 06의 `book_operations.py`에는 `requests`, ML 모듈에는 `joblib`·`scikit-learn`이 필요합니다. 현재 Compose에는 추가 패키지 설치 단계가 없으므로 새 환경에서는 먼저 설치 여부를 확인하고, 없으면 실습 컨테이너에 설치하세요.

```bash
docker compose exec airflow python -c "import requests, joblib, sklearn"
# 위 import가 실패하면 실행
docker compose exec airflow pip install requests joblib scikit-learn
```

컨테이너를 삭제·재생성하면 수동 설치한 패키지도 다시 설치해야 합니다. 반복해서 사용할 환경은 별도 이미지에 의존성을 포함하세요.

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
| `bakery_book_retry` | `read_report` | 일시·지속 실패, 5초 간격 재시도 1회 |
| `bakery_book_alert` | `read_report`, 최종 실패 시 콜백 | 실패 payload 로그 및 Discord 콜백 경로 |
| `bakery_book_branch` | `read_report → choose → write_report / no_orders` | 주문 유무로 저장·빈 결과 분기 |
| `bakery_book_join` | 위 분기 뒤 `finish` | 한 분기 성공·다른 분기 skip 후 합류 |
| `bakery_book_condition` | `check_delivery → deliver → observed` | 주문·목표 달성 시 저장, 조건 미달 skip |
| `cafe_book_daily`, `bakery_book_daily` | 각각 `report` | 매장 설정에서 생성한 DAG의 날짜별 보고서 |
| `bakery_book_ml` | `prepare → train → evaluate → approve → predict` | 모델 버전·활성 포인터·평가·예측 저장 |

Day 05 DAG의 실행 입력은 다음과 같습니다.

- `bakery_day05_select`, `bakery_book_operator`, `bakery_book_files`, 두 XCom DAG: `report_date` 기본값은 `2026-10-05`이며 `2026-10-05`, `2026-10-06`, `2026-10-07` 중 선택합니다. `bakery_day05_select`에는 첫 행을 복제하는 `duplicate_first`도 있으며 기본값은 `false`입니다.
- `bakery_book_taskflow`: `cafe_date` 기본값은 `2026-10-01`이고 `2026-10-01`·`2026-10-02`를 허용합니다. `bakery_date` 기본값은 `2026-10-05`이고 `2026-10-05`·`2026-10-06`을 허용합니다.
- Operator·Files·XCom DAG는 Airflow Variable `bakery_min_revenue`를 Task 실행 시 읽어 정수로 변환합니다. 설정하지 않으면 `10000`을 사용합니다. TaskFlow 결합 DAG는 목표 판정을 하지 않습니다.

프로젝트 루트는 컨테이너의 `/opt/airflow/workshop`에 마운트되며, 결과 파일은 호스트의 `outputs/`에도 나타납니다. 기본 카페 DAG는 고정 경로를 덮어씁니다. Day 05 Book 계열의 실행별 파일 경로는 `outputs/practice/book/day05/<URL 인코딩한 run_id>/` 아래입니다. Files DAG는 원본 CSV를 `orders.csv`로 복사하고 이 복사본으로 `report.json`을 만듭니다. 두 XCom DAG도 `report.json`을 만들며, TaskFlow DAG는 `combined.json`을 만듭니다. 경로에 DAG ID는 포함되지 않으므로 같은 `run_id`와 파일명을 사용하면 같은 파일을 덮어씁니다.

`bakery_orders_basic`, `bakery_day05_select`, `bakery_book_operator`에는 파일 저장 단계가 없습니다. 파일을 넘겨받는 Task는 해당 경로를 읽을 수 있어야 하며, 현재 Compose 구성은 프로젝트 전체를 한 컨테이너에 마운트합니다.

종료할 때는 다음 명령을 사용합니다. Airflow 상태는 명명 볼륨 `airflow-state`에 보존됩니다.

```bash
docker compose down
```

## Python 함수만 실행

Day 04·05 공통 함수는 Python 표준 라이브러리만 사용합니다. Day 06 운영·ML 함수의 추가 의존성은 위 설치 안내를 참고하세요. 프로젝트 루트에서 실행하세요.

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

이 예제는 `outputs/practice/book/day05/local-demo/report.json`을 생성하며, 다시 실행하면 덮어씁니다. 루트의 Python 파일 9개 중 `predict_bakery_demand.py`만 CLI 진입점이 있습니다. 나머지 8개는 함수 호출 없이 직접 실행하면 집계·예측을 수행하지 않습니다. DAG는 `bakery_practice.py`와 `practice_day05.py`를 호출하지 않습니다.

## 데이터와 예상 결과

주문 CSV 열은 `order_id`, `order_date`, `menu`, `quantity`, `unit_price`, `status`입니다. 집계 경로는 `status`가 `paid`인 주문만 선택하고, 수량과 단가를 정수로 바꿔 합산합니다. 기본 DAG와 `bakery_practice.py`는 날짜 구분 없이 전체 결제 주문을 집계합니다.

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

## Day 06 운영 실습

Retry·Alert·Branch·Join·Condition DAG의 `report_date` 기본값은 `2026-10-05`이며 문자열을 받습니다. Day 05와 달리 날짜 enum 제한은 없습니다.

- `bakery_book_retry`: `simulate_failure=true`이면 첫 시도만 실패하고 재시도에서 성공합니다. `always_fail=true`이면 두 시도 모두 실패합니다. 두 값의 기본값은 `false`입니다.
- `bakery_book_alert`: `always_fail=true`로 최종 실패 콜백을 확인합니다. 현재 `on_failure_callback`은 `discord_failure_notice`입니다. 웹훅 URL이 빈 문자열이라 실패 payload를 로그에 남긴 다음 콜백도 `ValueError`로 실패하며 Discord 전송은 하지 않습니다. 로그만 확인하려면 `failure_notice`로 연결하세요. 실제 웹훅 비밀값은 커밋하지 마세요.
- `bakery_book_branch`, `bakery_book_join`: 주문이 있으면 저장하고 없으면 `no_orders`를 선택합니다. `2026-10-07`로 빈 주문 분기를 확인할 수 있습니다. Join의 `finish`는 `none_failed_min_one_success`로 한 분기 성공·다른 분기 skip 이후 실행됩니다.
- `bakery_book_condition`: 주문이 있고 매출 목표 `10000`을 달성해야 저장합니다. `2026-10-06`과 `2026-10-07`은 검사·전달을 skip합니다. 마지막 `observed`는 `none_failed`라 skip 이후에도 실행할 수 있습니다.
- 동적 DAG는 `STORES`로 `cafe_book_daily`와 `bakery_book_daily`를 만듭니다. 카페는 기본 날짜 `2026-10-01`·목표 `15000`, 베이커리는 `2026-10-05`·목표 `10000`입니다. 실행 설정의 `report_date`가 Param보다 우선합니다.

| 결과 | 저장 경로 |
| --- | --- |
| Branch 보고서 | `outputs/book/day06/branch/<report_date>.json` |
| Join 보고서 | `outputs/book/day06/join/<report_date>.json` |
| 조건 전달 보고서 | `outputs/book/day06/delivery/<report_date>.json` |
| 매장별 동적 보고서 | `outputs/book/day06/dynamic/<store>/<report_date>.json` |

이 경로에는 실행 ID가 없으므로 같은 날짜로 재실행하면 덮어씁니다. Retry·Alert에는 파일 저장 단계가 없습니다. Day 06 운영 DAG들은 `max_active_runs`를 명시하지 않으며 ML DAG만 `1`로 지정합니다.

## 수요 예측 실습

`data/bakery_demand.csv`는 `date`, `expected_visitors`, `sold_quantity` 열과 12개 일별 표본을 담습니다. 날짜순 마지막 2행을 평가용, 앞 10행을 학습용으로 사용합니다. 최소 8개의 서로 다른 날짜가 필요하고 방문객 수·판매량은 유한한 음이 아닌 수여야 합니다.

`bakery_book_ml`의 기본 Param은 `source_path="data/bakery_demand.csv"`, `max_mae=3.0`, `expected_visitors=90`입니다. 방문객 수 하나를 특징으로 선형 회귀를 학습합니다. 후보 모델의 MAE가 허용값 이하이고, 학습 판매량 평균을 이용한 기준 예측과 기존 활성 모델보다 작아야 승인합니다. 활성 모델이 없으면 활성 모델 비교는 생략합니다. 현재 `passes_quality`가 두 번 정의되어 있으며 파일 끝의 정의가 적용됩니다.

```text
outputs/book/day06/ml/
├── runs/<정리한 run_id>-<SHA-256 앞 16자리>/
│   ├── source.csv / prepared.json
│   ├── candidate.joblib / metrics.json
│   └── prediction.json             # 승인된 실행만 생성
└── registry/
    ├── attempted.json              # 마지막 승인·거절 데이터 해시
    ├── active.json                 # 현재 활성 버전과 모델 경로
    └── models/vN/model.joblib
```

같은 실행의 준비·모델·평가 파일은 재사용합니다. 새 실행에서도 CSV 해시가 마지막 승인·거절 데이터와 같으면 준비부터 skip합니다. 품질 미달이면 활성 모델을 유지하고 승인·예측을 skip합니다. 같은 CSV로 임계값만 바꿔도 마지막 처리 해시가 같으면 재학습하지 않습니다.

Airflow 없이 전체 흐름을 실행하려면 로컬 Python 환경에도 의존성을 설치한 뒤 다음 예제를 실행하세요. 별도 `local-ml` 폴더를 사용합니다.

```bash
python3 -m venv .venv
.venv/bin/pip install requests joblib scikit-learn
.venv/bin/python - <<'PYML'
from bakery_ml import prepare_data, train_model, evaluate_model, approve_model, predict_active

prepared = prepare_data("data/bakery_demand.csv", "local-demo", "outputs/book/day06/local-ml")
if prepared is not None:
    metrics = evaluate_model(train_model(prepared))
    active = approve_model(metrics)
    if active is not None:
        print(predict_active(active, 90))
PYML
```

승인된 모델이 있으면 독립 CLI로 언제든 예측할 수 있습니다. 아래 명령은 위 로컬 예제의 활성 모델을 사용하며, `--active`를 생략하면 ML DAG의 기본 레지스트리를 읽습니다.

```bash
.venv/bin/python predict_bakery_demand.py \
  --active outputs/book/day06/local-ml/registry/active.json \
  --expected-visitors 90
```

CLI는 호출할 때마다 활성 모델을 읽고 JSON을 출력합니다. 판매량 예측은 실수이며 반올림하거나 0으로 보정하지 않습니다. 상세 파일 재사용·승인 규칙은 [ML 라우팅 문서](docs/bakery_ml.py.md)를 참고하세요.

## 코드 라우팅 문서

[문서 색인](docs/README.md)에서 각 파일의 함수 서명, 호출 관계, Task 연결, 입출력 경로와 수정 지점을 확인할 수 있습니다.

베이커리 실습 코드의 현재 구현에는 다음 특징이 있습니다.

- 두 읽기 함수는 `path` 인자 대신 고정된 `data/bakery_orders.csv` 경로를 사용합니다.
- `select_paid_orders`는 `is_paid_order`를 호출하지 않고 상태를 직접 비교합니다.
- 취소 주문 집계를 안내하는 주석은 있지만 해당 집계는 구현되어 있지 않습니다.
