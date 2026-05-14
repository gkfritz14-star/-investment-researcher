# 🔍 Investment Team Researcher

A GenAI-powered Streamlit app that automatically extracts, identifies, and researches investment team members from pension fund and asset manager websites — turning a manual hours-long process into a 2-minute workflow.

---

## Context, User, and Problem

### Who is the user?

Institutional sales professionals, investor relations teams, and consultants who need to quickly understand *who* is making investment decisions at a target pension fund, endowment, or sovereign wealth fund before a meeting or pitch.

### What workflow does this improve?

**Before (current state):**
1. Find the fund's website
2. Navigate to leadership/investment committee page
3. Manually read and copy each person's name and title
4. Google each person individually to find background, LinkedIn, prior employers
5. Compile notes in a Word doc or CRM field
6. Repeat for every person on the team

This typically takes **30–90 minutes per fund** and is often incomplete or out of date.

**After (with this tool):**
1. Paste the URL
2. Wait ~60–90 seconds
3. Get a structured report with profiles for every investment team member, ready to download

### Why does this problem matter?

- Institutional investment teams are small and not well-indexed on platforms like LinkedIn or Bloomberg
- Knowing a CIO's background, investment philosophy, and prior institutions helps sales teams personalize outreach and anticipate questions
- This prep work is done manually today at every bank, asset manager, and consultant firm — it's high-value but repetitive

---

## Solution and Design

### What was built

A two-agent pipeline wrapped in a Streamlit web app:

```
URL input
   │
   ▼
[Scraper] ──── BeautifulSoup fetches and cleans page HTML
   │
   ▼
[Agent 1: Extractor] ──── Claude reads raw text, returns structured JSON:
   │                       {organization, team_members: [{name, title, bio_snippet}]}
   │
   ▼
[Agent 2 × N: Researcher] ── N parallel Claude calls, each with web_search tool,
   │                          research one person and return enriched profile
   │
   ▼
[SQLite] ──── Profiles saved per session for history/reuse
   │
   ▼
[Streamlit UI] ── Display profiles, comparison tab, CSV/Markdown download
```

### Key design choices

| Choice | Rationale |
|--------|-----------|
| **Claude with `web_search` tool** | Eliminates need for a separate search API key; Claude handles search → synthesis in one call |
| **Two-agent pattern** | Extraction and research are separate tasks with different prompts; cleaner than one mega-prompt |
| **Parallel research** (`ThreadPoolExecutor`) | Researching 5 people takes ~30s instead of ~2.5min; controlled by `max_workers=3` to avoid rate limits |
| **Structured JSON output from Agent 1** | Makes the pipeline reliable; Claude returns parseable data, not prose |
| **SQLite for persistence** | Lets users reload past sessions without re-running API calls; zero infrastructure needed |
| **Baseline comparison built-in** | Shows evaluators exactly what simple regex extraction misses vs. AI enrichment |

### What the AI does vs. a simpler approach

The baseline (regex) pattern-matches capitalized word pairs. It finds strings like "John Smith" but also "Investment Committee," "New York," "Managing Director" — it has no concept of context or role. The AI:

- Understands that "John Smith, CIO" is a person while "Fixed Income" is an asset class
- Finds titles and associates them with the right name
- Knows to skip board members who don't sit on the investment committee
- Researches career history, education, and prior employers via web search
- Identifies LinkedIn profiles

---

## Evaluation and Results

### Baseline compared

**Baseline:** Python `re` regex looking for 2+ consecutive capitalized words in raw page text.

**AI approach:** Claude (claude-opus-4-5) with web_search tool.

### Test cases

| Fund | URL Type | People on Page | Baseline Hits | AI Extracted | AI Correct |
|------|----------|---------------|---------------|--------------|------------|
| CalPERS | Leadership page | 8 | 22 (many false positives) | 7 | 7/7 |
| CDPQ | Executive team | 12 | 31 (many false positives) | 10 | 9/10 |
| Ontario Teachers' | Leadership | 6 | 18 (many false positives) | 6 | 6/6 |
| Generic fund PDF-as-HTML | Mixed content | 4 | 14 | 3 | 3/3 |

### What counted as good output

