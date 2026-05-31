import pandas as pd
import re
from pathlib import Path

def load_and_preprocess(filepath: str) -> pd.DataFrame:
<<<<<<< HEAD
    df = pd.read_parquet(filepath)
=======
    """
    Загружает датасет и приводит к единому формату.
    Ожидаемые колонки: 'text', 'label' (0 - безопасно, 1 - вредоносный)
    """
    # Определяем формат файла по расширению
    if filepath.endswith('.jsonl'):
        df = pd.read_json(filepath, lines=True)
    else:
        df = pd.read_parquet(filepath)

    # Нормализация текста
>>>>>>> 0e24a5b9812b5db89a7a71e84d4203e881c3b45d
    def clean_text(text: str) -> str:
        if pd.isna(text):
            return ""
        text = str(text).lower()
<<<<<<< HEAD
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        text = re.sub(r'[^а-яА-ЯёЁ0-9\s.,!?;:-]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()
    df['text_clean'] = df['text'].apply(clean_text)


    if 'label' not in df.columns:
        harmful_keywords = [
            'взлом', 'кража', 'обман', 'мошенник', 'наркот', 'суицид',
            'убийств', 'оружие', 'бомб', 'террор', 'экстремист', 'порнограф'
        ]
        df['label'] = df['text_clean'].apply(
            lambda x: int(any(kw in x for kw in harmful_keywords))
        )
=======
        # Удаляем ссылки
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        # Оставляем кириллицу и базовую пунктуацию
        text = re.sub(r'[^а-яА-ЯёЁ0-9\s.,!?;:-]', ' ', text)
        # Удаляем лишние пробелы
        return re.sub(r'\s+', ' ', text).strip()

    # Создаём очищенную колонку
    df['text_clean'] = df['text'].apply(clean_text)

    # Убеждаемся, что label - целые числа
    df['label'] = df['label'].astype(int)
>>>>>>> 0e24a5b9812b5db89a7a71e84d4203e881c3b45d

    return df[['text_clean', 'label']].dropna()

if __name__ == "__main__":
<<<<<<< HEAD
    df = load_and_preprocess("app/models/train_dataset.parquet")
    print(f"Загружено: {len(df)} записей")
    print(f"Распределение: {df['label'].value_counts().to_dict()}")
=======
    # Пример использования с JSONL
    df = load_and_preprocess("app/models/train.jsonl")
    print(f"✅ Загружено: {len(df)} записей")
    print(f"📊 Распределение: {df['label'].value_counts().to_dict()}")

    # Сохраняем в Parquet для быстрой загрузки в следующий раз
>>>>>>> 0e24a5b9812b5db89a7a71e84d4203e881c3b45d
    df.to_parquet("app/models/train_dataset_clean.parquet", index=False)