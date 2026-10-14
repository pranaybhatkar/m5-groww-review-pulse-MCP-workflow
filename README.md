# Groww Review Intelligence Workflow (Milestone 5)

An AI workflow, built in n8n, that turns raw Google Play reviews of the **Groww** app into:

1. a structured **weekly product pulse** for the product team, and
2. a neutral, facts-only **fee explainer** that support can reuse,

and then, **only after a human approves**, logs both to a Google Doc and prepares a Gmail **draft** (nothing is ever sent automatically). The approved actions can run either as direct n8n nodes or through **MCP** (Model Context Protocol) tool calls.

- **Product:** Groww (same product as Milestone 4)
- **Data:** public Google Play reviews, 2026-08-02 to 2026-10-05
- **Fee issue found in the reviews:** total charges come out higher than the brokerage the user expected, and the breakdown is not clearly explained (details in section 4)

## Links

| Item | Link |
|---|---|
| Working prototype (n8n form) | `<PRODUCTION_FORM_URL>` |
| Demo video (3 min or less) | `<DEMO_VIDEO_DRIVE_LINK>` |
| GitHub repository | `<GITHUB_REPO_URL>` |

The prototype runs on an n8n Cloud trial, which ends around 18 October 2026. After that the link stops working, so the demo video and the exported workflows in `workflows/` are the lasting proof.

---

## 1. What it does

```
Reviews CSV -> clean -> sample -> AI themes + quotes -> AI fee-issue detection
            -> AI weekly pulse + AI fee explainer -> automatic checks
            -> HUMAN APPROVAL PAGE -> (Approve) Google Doc entry + Gmail draft
                                   -> (Reject)  nothing is saved
```

| Brief requirement | How it is met |
|---|---|
| Cluster into at most 5 themes, top 3 | Themes LLM returns at most 5 themes. Code counts each theme and takes the top 3 |
| 3 real user quotes | Every quote is checked in code to be **word for word** inside a real review. Quotes that were reworded or contain personal data are dropped |
| 1 recurring fee/charge confusion | A separate AI step classifies fee-related reviews. Code counts the categories and picks the winner (section 4) |
| Weekly pulse, 250 words or fewer | Themes, quotes, key observation, 3 actions. A check flags it above 240 words |
| Fee explainer | 6 bullets or fewer, neutral tone, 2 official links, "Last checked" date. Links and date are added by code, not written by the AI |
| MCP with approval gating | Nothing is written until the approval page returns "Approve" (section 5) |
| Append to Doc | `{date, top_themes, weekly_pulse, identified_fee_issue, explanation_bullets, source_links}` |
| Email draft | Subject `Weekly Product Pulse + Customer Clarification — <date>`. Body: pulse, then the fee explainer as a reusable support snippet. Recipient left empty, never sent |

---

## 2. Scope and data

- **Source:** public Google Play reviews of Groww (app id `com.nextbillion.groww`, English, India), collected with the `google-play-scraper` library.
- **Raw scrape:** 4,908 reviews (2026-08-02 to 2026-10-05), about 9 weeks.
- **After cleaning:** 2,439 reviews. Cleaning removes duplicates, emojis and non-English characters, and any review under 5 words.
- **Rating mix of the cleaned set:** 1 star 808, 2 stars 111, 3 stars 154, 4 stars 213, 5 stars 1,153.
- **Reviews mentioning a fee or charge:** 233 (flagged by keywords such as brokerage, charge, fee, deduct, tax).
- No personal data is stored. Reviews are public text, and quotes shown in outputs pass a personal-data check (phone numbers, emails, PAN-style strings).

### Why all trading reviews and not mutual funds only
Milestone 4 was a mutual fund assistant, so mutual funds were checked first. In the raw data, only **180 of 4,908 reviews (3.7%)** were about mutual funds (excluding F&O/intraday), and only **19** of those mentioned a fee. That is too few to call a fee "frequently misunderstood". The brief asks for the fee confusion that appears in the reviews, so the analysis uses all reviews, and the strongest confusion was about trade charges. This complements Milestone 4, which answers mutual fund fee facts.

---

## 3. Architecture (n8n)

```
Start (Form Trigger)
 -> Config -> Get reviews (Google Sheets)
 -> Prep reviews (Code) -> Sample (Code)
 -> Themes LLM -> Parse themes (Code)
 -> Fee LLM    -> Parse fee issue (Code)
 -> Pulse LLM  -> Explainer LLM
 -> Assemble and check (Code)
 -> Review page (approval form) -> Approved (IF)
      true  -> Doc append + Gmail draft (direct nodes, or MCP Agent) -> Done
      false -> Rejected end
```

