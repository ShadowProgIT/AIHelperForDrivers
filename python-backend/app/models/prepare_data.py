import pandas as pd
import re
from pathlib import Path

def load_and_preprocess(filepath: str) -> pd.DataFrame:

    df = pd.read_parquet(filepath)
    if filepath.endswith('.jsonl'):
        df = pd.read_json(filepath, lines=True)
    else:
        df = pd.read_parquet(filepath)

    def clean_text(text: str) -> str:
        if pd.isna(text):
            return ""
        text = str(text).lower()
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
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        text = re.sub(r'[^а-яА-ЯёЁ0-9\s.,!?;:-]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()
    df['text_clean'] = df['text'].apply(clean_text)
    df['label'] = df['label'].astype(int)
    return df[['text_clean', 'label']].dropna()

if __name__ == "__main__":
    df = load_and_preprocess("app/models/train_dataset.parquet")
    print(f"Загружено: {len(df)} записей")
    print(f"Распределение: {df['label'].value_counts().to_dict()}")
    df = load_and_preprocess("app/models/train.jsonl")
    print(f"Загружено: {len(df)} записей")
    print(f"Распределение: {df['label'].value_counts().to_dict()}")
    df.to_parquet("app/models/train_dataset_clean.parquet", index=False)