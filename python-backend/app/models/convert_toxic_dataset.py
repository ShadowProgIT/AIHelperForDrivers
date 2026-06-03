import pandas as pd
import json
from pathlib import Path


def convert_jsonl_to_parquet(train_jsonl_path: str, test_jsonl_path: str,
                             output_path: str = "app/models/safety_dataset.parquet"):
    train_data = []
    with open(train_jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            train_data.append(json.loads(line))
    test_data = []
    with open(test_jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            test_data.append(json.loads(line))
    all_data = train_data + test_data
    df = pd.DataFrame(all_data)
    print("Колонки в датасете:", df.columns.tolist())
    print(f"Размер датасета: {len(df)} записей")
    print("\nРаспределение меток:")
    print(df['label'].value_counts())
    df[['text', 'label']].to_parquet(output_path, index=False)
    print(f"\nДатасет сохранён: {output_path}")
    return df

if __name__ == "__main__":
    train_path = "app/models/train.jsonl"
    test_path = "app/models/test.jsonl"
    convert_jsonl_to_parquet(train_path, test_path)