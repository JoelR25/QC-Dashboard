# 6-Hour Simulation Playbook for Engineers

## 🎯 Mission: Build a Working Control Tower Demo by End of Day

**Target Audience**: Data Engineers executing this for the first time  
**Time Allocation**: 6 hours (with built-in buffer)  
**Tools Required**: Personal accounts only (FREE)  
**Output**: Functional dashboard ready for leadership demo

---

## ⏰ MASTER TIMELINE

| Time Slot | Activity | Deliverable | Can Fail? |
|-----------|----------|-------------|-----------|
| **0:00-0:45** | Setup & Install | Accounts created, tools installed | ❌ NO |
| **0:45-2:00** | Generate Data | CSV files with errors | ❌ NO |
| **2:00-3:00** | Validate Data | Quarantine table populated | ⚠️ YES (see backup) |
| **3:00-3:30** | Export Data | CSV safety net | ❌ NO |
| **3:30-4:45** | Build Dashboard | Power BI with visuals | ⚠️ YES (use backup) |
| **4:45-5:30** | Polish & Test | Final demo ready | ✅ Buffer time |
| **5:30-6:00** | Dry Run | Practice pitch | ✅ Buffer time |

**Critical Path**: 0:00 → 2:00 → 3:30 (If you have data by 3:30, you WILL succeed)

---

## 📅 HOUR-BY-HOUR BREAKDOWN

---

### ⏰ HOUR 1: SETUP (0:00 - 0:45)

#### ✅ Checkpoint: All tools installed and tested

#### Task 1.1: Databricks Community Edition (15 min)
**DO**:
1. Go to: https://community.cloud.databricks.com/
2. Click "Sign Up" (use personal email if work email blocks)
3. Verify email
4. Log in → Click "Create Cluster"
   - **Name**: `control-tower-demo`
   - **Runtime**: 13.3 LTS (default)
   - **Terminate after**: 120 minutes

**WAIT**: Cluster takes 3-5 minutes to start. **DO NOT SKIP THIS.**

**Verify**: Green circle next to cluster name

**Common Issues**:
- ❌ "Cluster won't start" → Refresh page, try again
- ❌ "No cluster option" → Make sure you're in Workspace, not Admin Console

---

#### Task 1.2: Power BI Desktop (15 min)
**DO**:
1. Go to: https://www.microsoft.com/en-us/download/details.aspx?id=58494
2. Download Power BI Desktop (free)
3. Install (default options, accept all prompts)
4. Launch Power BI Desktop
5. Click "Get Data" → "Blank Query" → Close (just testing it opens)

**Verify**: Power BI opens without errors

**Common Issues**:
- ❌ "Installation blocked" → Run as Administrator
- ❌ "Requires Windows 10" → Use a colleague's machine or cloud VM

---

#### Task 1.3: Python Environment (15 min)
**Local Setup** (for data generation):

**Option A: Anaconda (Recommended)**
```bash
# Download Anaconda from: https://www.anaconda.com/products/distribution
# Install, then:
conda create -n control-tower python=3.10
conda activate control-tower
pip install faker pandas numpy
```

**Option B: System Python**
```bash
# If you already have Python 3.8+
pip install faker pandas numpy
```

**Verify**:
```python
python -c "import faker, pandas, numpy; print('✅ Ready')"
```

**Common Issues**:
- ❌ "pip not found" → Install Python from python.org
- ❌ "Permission denied" → Use `pip install --user`

---

### ⏰ HOUR 2-3: GENERATE DATA (0:45 - 2:00)

#### ✅ Checkpoint: 3 CSV files created with visible errors

#### Task 2.1: Clone Repository (5 min)
```bash
cd ~/Desktop  # Or wherever you work
git clone https://github.com/JoelR25/QC-Dashboard.git
cd QC-Dashboard
```

**If Git Not Installed**: Download ZIP from GitHub, extract

---

#### Task 2.2: Generate Synthetic Data (10 min)
```bash
python scripts/01_generate_synthetic_data.py
```

**Expected Output**:
```
✅ Generated Product Master: 100 products
✅ Generated Store Master: 50 stores across 8 regions
✅ Generated Sales Transactions: 10,000 records
   📊 Error Injections:
      🔴 Orphan UPCs: 500 (5.0%)
         - Pattern UPC (999999001): 500 transactions
      🔴 Negative Sales: 100 (1.0%)
      🔴 Missing Stores: 200 (2.0%)
   ⚠️  Expected Trust Score: ~92.0%
```