| Node | Role |
|---|---|
| **Start** | Form with one dropdown: analysis window ("All data (about 9 weeks)" or "Last 4 weeks") |
| **Config** | One place for your email, Doc URL, the 2 source links, "Last checked" date and the source facts text |
| **Get reviews** | Reads the cleaned reviews from Google Sheets |
| **Prep reviews** | Applies the window, gives every review an ID (R1, R2, ...), flags fee-related reviews, computes totals |
| **Sample** | 400 random reviews for themes, plus up to 150 fee-related reviews (low ratings first) so the fee signal cannot be sampled away |
| **Themes LLM** | Gemini clusters the sample into at most 5 themes and proposes quotes. Assignments are returned in a compact format to avoid cut-off answers |
| **Parse themes** | Parses the answer (and repairs it if cut off), verifies quotes, counts each theme, computes the share of 1-2 star reviews per theme, picks the top 3 |
| **Fee LLM** | Sorts each fee-related review into one category (table below) |
| **Parse fee issue** | Counts the categories. The fee issue is the "unclear total charges" group. The catch-all category can never win |
| **Pulse LLM** | Writes the weekly pulse from verified facts only |
| **Explainer LLM** | Writes the fee explainer bullets using only the source facts in Config |
| **Assemble and check** | Adds links and date, runs the automatic checks, builds the Doc entry, the email and the approval page |
| **Review page / Approved** | The approval gate (section 5) |

### Why a fixed pipeline and not an AI agent
Every step is known in advance, and the brief requires an approval before any action. A fixed pipeline makes the gate a hard stop, lets code do the counting and checking that an AI model does unreliably, and makes each step inspectable. An agent is used only at the last step, to call the MCP tools.

### Fee categories used by the Fee LLM
| Code | Meaning |
|---|---|
| A | Total deducted is more than the brokerage the user expected |
| B | Confusion about the estimated amount held versus the final charge |
| C | Confusion about charges on the sell side or on both buy and sell |
| D | Unexpected or unexplained deduction |
| E | DDPI activation charge |
| F | Other or vague fee confusion (catch-all, never selected as the issue) |
| P | "Charges are too high" or a competitor is cheaper (a pricing complaint, not confusion) |
| X | Not really about a fee |

### Automatic checks (shown on the approval page)
Pulse length, at least 3 quotes that exist word for word in the reviews, no personal data in the pulse, explainer has 6 bullets or fewer, no numbers or rates inside the explainer, exactly 2 https source links, "Last checked" date present.

### Models and tools
n8n Cloud, Google Gemini (`gemini-3.1-flash-lite`, free tier via Google AI Studio), Google Sheets / Docs / Gmail nodes, n8n MCP Server Trigger and MCP Client Tool, Python (`google-play-scraper`, `pandas`) for data collection.

---

## 4. Fee issue identified from the reviews

**Identified issue:** *Total charges are more than the brokerage shown, and the breakdown is not clearly explained.*

This groups categories A, B, C and D. Users see a deduction larger than the brokerage they expected and cannot tell what the rest is (exchange and statutory charges, taxes, the estimated amount held before the final charge is deducted).

Real examples from the dataset (verified word for word, spelling as written by the users):
- "easy interface but sometimes it deducted amount without ur information if u r doing trading." (3 stars)
- "This is an estimated value of charges for today's trading. Final charges will be deducted at day-end. Check the contract note for exact details. brokage charge hevy" (1 star)

How it was chosen:
1. Keyword counts on the 2,439 cleaned reviews: "charge" in 179, "brokerage" in 78, "deduct" in 19, "hidden" in 19, "tax" in 18, "fee" in 15, **DDPI in only 4**, exit load in 0.
2. DDPI activation fees were considered first but are too rare to be "recurring", so they are reported only as a minor signal.
3. About half of the fee-related reviews are plain price complaints ("charges are too high", "competitor is cheaper"). These are reported in the pulse but are not what a neutral explainer can answer.
4. The explainer therefore targets the confusion about the total, using Groww's own help and pricing pages as sources.

The explainer does not quote any rate or rupee amount. It says what each charge is and points to the Groww pricing page for current rates, because rates change.

### Results vary between runs
Themes are computed on a random sample and the model is a free-tier model, so figures move a little from run to run. Across test runs the fee issue appeared in between **31 and 54 of the 150** fee-related reviews analysed. All shares in the outputs are labelled approximate. The run submitted with this project is saved in `weekly_pulse.md`, `doc_entry_snippet.md` and `email_draft.md`.

---

## 5. Where the MCP approval happens

The approval gate is the pair of nodes **Review page** and **Approved**:

1. **Review page** is a form page. It shows the full weekly pulse, the fee explainer, the automatic check results, and a required **Decision** dropdown (Approve / Reject).
2. **Approved** is an IF node. Only when `Decision` equals `Approve` does the workflow continue. **Reject** goes straight to a "Rejected. Nothing was saved or drafted." screen.
3. Everything that writes anything (Google Doc, Gmail) sits **after** this node on the "true" branch.

