# 코드 라우팅 문서

이 문서에서 라우팅은 실행 진입점부터 함수·Task 호출, 데이터 입력, 결과 출력까지 이어지는 경로를 뜻한다. HTTP URL 라우팅을 구현한 프로젝트는 아니다.

코드 파일별로 원본 경로를 유지하여 `docs/<원본 파일 경로>.md`에 1:1 대응 문서를 둔다. Python 코드 4개와 실행 설정 1개가 대상이며, CSV 입력·JSON 결과·캐시 파일은 별도 코드 문서를 만들지 않는다.

| 원본 | 대응 문서 | 역할 |
| --- | --- | --- |
| [orders.py](../orders.py) | [orders.py.md](orders.py.md) | 공통 CSV 읽기·결제 선택·집계·JSON 저장 |
| [bakery_practice.py](../bakery_practice.py) | [bakery_practice.py.md](bakery_practice.py.md) | 베이커리 함수 실습 |
| [dags/cafe_orders_basic.py](../dags/cafe_orders_basic.py) | [cafe_orders_basic.py.md](dags/cafe_orders_basic.py.md) | 카페 읽기 → 선택 → 집계 → 저장 DAG |
| [dags/bakery_orders_basic.py](../dags/bakery_orders_basic.py) | [bakery_orders_basic.py.md](dags/bakery_orders_basic.py.md) | 베이커리 읽기 → 선택 → 집계 DAG |
| [docker-compose.yaml](../docker-compose.yaml) | [docker-compose.yaml.md](docker-compose.yaml.md) | Airflow 실행 환경과 경로 연결 |

## 전체 흐름

```text
docker-compose.yaml → airflow standalone → dags/의 DAG 정의
  cafe_orders_basic    → orders.py → data/cafe_orders.csv
                                  → outputs/day04-summary.json
  bakery_orders_basic  → orders.py → data/bakery_orders.csv
                                  → 집계 반환값 (저장 Task 없음)

외부 호출자 → bakery_practice.py → data/bakery_orders.csv → 집계 반환값
```

두 DAG는 `orders.py`를 사용한다. `bakery_practice.py`는 DAG에서 호출하지 않는 별도 실습 모듈이다. Python 모듈 2개에는 직접 실행용 진입점이 없고, DAG 파일에는 맨 아래 DAG 생성 호출이 있다.

## 데이터와 현재 결과

CSV의 공통 열은 `order_id`, `order_date`, `menu`, `quantity`, `unit_price`, `status`다. 읽을 때 모든 값은 문자열이며, 집계 시 수량과 단가를 정수로 변환한다. 날짜별 그룹화는 수행하지 않는다.

| 입력 | 전체 행 | paid 행 | paid 수량 | paid 매출 |
| --- | ---: | ---: | ---: | ---: |
| `data/cafe_orders.csv` | 8 | 6 | 10 | 32500 |
| `data/bakery_orders.csv` | 8 | 6 | 10 | 22500 |

`outputs/practice/day04-summary.json`은 현재 베이커리 집계와 같은 값을 담지만, 저장된 코드에는 이 파일을 작성하는 호출이 없다. 기존 파일의 존재를 자동 생성 경로의 증거로 해석하지 않는다.

## 문서 유지 규칙

코드 추가·이동·삭제 시 대응 문서와 위 표를 함께 변경한다. 함수 서명, 내부 함수, 호출 대상, Task 연결, 입출력 경로가 바뀌면 해당 문서를 갱신한다. 설명은 주석의 의도보다 실제 실행 코드를 기준으로 한다.
