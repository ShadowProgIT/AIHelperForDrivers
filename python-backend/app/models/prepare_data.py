# app/models/prepare_data.py
import pandas as pd
import re
from pathlib import Path


def load_and_preprocess(filepath: str) -> pd.DataFrame:
    """
    Загружает датасет и приводит к единому формату.
    Ожидаемые колонки: 'text', 'label' (0 - безопасно, 1 - вредоносный)
    """
    df = pd.read_parquet(filepath)

    # Нормализация текста
    def clean_text(text: str) -> str:
        if pd.isna(text):
            return ""
        text = str(text).lower()
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)  # удаляем ссылки
        text = re.sub(r'[^а-яА-ЯёЁ0-9\s.,!?;:-]', ' ', text)  # оставляем кириллицу и базовую пунктуацию
        return re.sub(r'\s+', ' ', text).strip()

    df['text_clean'] = df['text'].apply(clean_text)

    # Проверка наличия целевой переменной
    if 'label' not in df.columns:
        # Если метки нет, можно добавить эвристическую разметку (опционально)
        # Например, по ключевым словам
        harmful_keywords = [
            'взлом', 'кража', 'обман', 'мошенник', 'наркот', 'суицид',
            'убийств', 'оружие', 'бомб', 'террор', 'экстремист', 'порнограф'
        ]
        df['label'] = df['text_clean'].apply(
            lambda x: int(any(kw in x for kw in harmful_keywords))
        )

    return df[['text_clean', 'label']].dropna()


if __name__ == "__main__":
    # Пример использования
    df = load_and_preprocess("app/models/train_dataset.parquet")
    print(f"✅ Загружено: {len(df)} записей")
    print(f"📊 Распределение: {df['label'].value_counts().to_dict()}")
    df.to_parquet("app/models/train_dataset_clean.parquet", index=False)