import pandas as pd
import re

df = pd.read_csv('groww_reviews.csv')
print(f"Starting with {len(df)} reviews")

before = len(df)
df = df.drop_duplicates(subset='review_text')
print(f"Removed {before - len(df)} duplicate reviews")

df['word_count'] = df['review_text'].astype(str).apply(lambda x: len(x.split()))
before = len(df)
df = df[df['word_count'] >= 5]
print(f"Removed {before - len(df)} reviews under 5 words")

def clean_text(text):
    text = str(text)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df['review_text'] = df['review_text'].apply(clean_text)

df['word_count'] = df['review_text'].apply(lambda x: len(x.split()))
before = len(df)
df = df[df['word_count'] >= 5]
print(f"Removed {before - len(df)} reviews that became empty/short after cleaning")

df = df.drop(columns=['word_count'])
df.to_csv('groww_reviews_clean.csv', index=False)
print(f"\nFinal clean dataset: {len(df)} reviews")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")