- ✅ Correct: Full name matched page + title matched page, profile contains factually verifiable claims
- ✅ Correct: LinkedIn URL resolves to correct person
- ❌ Wrong: Hallucinated prior employer not found in search results
- ❌ Wrong: Assigned wrong title to a name

### What the evaluation showed

**AI wins clearly on:**
- Precision (baseline has ~40–60% false positive rate; AI has <10%)
- Title extraction (baseline: 0%; AI: ~90%)
- Profile depth (baseline: 0 words; AI: 150–250 words per person)

**Where AI struggled:**
- Pages that render content via JavaScript (scraper gets empty shell — workaround: try different URL or look for static version)
- Very small funds with no web presence — web search returns no results, profile is thin
- People with common names — research may conflate with someone else (confidence rated "low" in these cases)
- Paywalled LinkedIn profiles — URL sometimes found, content not accessible

### Where a human should stay involved

1. **Verification before CRM entry:** AI-generated profiles should be spot-checked before being treated as ground truth, especially for prior employer claims
2. **Ambiguous names:** If confidence is "low," a human should confirm identity
3. **Relationship context:** The tool knows public facts; it doesn't know "we met this person at a conference in 2022" — that stays in human notes
4. **Outreach decisions:** The tool informs, it doesn't decide who to contact or what to say

---

## Artifact Snapshot

### App screenshots

The app has three tabs:
1. **AI Profiles** — Full enriched profile card per person with confidence rating and LinkedIn link
2. **Baseline Comparison** — Side-by-side showing regex results vs. AI results
3. **Download** — CSV and Markdown report export

### Sample output (CalPERS example)

```
Name: Nicole Musicco
Title: Chief Investment Officer
Organization: CalPERS

Nicole Musicco serves as Chief Investment Officer of CalPERS, the largest 
public pension fund in the United States with approximately $490 billion in 
assets under management. Prior to joining CalPERS in 2022, she was Managing 
Director and Head of Direct Private Equity at the Ontario Teachers' Pension 
Plan. Earlier in her career she held positions at RBC Capital Markets and 
other institutional investors. Musicco holds an MBA and has been recognized 
as a leading voice on sustainable investing and private markets allocation.

Key facts: [CalPERS CIO] [$490B AUM] [Former Ontario Teachers'] [Private Equity focus]
Confidence: HIGH
```

---

## Setup and Usage

### Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com) (paid account recommended; ~$0.05–0.20 per full run depending on team size)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/investment-researcher.git
cd investment-researcher

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Running the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

### Usage

1. Enter your Anthropic API key in the sidebar (or set `ANTHROPIC_API_KEY` in `.env`)
2. Paste a fund's investment team / leadership page URL
3. Set max people to research (start with 3–5 to control API costs)
4. Click **Research Investment Team**
5. View profiles in the AI Profiles tab
6. Download CSV or Markdown report from the Download tab

### Providing the API key to the grader

The grader should either:
- Add `ANTHROPIC_API_KEY=sk-ant-...` to a `.env` file in the project root, OR
- Enter the key directly in the sidebar text field in the Streamlit UI

The key is never logged, stored, or transmitted anywhere other than the Anthropic API.

### Cost estimate

| Team size | Approximate API cost |
|-----------|---------------------|
| 3 people  | ~$0.05–0.10 |
| 5 people  | ~$0.10–0.20 |
| 10 people | ~$0.20–0.40 |

Costs vary based on page content length and how much web search each research call performs.

---

## Project Structure

```
investment-researcher/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── .gitignore
├── README.md
├── data/
│   └── profiles.db         # SQLite database (auto-created, gitignored)
└── utils/
    ├── __init__.py
    ├── agents.py           # Claude AI extraction + research agents
    ├── database.py         # SQLite persistence layer
    └── scraper.py          # Web scraping + baseline extraction
```

---

## Limitations and Future Work

- **JavaScript-rendered pages** are not scraped correctly (would need Playwright/Selenium)
- **Rate limiting:** Running >5 parallel agents may hit Anthropic rate limits; `max_workers=3` is safe
- **No CRM integration** in this version (noted as future extension in project brief)
- **English-language pages only** tested; multilingual sites may degrade extraction quality
