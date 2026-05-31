# app/models/train_classifier.py
import joblib
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def train_classifier(
        data_path: str,
        model_output: str = "app/models/safety_classifier.pkl",
        vectorizer_output: str = "app/models/tfidf_vectorizer.pkl"
):
    """
    Обучает простой, но эффективный классификатор: TF-IDF + Logistic Regression.
    Преимущества: быстрый инференс, легко деплоить, хорошо работает на русском.
    """
    # 1. Загрузка данных
    df = pd.read_parquet(data_path)

    df = df.sample(n=30000, random_state=42)
    if 'text_clean' not in df.columns:
        df['text_clean'] = df['text']

    X = df['text_clean'].fillna("")
    y = df['label']

    # 2. Разделение
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 3. Векторизация (оптимизирована под русский язык)
    vectorizer = TfidfVectorizer(
        analyzer='word',
        token_pattern=r'(?u)\b\w+\b',  # лучше для кириллицы
        max_features=10000,
        min_df=2,
        max_df=0.8,
        ngram_range=(1, 2),  # унимграммы + биграммы
        sublinear_tf=True
    )

    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # 4. Обучение модели
    model = LogisticRegression(
        class_weight='balanced',  # важно при дисбалансе классов
        max_iter=1000,
        random_state=42,
        solver='lbfgs'
    )
    model.fit(X_train_vec, y_train)

    # 5. Оценка
    y_pred = model.predict(X_test_vec)
    f1 = f1_score(y_test, y_pred)
    logger.info(f"🎯 F1-score на тесте: {f1:.4f}")
    logger.info("\n" + classification_report(y_test, y_pred, target_names=['Safe', 'Harmful']))

    # 6. Сохранение
    Path(model_output).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_output)
    joblib.dump(vectorizer, vectorizer_output)

    logger.info(f"✅ Модель сохранена: {model_output}")
    logger.info(f"✅ Векторизатор сохранён: {vectorizer_output}")

    return model, vectorizer, f1


if __name__ == "__main__":
    train_classifier("app/models/safety_dataset.parquet")