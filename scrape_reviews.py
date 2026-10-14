from google_play_scraper import reviews, Sort
import pandas as pd

all_reviews = []
token = None
cutoff = pd.Timestamp.now() - pd.Timedelta(weeks=12)

for batch in range(50):
    result, token = reviews(
        'com.nextbillion.groww',
        lang='en',
        country='in',
        sort=Sort.NEWEST,
        count=200,
        continuation_token=token
    )
    all_reviews.extend(result)

    oldest_in_batch = min(r['at'] for r in result)
    print(f"Batch {batch + 1}: {len(all_reviews)} reviews so far, oldest so far = {oldest_in_batch.date()}")

    if oldest_in_batch < cutoff or token is None:
        break

df = pd.DataFrame(all_reviews)
df = df[['content', 'score', 'at']]
df.columns = ['review_text', 'rating', 'date']
df = df[df['date'] >= cutoff]
df = df.drop_duplicates(subset='review_text')

df.to_csv('groww_reviews.csv', index=False)
print(f"\nSaved {len(df)} reviews to groww_reviews.csv")
print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")

