# ⚡ QUICK START - 6-Hour Demo Execution Guide

## 🎯 Your Mission Today

Build a working **Data Quality Control Tower** dashboard that:
- Shows a **Trust Score** in RED (~92%)
- Demonstrates **Quarantine Pattern** with real data errors
- Enables **Root Cause Drill-Down** (3 clicks to find the problem)
- Convinces leadership to fund the production build

**Time Available**: 6 hours  
**Cost**: $0 (all free tools)  
**Difficulty**: Intermediate

---

## 📋 Pre-Flight Checklist (Before You Start)

### Required Accounts (All FREE)
- [ ] **Databricks Community Edition** - https://community.cloud.databricks.com/ (OPTIONAL, can skip)
- [ ] **Power BI Desktop** - Download from Microsoft (REQUIRED)
- [ ] **GitHub Account** - To clone this repo (or download ZIP)

### Required Software
- [ ] **Python 3.8+** - Check: `python --version`
- [ ] **Git** - Check: `git --version` (or download ZIP)
- [ ] **Text Editor** - VS Code, Sublime, or Notepad++

### Mental Prep
- [ ] Calendar blocked for 6 hours (minimize interruptions)
- [ ] Coffee/water nearby
- [ ] Backup demo time scheduled (in case you need it)

---

## ⏱️ THE 6-HOUR SPRINT

### HOUR 1: Setup (0:00 - 1:00)

**📥 Step 1: Get the Code** (5 min)
```bash
# Option A: Clone with Git
git clone https://github.com/JoelR25/QC-Dashboard.git
cd QC-Dashboard

# Option B: Download ZIP
# Download from GitHub → Extract → Open folder in terminal
```

**🐍 Step 2: Install Python Dependencies** (10 min)
```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

**✅ Verify**: Run `python -c "import faker, pandas, numpy; print('✅ Ready')"`

**📊 Step 3: Install Power BI Desktop** (30 min)
1. Download: https://aka.ms/pbidesktopstore
2. Install with default options
3. Launch once to verify it opens

**✅ Verify**: Power BI Desktop opens without errors

**🗂️ Step 4: Create Data Directories** (5 min)
```bash
# Already done by git, but verify:
ls data/
# Should see: bronze/ silver/ gold/ master/ quarantine/
```

**Buffer**: 10 minutes for unexpected issues

---

### HOUR 2: Generate Data (1:00 - 2:00)

**🎲 Step 1: Generate Synthetic Data** (10 min)
```bash
python scripts/01_generate_synthetic_data.py
```

**Expected Output**:
```
✅ Generated Product Master: 100 products
✅ Generated Store Master: 50 stores
✅ Generated Sales Transactions: 10,000 records
   📊 Error Injections:
      🔴 Orphan UPCs: 500 (5.0%)
      🔴 Negative Sales: 100 (1.0%)
      🔴 Missing Stores: 200 (2.0%)
   ⚠️  Expected Trust Score: ~92.0%
```

**🚨 CRITICAL CHECK**: Trust Score must be < 98%  
If 100%, see troubleshooting.md → Issue 1

**✅ Verify**:
```bash
ls -lh data/bronze/sales_transactions.csv  # Should be ~1.5 MB
head data/bronze/sales_transactions.csv    # Should see transaction data
```

**🛡️ Step 2: Run Quality Validation** (20 min)
```bash
python scripts/02_validate_data_quality.py
```

**Expected Output**:
```
📊 Data Quality Metrics - Batch 1
════════════════════════════════════════════
   Input Rows:       10,000
   ✅ Valid Rows:     9,200 (92.0%)
   ⚠️  Quarantine:     800 (8.0%)
   🎯 Trust Score:    92.00%
════════════════════════════════════════════
```

**🚨 CRITICAL CHECK**: Quarantine file must have data  
```bash
wc -l data/quarantine/sales_quarantine.csv
# Should show ~800 lines (plus header)
```

**✅ Verify**:
```bash
head data/quarantine/sales_quarantine.csv
# Should see Error_Reason column with values like "upc_exists"
```

**📊 Step 3: Create Gold Layer** (15 min)

Create file: `scripts/03_create_gold_layer.py`
```python
import pandas as pd

