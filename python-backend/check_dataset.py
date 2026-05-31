import pandas as pd

df = pd.read_parquet("app/models/train_dataset.parquet")
print("Колонки:", df.columns.tolist())
print("Размер:", len(df))
print("Первые 5 строк:")
print(df.head())
print("Распределение label:\n", df['label'].value_counts())