### Two ways to run the approved actions
| Variant | How | File |
|---|---|---|
| **A. Direct nodes** | Google Docs node (update, insert at end of document) and Gmail node (create draft) | `workflows/M5-working-v2.json` |
| **B. MCP** | An **MCP Agent** calls two tools on a separate **MCP Server** workflow: `append_to_doc` and `create_email_draft`. Authentication is a Bearer token. The agent is told to call each tool exactly once, pass the text unchanged, and never send an email | `workflows/M5-mcp-version.json` and `workflows/M5-mcp-server.json` |

In variant B, the direct Docs and Gmail nodes are deactivated. In testing, each tool was called exactly once, the draft carried only the DRAFT label, and the Doc entry matched the draft text word for word.

Safety notes:
- The Gmail draft is created with **no recipient**, so it cannot be sent by accident.
- The Google Doc is fixed inside the MCP server, so a caller cannot choose another document.
- The MCP server requires a Bearer token. Never commit it.

---

## 6. How to run it

### Prerequisites
- Python 3 (only for data collection), an n8n Cloud account, a Google account, a free Gemini API key from Google AI Studio.

### Step 1: collect and clean the reviews
```bash
python -m venv venv
venv\Scripts\activate          # Windows. On Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python scrape_reviews.py       # writes groww_reviews.csv (raw)
python clean_reviews.py        # writes groww_reviews_clean.csv
```
A ready sample is in `data/sample_reviews.csv`.

### Step 2: put the cleaned reviews in Google Sheets
Import `groww_reviews_clean.csv` into a new Google Sheet. Keep the columns `review_text`, `rating`, `date`.

### Step 3: import the workflow into n8n
1. In n8n, create a workflow and use **Import from file** with a JSON from `workflows/`.
2. Reconnect credentials (exported files do not contain secrets): Google Sheets, Google Docs, Gmail, and the Google Gemini API key.
3. Open the **Config** node and set `myEmail`, `docUrl` (a blank Google Doc), `link1`, `link2` and `lastChecked`.
4. Open **Get reviews** and point it at your Sheet.
5. For the MCP variant, import `M5-mcp-server.json` first, create a Bearer credential with a long random token, publish it, then paste its **Production URL** into the MCP Client Tool of the agent and select the same Bearer credential.
6. On every AI node, turn **Retry On Fail** on (3 tries, 5000 ms), because free-tier models sometimes answer "high demand".

### Step 4: run
1. **Publish** the workflow.
2. Open the **Start** node, copy its **Production URL**, and open it in a browser.
3. Choose the analysis window and submit. Wait one to two minutes without refreshing.
4. Read the pulse, the explainer and the check results on the approval page.
5. Choose **Approve** to log to the Doc and create the Gmail draft, or **Reject** to save nothing.

Check your Doc for a new entry and Gmail Drafts for a new draft.

---

## 7. Known limits

- Reviews under 5 words were removed, so the data does not represent the app's overall rating (33% one-star in the cleaned set is not the real average).
- Theme shares come from a random sample of 400 reviews. Fee shares come from a sample of 150 fee-related reviews that favours low ratings. They are not shares of all 2,439 reviews.
- Some groups are small (customer support and fees and charges are each roughly 35 reviews in the sample), so their percentages are rough.
- Only about 9 weeks of data from one period, so the pulse makes no claim about trends over time.
- The free-tier model can be busy or cut an answer short. Retries, a compact answer format and a repair step reduce this, but a rare failed run is possible.
- Mutual fund reviews are only 3.7% of the dataset, so the fee issue concerns trade charges, not mutual fund fees.
- Source pages are checked manually. The "Last checked" date must be refreshed if the pages change.
- The explainer is general information based on Groww's public pages. It is not investment advice and does not quote current rates.
- The n8n Cloud trial limits how long the live link works.

---

## 8. Repository contents

```
README.md                 this file
sources.md                source list (official URLs used and considered)
weekly_pulse.md           the weekly product pulse from the submitted run
doc_entry_snippet.md      the entry appended to the Google Doc
email_draft.md            the Gmail draft text
requirements.txt          Python packages for data collection
.gitignore                keeps secrets and local folders out of git
scrape_reviews.py         collects Google Play reviews
clean_reviews.py          cleans the reviews
data/sample_reviews.csv   sample of the cleaned reviews (the main input)
data/raw/                 full raw scrape and cleaned export
analysis/                 optional scripts and outputs used to find the fee issue
workflows/                exported n8n workflows (no secrets)
screenshots/              approval page, Doc entry, Gmail draft, MCP tool calls
```

The optional analysis scripts used to find the fee issue (`count_keywords.py`, `count_fee_topics.py`, `mf_issues.py`) and their outputs are under `analysis/`.