**CRITICAL VERIFICATION**:
```bash
ls -lh data/bronze/
# Should see: sales_transactions.csv (~1.5 MB)

head -n 5 data/bronze/sales_transactions.csv
# Should see: Transaction_ID,UPC,Store_ID,Week_End,Units_Sold,Sales_Dollars,List_Price
```

**⚠️ FAIL CONDITION**: If Trust Score is 100% (no errors), **STOP**
```bash
# Regenerate with forced errors:
python scripts/01_generate_synthetic_data.py --force-errors
```

**Common Issues**:
- ❌ "No module named 'faker'" → Run `pip install faker pandas numpy`
- ❌ "Permission denied on data/" → Check folder exists, or create it

---

#### Task 2.3: Validate Data Quality (30 min)
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

**CRITICAL FILES CREATED**:
- `data/silver/sales_clean.csv`
- `data/quarantine/sales_quarantine.csv`
- `data/audit_log.csv`

**Verify Quarantine Has Errors**:
```bash
head data/quarantine/sales_quarantine.csv
# Look for "Error_Reason" column with values like "upc_exists, sales_positive"
```

**⚠️ FAIL CONDITION**: If quarantine file is empty
**FIX**: Check the validation script ran completely. Re-run if needed.

---

#### Task 2.4: Create Gold Layer (25 min)

**Option A: Local Python (Pandas)**
Create file: `scripts/03_create_gold_layer.py`

```python
import pandas as pd

# Load clean silver data
silver_clean = pd.read_csv('data/silver/sales_clean.csv')

# Join with master data for Brand and Region
product_master = pd.read_csv('data/master/product_master.csv')
store_master = pd.read_csv('data/master/store_master.csv')

# Merge
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
gold_brand_analytics = sales_enriched.groupby(['Brand', 'Region']).agg({
    'Sales_Dollars': 'sum',
    'Units_Sold': 'sum',
    'Transaction_ID': 'count'
}).reset_index()

gold_brand_analytics.columns = ['Brand', 'Region', 'Total_Revenue', 'Total_Units', 'Transaction_Count']

# Save
gold_brand_analytics.to_csv('data/gold/brand_analytics.csv', index=False)
print(f"✅ Gold layer created: {len(gold_brand_analytics)} rows")
```

**Run**:
```bash
python scripts/03_create_gold_layer.py
```

**Verify**:
```bash
head data/gold/brand_analytics.csv
# Should see aggregated data by Brand and Region
```

---

### ⏰ HOUR 4: EXPORT SAFETY NET (3:00 - 3:30)

#### ✅ Checkpoint: All data accessible for Power BI (even if Databricks fails)

#### Task 4.1: Prepare Power BI Data (10 min)

**Create Reconciliation Summary CSV** (simulates the reconciliation table):

Create file: `scripts/04_create_reconciliation_summary.py`

```python
import pandas as pd
from datetime import datetime, timedelta

# Get metrics from audit log
audit_log = pd.read_csv('data/audit_log.csv')

# Calculate week_end_date (last Saturday)
today = datetime.now()
days_since_saturday = (today.weekday() + 2) % 7
last_saturday = today - timedelta(days=days_since_saturday)
week_end = last_saturday.date()

# Create reconciliation entries for each layer
reconciliation = []

# Layer 1: Bronze (from audit log)
row = audit_log.iloc[0]
reconciliation.append({
    'product_name': 'Circana_Retail',
    'week_end_date': week_end,
    'layer_name': 'Bronze',
    'row_count_expected': row['input_rows'],
    'row_count_actual': row['input_rows'],
    'variance_pct': 0.0,
    'status': 'OK',
    'trust_score_pct': None
})

# Layer 2: Silver
reconciliation.append({
    'product_name': 'Circana_Retail',
    'week_end_date': week_end,
    'layer_name': 'Silver',
    'row_count_expected': row['input_rows'],
    'row_count_actual': row['valid_rows'] + row['quarantine_rows'],
    'variance_pct': 0.0,
    'status': 'WARNING' if row['trust_score_pct'] < 95 else 'OK',
    'trust_score_pct': row['trust_score_pct']
})

# Layer 3: Gold
gold_data = pd.read_csv('data/gold/brand_analytics.csv')
gold_revenue = gold_data['Total_Revenue'].sum()
silver_clean = pd.read_csv('data/silver/sales_clean.csv')
silver_revenue = silver_clean['Sales_Dollars'].sum()

reconciliation.append({
    'product_name': 'Circana_Retail',
    'week_end_date': week_end,
    'layer_name': 'Gold',
    'row_count_expected': int(silver_revenue),
    'row_count_actual': int(gold_revenue),
    'variance_pct': ((gold_revenue - silver_revenue) / silver_revenue * 100) if silver_revenue > 0 else 0,
    'status': 'OK',
    'trust_score_pct': None
})

reconciliation_df = pd.DataFrame(reconciliation)
reconciliation_df.to_csv('data/reconciliation_summary.csv', index=False)
print("✅ Reconciliation summary created")
```

