# Airflow 주문 데이터 실습

카페·베이커리 주문 CSV를 읽고 결제 완료 주문만 골라 건수·수량·매출을 집계하는 Python 및 Apache Airflow 실습 프로젝트입니다.

## 구성

```text
.
├── docker-compose.yaml         # Airflow 컨테이너 실행 설정
├── orders.py                   # 공통 읽기·필터·집계·저장 함수
├── bakery_practice.py          # 베이커리 Python 함수 실습
├── dags/
│   ├── cafe_orders_basic.py    # 읽기 → 결제 선택 → 집계 → JSON 저장
│   └── bakery_orders_basic.py  # 읽기 → 결제 선택 → 집계
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

두 DAG는 `schedule=None`으로 설정되어 있습니다. 웹 UI에서 원하는 DAG를 활성화한 뒤 수동 실행합니다.

| DAG ID | Task 순서 | 결과 |
| --- | --- | --- |
| `cafe_orders_basic` | `read → keep_paid → total → save` | `outputs/day04-summary.json` 저장 |
| `bakery_orders_basic` | `read → keep_paid → total` | `total` Task의 반환값으로 집계 전달 |

프로젝트 루트는 컨테이너의 `/opt/airflow/workshop`에 마운트됩니다. 카페 DAG가 저장한 JSON은 호스트의 `outputs/`에도 나타나며 재실행 시 덮어씁니다. 베이커리 DAG에는 파일 저장 단계가 없습니다.

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

`orders.py`와 `bakery_practice.py`에는 자동 실행 진입점이 없으므로 파일만 직접 실행하면 집계가 출력되지 않습니다. 두 Airflow DAG는 `orders.py`를 사용하며 `bakery_practice.py`를 호출하지 않습니다.

## 데이터와 예상 결과

CSV 열은 `order_id`, `order_date`, `menu`, `quantity`, `unit_price`, `status`입니다. `status`가 `paid`인 주문만 선택하고, 수량과 단가를 정수로 바꿔 합산합니다. 날짜별 그룹화는 하지 않습니다.

| 데이터 | 결제 주문 건수 | 총수량 | 총매출 |
| --- | ---: | ---: | ---: |
| 카페 | 6 | 10 | 32500 |
| 베이커리 | 6 | 10 | 22500 |

결과 사전의 키는 `order_count`, `quantity`, `revenue`입니다.

## 코드 라우팅 문서

[문서 색인](docs/README.md)에서 각 파일의 함수 서명, 호출 관계, Task 연결, 입출력 경로와 수정 지점을 확인할 수 있습니다.

베이커리 실습 코드의 현재 구현에는 다음 특징이 있습니다.

- 두 읽기 함수는 `path` 인자 대신 고정된 `data/bakery_orders.csv` 경로를 사용합니다.
- `select_paid_orders`는 `is_paid_order`를 호출하지 않고 상태를 직접 비교합니다.
- 취소 주문 집계를 안내하는 주석은 있지만 해당 집계는 구현되어 있지 않습니다.