# Load data
silver_clean = pd.read_csv('data/silver/sales_clean.csv')
product_master = pd.read_csv('data/master/product_master.csv')
store_master = pd.read_csv('data/master/store_master.csv')

# Merge to enrich
sales_enriched = silver_clean.merge(
    product_master[['UPC', 'Brand', 'Category']], 
    on='UPC', 
    how='left'
).merge(
    store_master[['Store_ID', 'Region']], 
    on='Store_ID', 
    how='left'
)

# Aggregate
gold = sales_enriched.groupby(['Brand', 'Region']).agg({
    'Sales_Dollars': 'sum',
    'Units_Sold': 'sum',
    'Transaction_ID': 'count'
}).reset_index()

gold.columns = ['Brand', 'Region', 'Total_Revenue', 'Total_Units', 'Transaction_Count']

# Save
gold.to_csv('data/gold/brand_analytics.csv', index=False)
print(f"✅ Gold layer created: {len(gold)} rows")
```

Run: `python scripts/03_create_gold_layer.py`

**Buffer**: 15 minutes

---

### HOUR 3: Build Dashboard Part 1 (2:00 - 3:00)

**📂 Step 1: Import Data into Power BI** (15 min)

1. Open Power BI Desktop
2. Click **Get Data** → **Text/CSV**
3. Import files (in order):
   - `data/master/product_master.csv`
   - `data/master/store_master.csv`
   - `data/silver/sales_clean.csv`
   - `data/quarantine/sales_quarantine.csv` ⚠️ **CRITICAL**
   - `data/gold/brand_analytics.csv`
   - `data/audit_log.csv`
4. Click **Load** (NOT Transform)

**✅ Verify**: All 6 tables appear in Fields pane (right side)

**🔗 Step 2: Create Relationships** (10 min)

Click **Model** view (left sidebar, 3rd icon)

Create relationships (drag lines):
- `sales_clean[UPC]` → `product_master[UPC]`
- `sales_clean[Store_ID]` → `store_master[Store_ID]`
- `sales_quarantine[UPC]` → `product_master[UPC]`
- `sales_quarantine[Store_ID]` → `store_master[Store_ID]`

**📐 Step 3: Create DAX Measures** (25 min)

Click **Report** view. Right-click `audit_log` → **New Measure**

**Paste these (one at a time)**:

```dax
Trust Score % = 
DIVIDE(
    SUM(audit_log[valid_rows]),
    SUM(audit_log[input_rows]),
    0
) * 100
```

```dax
Quarantine Rows = SUM(audit_log[quarantine_rows])
```

```dax
Revenue at Risk = 
SUMX(
    sales_quarantine,
    ABS(sales_quarantine[Sales_Dollars])
)
```

```dax
Trust Score Color = 
SWITCH(
    TRUE(),
    [Trust Score %] >= 98, "Green",
    [Trust Score %] >= 95, "Yellow",
    "Red"
)
```

**✅ Verify**: Measures appear under `audit_log` with calculator icon (fx)

**Buffer**: 10 minutes

---

### HOUR 4: Build Dashboard Part 2 (3:00 - 4:00)

**📊 Step 1: Create Trust Score Gauge** (10 min)

1. Click blank canvas
2. **Visualizations** pane → Click **Gauge**
3. **Value**: Drag `[Trust Score %]` measure
4. **Target**: Type 100 manually
5. **Format** visual → **Data colors**:
   - Minimum: Red (#FF0000)
   - Center: Yellow (#FFC000) at 95
   - Maximum: Green (#00B050) at 100
6. Resize to top-left (make it BIG)

**🎯 Step 2: Create Revenue at Risk Card** (5 min)

1. **Visualizations** → Click **Card**
2. **Fields**: Drag `[Revenue at Risk]` measure
3. **Format** → **Callout value** → Font size: 40
4. Position: Top-right

**📇 Step 3: Create Quarantine Table** (10 min)

1. **Visualizations** → Click **Table**
2. **Columns** (drag from `sales_quarantine`):
   - `UPC`
   - `Store_ID`
   - `Sales_Dollars`
   - `Error_Reason`
3. Position: Middle of page
4. **Format** → Enable **Column sorting**

**🌳 Step 4: Create Decomposition Tree** (20 min)

**⚠️ This is your demo "wow" moment!**

1. **Visualizations** → Click **Decomposition Tree** (AI visual, tree icon)
2. **Analyze**: Drag the MEASURE `[Quarantine Rows]` (NOT a column!)
3. **Explain by**: Drag these fields IN ORDER:
   - `sales_quarantine[Error_Reason]` (FIRST - most important)
   - `store_master[Region]`
   - `product_master[Brand]`
   - `product_master[Category]`
4. Position: Bottom half (wide)

**Test Interaction**:
- Click on the visual
- Click "Error_Reason" → Should expand to show error types
- Click "+" next to an error → Should drill to Region
- Click "+" again → Should drill to Brand

**🚨 If blank**: See troubleshooting.md → Issue 4

**Buffer**: 15 minutes

---

### HOUR 5: Polish & Test (4:00 - 5:00)

**🎨 Step 1: Add Branding** (15 min)

1. **Insert** → **Text Box**
2. Type: "Data Quality Control Tower"
3. **Home** → Font: Segoe UI, Size: 28, Bold
4. Position: Top-left above gauge

Add descriptive labels:
- Above Quarantine Table: "Invalid Records Caught Before Reporting"
- Above Decomposition Tree: "Click to drill down into root causes →"

**🧪 Step 2: Test All Interactions** (20 min)

**Checklist**:
- [ ] Trust Score shows ~92% (RED)
- [ ] Revenue at Risk shows a dollar value (e.g., $50,000)
- [ ] Quarantine Table has 800 rows
- [ ] Decomposition Tree expands on click
- [ ] Can drill: Error_Reason → Region → Brand
- [ ] No blank visuals or errors

**If ANY fails**: Pause, check troubleshooting.md, fix before proceeding

**💾 Step 3: Save Everything** (10 min)

1. **File** → **Save As**
2. Name: `ControlTower_Demo_[TODAY'S DATE].pbix`
3. Save to Desktop AND cloud backup

**Create PDF backup**:
- **File** → **Export to PDF**
- Save as `ControlTower_Dashboard.pdf`

**🔄 Step 4: Refresh Test** (5 min)

1. Click **Home** → **Refresh**
2. Verify all visuals update without errors
3. If any errors: Note them, check data sources

**Buffer**: 10 minutes

---

### HOUR 6: Dry Run & Prep (5:00 - 6:00)

**🎭 Step 1: Practice the Pitch** (30 min)

Open: `docs/executive_pitch_outline.md`

**Practice these key moments** (out loud!):

1. **The Hook** (30 seconds):
   - Point to RED Trust Score
   - Say: "See this? 94%. It's red. This tells you not to make a decision yet."

2. **The Impact** (30 seconds):
   - Point to Revenue at Risk
   - Say: "$50,000 in unattributed sales. That's the financial impact of this quality issue."

3. **The Wow** (2 minutes):
   - Click on Decomposition Tree
   - Drill down: Error Type → Region → Brand
   - Say: "In three clicks, I went from 'something's wrong' to 'exactly what and who fixes it.'"

**Time yourself**: Should be 10-12 minutes (leaves room for questions)

**📸 Step 2: Create Backup Screenshots** (10 min)

In case Power BI crashes during demo:

1. Take screenshot of each visual
2. Save to folder: `demo_backups/`
3. Have image viewer ready to show if needed

**🖥️ Step 3: Test Screen Share** (10 min)

If virtual demo:
1. Open Zoom/Teams
2. Start screen share
3. Share Power BI window (full screen)
4. Verify:
   - Visuals are readable
   - Mouse cursor visible
   - No personal info exposed (taskbar, notifications)

**📋 Step 4: Final Checks** (5 min)

- [ ] Power BI file opens cleanly
- [ ] Trust Score is visible and RED
- [ ] Can click through Decomposition Tree
- [ ] Backup PDF ready
- [ ] Pitch outline open on second monitor
- [ ] Phone on silent
- [ ] Water bottle nearby

**🧘 Step 5: Relax** (5 min)

You did it! Take a break. You're ready.

---

## 🎤 Demo Day: The 15-Minute Pitch

### Opening (0:00 - 2:30): The Problem
Show blurred dashboard image (or black screen)

> "We make million-dollar decisions based on Circana data. But we have a blindspot. Our current monitoring tells us if the pipeline ran, not if the data is correct. Last quarter, this cost us $200,000 when data for a new product was silently dropped."

### Setup (2:30 - 5:00): The Solution
Show architecture diagram (from `docs/architecture_diagrams.md`)

> "We're proposing a Data Quality Control Tower. Three innovations: **Quarantine Pattern** (catch bad data), **Trust Score** (measure quality), and **Root Cause Drill-Down** (find exactly what's wrong)."

### Demo (5:00 - 12:00): Show It Live
**Switch to Power BI** (F5 for presentation mode)

**Part 1: The Hook** (1 min)
- Point to Trust Score gauge (RED)
- "94%. This tells you: don't make decisions yet."

**Part 2: The Impact** (1 min)
- Point to Revenue at Risk
- "$50,000 in unattributed sales."

**Part 3: The Flow** (2 min - SKIP IF RUNNING LATE)
- Point to Sankey (if you built it) or Quarantine Table
- "6,000 rows caught before reaching user reports."

**Part 4: The Wow** (3 min)
- Click Decomposition Tree
- Drill: Error Type → Region → Brand
- "Three clicks to find the root cause. The commercial team launched 'Summer Seltzer' but forgot to add it to Product Master. I know exactly who to call."

### Close (12:00 - 15:00): The Ask
Show comparison slide (Current vs. Target State)

> "I built this proof of concept in 6 hours on a personal account. To scale this, I need approval to implement in our production Databricks environment. Investment: 2 weeks, 1 engineer. ROI: 40% time savings, prevent $200K+ mistakes. This shifts us from reactive to proactive data governance."

**Pause for questions.**

---

## 🆘 Emergency Contacts

**Stuck? Check**:
1. `docs/troubleshooting.md` - Most common issues
2. `docs/6_hour_engineer_playbook.md` - Detailed steps
3. GitHub Issues - Report problems

**Still Stuck?**:
- Power BI Community: https://community.powerbi.com/
- Stack Overflow: Tag `powerbi` or `databricks`
- Your team's senior data engineer

---

## 🎉 Post-Demo

**If Demo Went Well**:
1. ✅ Send follow-up email within 1 hour (template in `docs/executive_pitch_outline.md`)
2. ✅ Share .pbix file and PDF export
3. ✅ Schedule follow-up meeting to discuss next steps
4. ✅ Update this repo with lessons learned

**If Demo Had Issues**:
1. Don't panic - leadership cares about the concept, not perfection
2. Send corrected version later: "Here's the visual that didn't load..."
3. Offer to re-demo in smaller group
4. Frame it as: "This is why we need production environment - Community Edition has limits"

---

## 🚀 Next Steps (After Approval)

1. Review `docs/enterprise_reconciliation_framework.md`
2. Follow 4-week implementation roadmap
3. Use `notebooks/03_reconciliation_engine.py` as template
4. Deploy to production Azure Databricks
5. Publish Power BI App to organization

---

## 💪 You've Got This!

**Remember**:
- The goal is to show VALUE, not perfection
- Even a partially working demo proves the concept
- Leadership cares about ROI, not technical details
- **You're solving a $200K problem - that's huge!**

**Good luck! 🚀**

---

**Questions?** Open an issue on GitHub or tag your senior data engineer.

**Feedback?** Please update this guide with any improvements!
