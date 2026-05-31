import pandas as pd
import json
from pathlib import Path


def convert_jsonl_to_parquet(train_jsonl_path: str, test_jsonl_path: str,
                             output_path: str = "app/models/safety_dataset.parquet"):
    """
    Конвертирует датасет Toxic_Russian_Comments из JSONL в Parquet
    """
    # Загрузка train данных
    train_data = []
    with open(train_jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            train_data.append(json.loads(line))

    # Загрузка test данных
    test_data = []
    with open(test_jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            test_data.append(json.loads(line))

    # Объединяем train и test
    all_data = train_data + test_data

    # Создаём DataFrame
    df = pd.DataFrame(all_data)

    # Проверяем структуру датасета
    print("Колонки в датасете:", df.columns.tolist())
    print(f"Размер датасета: {len(df)} записей")

    # В датасете Toxic_Russian_Comments колонки:
    # - 'text' - текст комментария
    # - 'label' - метка (0 - нормальный, 1 - токсичный)

    # Проверяем распределение меток
    print("\nРаспределение меток:")
    print(df['label'].value_counts())

    # Сохраняем в Parquet
    df[['text', 'label']].to_parquet(output_path, index=False)
    print(f"\n✅ Датасет сохранён: {output_path}")

    return df


if __name__ == "__main__":
    # Укажите пути к вашим файлам
    train_path = "app/models/train.jsonl"  # или полный путь
    test_path = "app/models/test.jsonl"  # или полный путь

    convert_jsonl_to_parquet(train_path, test_path)