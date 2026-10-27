# bakery_ml.py 라우팅

대응 원본: [bakery_ml.py](../bakery_ml.py)

## 역할과 진입점

수요 CSV 준비 → 선형 회귀 학습 → MAE 평가 → 버전 등록·활성화 → 예측을 제공한다. `joblib`, `scikit-learn`이 필요하며 직접 실행 진입점은 없다. [ML DAG](dags/bakery_book_ml.py.md)와 [예측 CLI](predict_bakery_demand.py.md)가 호출한다.

### `to_xy(rows)`

각 행의 `expected_visitors`, `sold_quantity`를 float로 변환하고 유한한 음이 아닌 수인지 검사한다. 방문객 수를 한 열짜리 2차원 `X`, 판매량을 1차원 `y`로 반환한다.

### `read_json(path)`

UTF-8 JSON 파일을 읽어 Python 값으로 반환한다.

### `save_json(data, path)`

한글 보존·들여쓰기 2칸·마지막 줄바꿈으로 JSON을 쓰고 경로 문자열을 반환한다. `allow_nan=False`이며 부모 디렉터리는 만들지 않는다. `orders.save_json`과 별개 함수다.

### `atomic_json(data, path)`

부모 폴더 생성 → 같은 폴더의 `<파일명>.tmp`에 `save_json` → `os.replace`로 교체한다. 최종 경로 문자열을 반환한다.

### `run_folder(run_id, output_root)`

실행 ID의 영문·숫자·점·밑줄·하이픈 외 문자를 `_`로 치환하고 양끝 `._-`를 제거해 최대 60자로 자른다. 빈 이름은 `run`을 쓴다. 원본 실행 ID의 SHA-256 앞 16자리를 붙여 `<output_root>/runs/<label>-<hash>` Path를 반환한다.

### `runtime_versions()`

Python, scikit-learn, joblib 버전을 `python`, `scikit_learn`, `joblib` 키로 반환해 평가 기록에 넣는다.

### `prepare_data(source_path, run_id, output_root="outputs/book/day06/ml")`

같은 실행의 `prepared.json`이 있으면 즉시 경로를 재사용한다. 그렇지 않으면 CSV 바이트의 SHA-256을 구하고 마지막 `registry/attempted.json`의 해시와 같으면 `None`을 반환한다. 모든 과거 데이터 해시를 검색하는 방식은 아니다.

CSV를 `date` 문자열로 정렬하고 서로 다른 날짜가 최소 8개인지 검사한다. 마지막 2행을 평가용, 나머지를 학습용으로 나눠 `to_xy`를 적용한다. 원본 바이트를 `source.csv`에 보관하고 실행 ID·해시·레지스트리 경로·특징·타깃·학습/평가 날짜와 X/y를 `prepared.json`으로 저장한다.

### `train_model(prepared_path)`

같은 폴더의 `candidate.joblib`이 있으면 재사용한다. 없으면 준비 JSON을 읽어 `LinearRegression().fit(train.X, train.y)`를 수행한다. `joblib.dump`로 임시 파일에 저장하고 `os.replace` 후 모델 경로를 반환한다.

### `improves_active(mae, active_mae)`

활성 모델이 없거나 후보 MAE가 활성 모델 MAE보다 엄격히 작으면 참이다.

### `passes_quality(mae, baseline_mae, max_mae, active_mae=None)`

같은 이름의 함수가 파일에 두 번 정의되어 있으며 **파일 끝의 정의가 실제로 사용된다**. `mae <= max_mae`, `mae < baseline_mae`, `improves_active(mae, active_mae)`를 모두 만족해야 승인한다. 앞선 정의는 활성 모델 비교를 하지 않지만 뒤의 정의로 덮어써진다.

### `evaluate_model(candidate_path, max_mae=3.0)`

`metrics.json`이 있으면 기존 결과를 재사용한다. 없으면 허용 MAE가 유한한 음이 아닌 수인지 검사하고 후보·준비 데이터를 읽는다. 평가용 2행에 대한 후보 MAE와 학습 판매량 평균을 상수 예측으로 사용한 기준 MAE를 구한다. 활성 모델이 있으면 같은 평가 데이터로 활성 모델 MAE도 계산한다.

`passes_quality` 결과를 `accepted`로 넣고 해시·실행 ID·활성 버전·예측값·실측값·MAE·행 수·날짜·런타임 버전 등을 `metrics.json`에 원자적으로 저장한다. 같은 실행의 파일을 재사용하면 바뀐 임계값으로 다시 평가하지 않는다.

### `register_version(metrics, metrics_path)`

`registry/models/v숫자` 디렉터리의 최댓값 다음 버전을 선택해 `metrics["registered_version"]`에 기록한다. 재호출 시 기록된 버전을 사용한다. 후보를 `models/vN/model.joblib`로 복사하고 버전·모델 경로·해시·실행 ID·평가 경로를 `registry/active.json`에 저장한다. 승인 여부 자체는 이 함수에서 검사하지 않는다.

### `approve_model(metrics_path)`

평가 당시 활성 버전과 현재 버전이 달라졌으면 `ValueError`로 오래된 후보를 거절한다. 단, 해당 데이터와 등록 버전이 이미 활성화된 재실행은 허용한다. 품질 미달이면 `attempted.json`에 `rejected`를 기록하고 활성 모델은 유지한 채 `None`을 반환한다.

승인된 후보의 해시가 현재 활성 모델과 다르면 `register_version`을 호출한다. 이후 `attempted.json`에 `approved`를 기록하고 `active.json` 경로를 반환한다. 등록과 활성 포인터 갱신은 파일 기반이며 별도 프로세스 간 잠금은 없다.

### `predict_active(active_path, expected_visitors=90)`

방문객 수를 float로 변환하고 유한한 음이 아닌 수인지 검사한다. 호출할 때마다 활성 포인터와 모델을 다시 읽어 `model.predict([[expected_visitors]])`를 실행한다. `version`, `model_path`, `expected_visitors`, `predicted_quantity` 사전을 반환하며 판매량을 반올림하거나 0으로 보정하지 않는다.

## 파일 흐름과 수정 지점

```text
data/bakery_demand.csv → prepare_data → runs/<label>-<hash>/source.csv, prepared.json
  → train_model → candidate.joblib
  → evaluate_model → metrics.json
  → approve_model → registry/attempted.json
                  → registry/models/vN/model.joblib, registry/active.json (승인 시)
  → predict_active → 예측 사전 → DAG가 같은 실행 폴더의 prediction.json 저장
```

모든 경로는 기본적으로 `outputs/book/day06/ml/` 아래다. 기존 실행의 준비·모델·평가 파일을 재사용하므로 새 데이터나 임계값으로 새 실험을 하려면 새 실행 ID를 사용한다. 마지막으로 승인 또는 거절한 데이터와 같은 CSV는 새 실행에서도 준비 단계가 건너뛴다. 데이터 분할은 `prepare_data`, 모델 종류는 `train_model`, 품질 기준은 마지막 `passes_quality`, 버전·승인은 `register_version`·`approve_model`에서 변경한다. 입력·파일·모델 로딩 오류는 호출자에게 전달한다.
