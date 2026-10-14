import pandas as pd

df = pd.read_csv('groww_reviews_clean.csv')
text = df['review_text'].str.lower()

any_fee = text.str.contains(
    r'ddpi|brokerage|\bcharg(?:e|es|ed|ing)\b|\bfees?\b|deduct', regex=True
)
fee = df[any_fee].copy()
fee.to_csv('fee_reviews.csv', index=False)
print(f"Fee-related reviews: {len(fee)} (saved to fee_reviews.csv)\n")

ft = fee['review_text'].str.lower()
subtopics = {
    'brokerage':          r'brokerage',
    'DP / demat charges': r'\bdp\b|demat',
    'AMC / maintenance':  r'\bamc\b|maintenance',
    'platform fee':       r'platform fee',
    'GST / stamp duty':   r'\bgst\b|stamp',
    'tax':                r'\btax',
    'hidden':             r'\bhidden\b',
    'deducted':           r'deduct',
    'intraday / F&O':     r'intraday|f&o|\bfno\b|option',
    'withdrawal':         r'withdraw|payout',
    'IPO / MTF':          r'\bipo\b|\bmtf\b|margin',
    'penalty / fine':     r'penalt|\bfine\b',
    'unexpected / why':   r'unexpected|without (?:telling|notice|informing)|why .*charg',
    'high / too much':    r'too (?:much|high)|very high|so much|zyada|jyada',
}
print("--- What the fee reviews are about ---")
for name, pat in subtopics.items():
    n = ft.str.contains(pat, regex=True).sum()
    print(f"{name:20} {n:4}")

print("\n--- Rating split of fee reviews ---")
print(fee['rating'].value_counts().sort_index())

print("\n--- 30 random fee reviews (1-3 stars only) ---")
low = fee[fee['rating'] <= 3]
for _, r in low.sample(min(30, len(low)), random_state=1).iterrows():
    print(f"[{r['rating']}*] {r['review_text'][:220]}")