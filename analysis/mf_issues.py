import pandas as pd

df = pd.read_csv('groww_reviews.csv')   # all raw reviews (4,908)
df = df.dropna(subset=['review_text']).drop_duplicates(subset='review_text')
t = df['review_text'].str.lower()

# 1) Is the review about mutual funds?
MF = (r'mutual fund|\bmfs?\b|\bsips?\b|\bnav\b|elss|folio|index fund|\bnfo\b|'
      r'lump ?sum|redeem|redemption|exit load|expense ratio|\bamc\b|'
      r'direct plan|regular plan|mf central|\bcams\b|kfin|karvy')

# 2) Is it really about F&O / intraday? (we drop these)
FNO = (r'f&o|\bfno\b|intraday|futures|call option|put option|option chain|'
       r'\blots?\b|scalping|nifty|banknifty')

sel = df[t.str.contains(MF, regex=True) & ~t.str.contains(FNO, regex=True)].copy()
st = sel['review_text'].str.lower()

# 3) What is the issue?
GROUPS = {
    'Fees & charges':
        r'charg|\bfees?\b|brokerage|deduct|penalt|exit load|expense ratio|stamp|'
        r'commission|hidden|\bgst\b|\btax|cost',
    'SIP / auto-debit / mandate problems':
        r'\bsips?\b|\bnach\b|bounce|auto.?debit|mandate|installment|instalment',
    'Redemption / withdrawal / payout delays':
        r'redeem|redemption|withdraw|payout|not received|money (?:stuck|not)|delay|pending',
    'Returns / NAV / performance':
        r'\bnav\b|return|profit|loss|performance|xirr|cagr|negative|wrong value',
    'KYC / onboarding / account':
        r'\bkyc\b|verification|verify|onboard|sign.?up|account (?:open|creat|block|suspend)|bank (?:link|add)',
    'App bugs / errors / glitches':
        r'glitch|\bbug|error|crash|hang|not working|not loading|server|slow|lag|failed|failure',
    'Statements / reports / tax documents':
        r'statement|report|capital gain|tax (?:report|statement)|download|\bcas\b|certificate',
    'Fund info / selection / features':
        r'which fund|fund (?:list|option|selection|information|details)|compare|rating|not available|missing|feature|option',
    'Customer support':
        r'support|customer care|customer service|help|complaint|no response|no reply|ticket',
}

lines = []
sel['issues'] = ''
print(f"All reviews scanned:           {len(df)}")
print(f"Mutual-fund related (no F&O):  {len(sel)}\n")
print("--- Issue groups (a review can be in more than one) ---")

used = pd.Series(False, index=sel.index)
for name, pat in GROUPS.items():
    m = st.str.contains(pat, regex=True)
    used |= m
    sel.loc[m, 'issues'] += name + ' | '
    print(f"{name:42} {m.sum():4}")
    lines.append(f"\n\n===== {name}  ({m.sum()}) =====\n")
    for _, r in sel[m].sort_values('rating').iterrows():
        lines.append(f"[{r['rating']}*] [{str(r['date'])[:10]}] {r['review_text']}\n")

other = sel[~used]
print(f"{'Other (MF-related, no clear issue)':42} {len(other):4}")
lines.append(f"\n\n===== Other ({len(other)}) =====\n")
for _, r in other.sort_values('rating').iterrows():
    lines.append(f"[{r['rating']}*] [{str(r['date'])[:10]}] {r['review_text']}\n")

print("\n--- Rating split of MF reviews ---")
print(sel['rating'].value_counts().sort_index().to_string())

with open('mf_issues.txt', 'w', encoding='utf-8') as f:
    f.writelines(lines)
sel.to_csv('mf_reviews.csv', index=False, encoding='utf-8')
print("\nSaved: mf_issues.txt (read this) and mf_reviews.csv (for N8N later)")