**Run**:
```bash
python scripts/04_create_reconciliation_summary.py
```

---

#### Task 4.2: Verify All Files Exist (5 min)

**Checklist**:
```bash
ls -lh data/master/product_master.csv        # ✅ ~15 KB
ls -lh data/master/store_master.csv          # ✅ ~5 KB
ls -lh data/bronze/sales_transactions.csv    # ✅ ~1.5 MB
ls -lh data/silver/sales_clean.csv           # ✅ ~1.3 MB
ls -lh data/quarantine/sales_quarantine.csv  # ✅ ~150 KB (MUST have data)
ls -lh data/gold/brand_analytics.csv         # ✅ ~10 KB
ls -lh data/audit_log.csv                    # ✅ ~1 KB
ls -lh data/reconciliation_summary.csv       # ✅ ~1 KB
```

**⚠️ CRITICAL**: If `sales_quarantine.csv` is empty or < 10 KB, **regenerate data**.

---

#### Task 4.3: Backup to Cloud (Optional, 15 min)

**If you want to access data from anywhere**:

**Option A: Google Drive**
1. Upload `data/` folder to Google Drive
2. Share link with yourself

**Option B: GitHub (careful with file size)**
```bash
# Add data to .gitignore EXCEPT sample files
echo "!data/quarantine/sales_quarantine.csv" >> .gitignore
git add .
git commit -m "Add sample data for demo"
git push
```

---

### ⏰ HOUR 5-6: BUILD POWER BI DASHBOARD (3:30 - 4:45)

#### ✅ Checkpoint: Dashboard with Trust Score, Sankey, and Decomposition Tree

#### Task 5.1: Import Data into Power BI (15 min)

**Open Power BI Desktop**

1. **Get Data** → **Text/CSV**
2. Import files in this order:
   - `data/master/product_master.csv`
   - `data/master/store_master.csv`
   - `data/bronze/sales_transactions.csv` (optional, for comparison)
   - `data/silver/sales_clean.csv`
   - `data/quarantine/sales_quarantine.csv` ⚠️ **CRITICAL**
   - `data/gold/brand_analytics.csv`
   - `data/audit_log.csv`
   - `data/reconciliation_summary.csv`

3. Click **Load** (not Transform - use as-is)

**Verify**: All tables appear in Fields pane (right side)

---

#### Task 5.2: Create Data Model (10 min)

**Switch to Model View** (left sidebar, icon with three connected boxes)

