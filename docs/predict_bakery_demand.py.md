# predict_bakery_demand.py 라우팅

대응 원본: [predict_bakery_demand.py](../predict_bakery_demand.py)

## 역할과 진입점

학습·승인을 마친 활성 모델로 수요를 예측하는 CLI다. `if __name__ == "__main__": main()`으로 실행한다. import만으로는 예측하지 않지만 `bakery_ml`의 joblib·scikit-learn 의존성을 로드한다.

### `main()`

`argparse`로 `--active`(기본 `outputs/book/day06/ml/registry/active.json`)와 float형 `--expected-visitors`(기본 `90`)를 받는다. `bakery_ml.predict_active(options.active, options.expected_visitors)` 결과를 한글 보존·들여쓰기 2칸 JSON으로 표준 출력에 표시한다.

```bash
python3 predict_bakery_demand.py --expected-visitors 90
```

## 입출력과 수정 지점

실행할 때마다 활성 JSON과 그 안의 모델 경로를 읽는다. 결과 파일을 저장하지 않으며 학습·버전 등록도 하지 않는다. 먼저 ML DAG 또는 Python 함수로 모델을 승인해야 한다. 파일 미존재·모델 로딩·방문객 수 검증 오류는 그대로 전파된다. 인자·기본값은 `main`, 예측 계산은 [bakery_ml.py](bakery_ml.py.md)의 `predict_active`에서 변경한다.
