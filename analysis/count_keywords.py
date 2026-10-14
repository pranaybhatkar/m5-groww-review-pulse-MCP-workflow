import pandas as pd

df = pd.read_csv('groww_reviews_clean.csv')
text = df['review_text'].str.lower()

patterns = {
    'DDPI':        r'\bddpi\b',
    'brokerage':   r'brokerage',
    'charge(s)':   r'\bcharg(?:e|es|ed|ing)\b',
    'fee(s)':      r'\bfees?\b',
    'exit load':   r'exit load',
    'AMC':         r'\bamc\b',
    'tax':         r'\btax(?:es)?\b',
    'STCG/LTCG':   r'\b(?:stcg|ltcg)\b',
    'square off':  r'square[- ]?off',
    'deduct':      r'\bdeduct\w*',
    'hidden':      r'\bhidden\b',
    'TPIN':        r'\btpin\b',
}

print(f"Total reviews: {len(df)}\n")
for name, pat in patterns.items():
    n = text.str.contains(pat, regex=True).sum()
    print(f"{name:12} {n:5}   ({n / len(df) * 100:.1f}%)")

any_fee = text.str.contains(r'ddpi|brokerage|\bcharg(?:e|es|ed|ing)\b|\bfees?\b|deduct', regex=True)
print(f"\nAny fee/charge-related: {any_fee.sum()} ({any_fee.sum() / len(df) * 100:.1f}%)")

print("\n--- Sample DDPI reviews ---")
for r in df[text.str.contains(r'\bddpi\b', regex=True)].head(8)['review_text']:
    print("-", r[:250])