**Create Relationships**:
1. Drag `sales_clean[UPC]` → `product_master[UPC]`
2. Drag `sales_clean[Store_ID]` → `store_master[Store_ID]`
3. Drag `sales_quarantine[UPC]` → `product_master[UPC]` (may be many-to-many, that's OK)
4. Drag `sales_quarantine[Store_ID]` → `store_master[Store_ID]`

**Verify**: Lines appear between tables

---

#### Task 5.3: Create DAX Measures (20 min)

**Right-click `audit_log` table** → **New Measure**

**Paste each measure**:

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

**Verify**: Measures appear under `audit_log` table with calculator icon

---

#### Task 5.4: Build Dashboard Visuals (40 min)

**Switch to Report View** (first icon on left sidebar)

**Page 1: Executive Dashboard**

**Visual 1: Trust Score Gauge** (5 min)
1. **Insert** → **Gauge**
2. **Value**: `[Trust Score %]`
3. **Target**: 100
4. **Format** → **Data colors** → Conditional formatting:
   - If value < 95 → Red
   - If value < 98 → Yellow
   - Else → Green
5. Resize to top-left (large and prominent)

**Visual 2: Revenue at Risk Card** (3 min)
1. **Insert** → **Card**
2. **Fields**: `[Revenue at Risk]`
3. **Format** → **Display units**: Auto
4. **Callout value** → **Font size**: 40
5. Position: Top-right

**Visual 3: Quarantine Rows Card** (3 min)
1. **Insert** → **Card**
2. **Fields**: `[Quarantine Rows]`
3. Format as above
4. Position: Next to Revenue at Risk

**Visual 4: Sankey Diagram** (15 min)

**⚠️ Requires Custom Visual**:
1. Click **...** (three dots) in Visualizations pane → **Get more visuals**
2. Search "Sankey"
3. Install "Sankey Diagram by OKViz" (free)

**Configure**:
1. Select Sankey visual
2. **Source**: Create calculated column in reconciliation_summary:
   ```
   Source Layer = 
   SWITCH(
       reconciliation_summary[layer_name],
       "Bronze", "ADLS Landing",
       "Silver", "Bronze",
       "Gold", "Silver Clean",
       "Unknown"
   )
   ```
3. **Destination**: `reconciliation_summary[layer_name]`
4. **Weight**: `reconciliation_summary[row_count_actual]`
5. **Format** → Colors: Bronze=Orange, Silver=Blue, Gold=Gold

**Visual 5: Decomposition Tree** (14 min)

**⚠️ Requires AI Visual**:
1. **Insert** → **Decomposition Tree** (built-in AI visual)
2. **Analyze**: `Quarantine Rows` (the measure)
3. **Explain by**: Drag these fields:
   - `sales_quarantine[Error_Reason]`
   - `store_master[Region]`
   - `product_master[Brand]`
   - `product_master[Category]`

4. Position: Bottom half of page (wide)

**Test Interaction**:
- Click on a segment → Tree auto-expands
- Click "+" to drill deeper
- This is your "wow" moment in the demo!

---

#### Task 5.5: Add Slicers (5 min)

1. **Insert** → **Slicer**
2. **Field**: `reconciliation_summary[week_end_date]`
3. Position: Top center
4. **Format** → **Slicer settings** → **Style**: Dropdown

---

### ⏰ HOUR 6: POLISH & DRY RUN (4:45 - 5:30)

#### Task 6.1: Add Text & Branding (15 min)

1. **Insert** → **Text Box**
2. Add title: "Data Quality Control Tower"
3. **Font**: Segoe UI, Size 28, Bold
4. Position: Top-left above Trust Score

Add descriptive text boxes:
- Above Sankey: "Data Flow: 10,000 rows entered, 9,200 clean, 800 quarantined"
- Above Decomposition Tree: "Click to drill down into error root causes"

**Add Company Logo** (if available):
1. **Insert** → **Image**
2. Upload logo
3. Position: Top-right corner

---

#### Task 6.2: Test All Interactions (15 min)

**Test Checklist**:
- [ ] Trust Score shows a value < 100% (ideally ~92%)
- [ ] Revenue at Risk shows a dollar amount
- [ ] Sankey diagram shows flow with visible quarantine stream
- [ ] Decomposition Tree expands when clicked
- [ ] Week slicer filters all visuals
- [ ] No error messages or blank visuals

**If ANY visual is blank**: Check the data source, verify CSV files loaded correctly

---

#### Task 6.3: Save & Backup (5 min)

1. **File** → **Save As**
2. Name: `ControlTower_Demo_YYYYMMDD.pbix`
3. Save to Desktop AND cloud (OneDrive/Google Drive)

**Create PDF Export**:
1. **File** → **Export to PDF**
2. Save as `ControlTower_Dashboard.pdf` (for email attachments)

---

#### Task 6.4: Dry Run Presentation (10 min)

**Practice the 15-minute pitch**:
1. Start Power BI in Presentation Mode (F5)
2. Walk through:
   - Hook: Point to red Trust Score
   - Impact: Point to Revenue at Risk
   - Flow: Explain Sankey
   - Root Cause: Click through Decomposition Tree
3. Time yourself (should be 10-12 minutes, leaving room for questions)

**Record Issues**:
- Visual loads slowly? → Use Import mode, not DirectQuery
- Can't explain a metric? → Review DAX formulas
- Decomposition Tree doesn't drill? → Check field hierarchy

---

### ⏰ BUFFER TIME (5:30 - 6:00)

**Use this for**:
- Fixing any issues from dry run
- Creating backup slides (export dashboard pages as images)
- Rehearsing objection handling
- Setting up screen sharing for virtual demo
- **Taking a break** - you earned it!

---

## 🚨 FAILURE RECOVERY PROCEDURES

### Scenario 1: "Data has no errors (100% Trust Score)"
**Problem**: Generator created perfect data, no quarantine records

**Fix** (10 min):
```python
# Force errors in sales_transactions.csv
import pandas as pd

df = pd.read_csv('data/bronze/sales_transactions.csv')

# Force 500 orphan UPCs
df.loc[:500, 'UPC'] = '999999001'

# Force 100 negative sales
df.loc[501:600, 'Sales_Dollars'] = df.loc[501:600, 'Sales_Dollars'] * -1

# Force 200 missing stores
df.loc[601:800, 'Store_ID'] = 'STORE_999'

df.to_csv('data/bronze/sales_transactions.csv', index=False)
print("✅ Errors injected manually")

# Re-run validation
python scripts/02_validate_data_quality.py
```

---

### Scenario 2: "Power BI won't connect to Databricks"
**Problem**: Community Edition connectivity issues

**Fix**: **You already have CSV backups!**
- Just use the CSV files from `data/` folder
- This is why we created the safety net in Hour 4
- Demo works identically with CSVs vs. live connection

---

### Scenario 3: "Decomposition Tree is blank"
**Problem**: No data in quarantine table or wrong fields

**Fix** (5 min):
1. Verify `sales_quarantine.csv` has data: `head data/quarantine/sales_quarantine.csv`
2. In Power BI, **Refresh** data: Home → Refresh
3. Check Decomposition Tree fields:
   - **Analyze** must be a measure (like `[Quarantine Rows]`)
   - **Explain by** must be dimension fields (like `Error_Reason`)

---

### Scenario 4: "Sankey Diagram won't install"
**Problem**: Power BI App Source blocked by IT

**Fix**: **Use Waterfall Chart instead**
1. **Insert** → **Waterfall Chart**
2. **Category**: `reconciliation_summary[layer_name]`
3. **Y-axis**: `reconciliation_summary[row_count_actual]`
4. Not as pretty, but shows the same flow concept

---

### Scenario 5: "Running out of time!"
**Minimum Viable Demo** (if at Hour 5 with only 30 min left):

**Skip**:
- Gold layer (use Silver directly)
- Sankey diagram (use simple bar chart)
- Fancy formatting

**MUST HAVE**:
- Trust Score gauge (red/yellow/green)
- Revenue at Risk card
- Table of quarantine records (sortable by Error_Reason)

This is still enough for a convincing demo!

---

## ✅ FINAL PRE-DEMO CHECKLIST

**30 Minutes Before the Meeting**:
- [ ] Power BI file opens without errors
- [ ] Trust Score is visible and RED (< 95%)
- [ ] Quarantine table has data (at least 500 rows)
- [ ] Decomposition Tree expands when clicked
- [ ] You can explain each visual in < 1 minute
- [ ] Pitch deck script is open on second monitor
- [ ] Screen sharing tested (Teams/Zoom)
- [ ] Phone on silent
- [ ] Water bottle nearby
- [ ] You've practiced the "Money Line": 
   > "This went from 'something's wrong' to 'exactly what and who fixes it' in three clicks."

---

## 🎉 POST-DEMO ACTIONS

**If Demo Went Well**:
1. Send follow-up email within 1 hour (template in executive_pitch_outline.md)
2. Share .pbix file and PDF export
3. Offer 1-on-1 walkthrough to interested stakeholders
4. Document any questions you couldn't answer
5. Update this playbook with lessons learned

**If Demo Had Issues**:
1. Don't panic - note what failed
2. Follow up with corrected version: "Here's the visual that didn't load..."
3. Offer to re-demo in smaller group
4. Use it as a learning opportunity: "This is why we need production environment"

---

## 📞 EMERGENCY CONTACTS (If You Get Stuck)

**Databricks Community Support**: https://community.databricks.com/  
**Power BI Community**: https://community.powerbi.com/  
**Stack Overflow**: Tag questions with `databricks` or `powerbi`

**Internal**: Tag your senior data engineer or BI analyst

**Remember**: The goal is to SHOW THE CONCEPT, not perfection. Even a partially working demo proves the value!

---

**Good luck! You've got this! 🚀**

