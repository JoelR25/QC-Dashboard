# Troubleshooting Guide - Data Quality Control Tower

## 🆘 Common Issues & Quick Fixes

This guide covers the most common issues you'll encounter during the 6-hour simulation and how to fix them FAST.

---

## 🔴 CRITICAL ISSUES (Demo Stoppers)

### Issue 1: Trust Score is 100% (No Errors Generated)

**Symptoms**:
- Quarantine table is empty
- Trust Score shows 100%
- Demo has no "wow" moment

**Cause**: Random seed didn't generate errors OR validation script didn't run

**Fix** (5 minutes):
```python
# Manually inject errors into sales_transactions.csv
import pandas as pd

df = pd.read_csv('data/bronze/sales_transactions.csv')

# Force specific errors for pattern detection
df.loc[:500, 'UPC'] = '999999001'  # Orphan UPC
df.loc[501:600, 'Sales_Dollars'] = df.loc[501:600, 'Sales_Dollars'] * -1  # Negative
df.loc[601:800, 'Store_ID'] = 'STORE_999'  # Missing store

df.to_csv('data/bronze/sales_transactions.csv', index=False)

# Re-run validation
python scripts/02_validate_data_quality.py
```

**Verify Fix**:
```bash
wc -l data/quarantine/sales_quarantine.csv
# Should show ~800 lines (plus header)
```

---

### Issue 2: Power BI Visuals Are Blank

**Symptoms**:
- Dashboard loads but visuals show "(Blank)"
- No data appears in tables

**Cause**: Data didn't import OR relationships are broken

**Fix (Option A): Refresh Data** (2 minutes):
1. In Power BI Desktop, click **Home** → **Refresh**
2. Wait for refresh to complete
3. Check if visuals populate

**Fix (Option B): Re-import Data** (5 minutes):
1. Click **Home** → **Transform Data**
2. Right-click each query → **Refresh Preview**
3. Click **Close & Apply**

**Fix (Option C): Check File Paths** (3 minutes):
1. **Home** → **Transform Data** → **Data Source Settings**
2. Verify paths point to correct CSV files
3. Click **Change Source** to update paths if needed

**Verify Fix**:
- Click on `sales_quarantine` table in Fields pane
- Should see row count (e.g., "800 rows loaded")

---

### Issue 3: Databricks Cluster Won't Start

**Symptoms**:
- Cluster stuck in "Pending" for > 10 minutes
- Error: "Cluster failed to start"

**Cause**: Community Edition capacity limit OR account issue

**Fix (Option A): Wait and Retry** (5 minutes):
1. Terminate the cluster
2. Wait 2 minutes
3. Start again

**Fix (Option B): Create New Cluster** (3 minutes):
1. Click "Create Cluster" (new one)
2. Use different name: `control-tower-demo-v2`
3. Select Runtime 13.3 LTS
4. Start

**Workaround**: **You don't actually need Databricks for the demo!**
- The CSV safety net is enough
- Skip Databricks entirely if issues persist
- Demo works with just Power BI + local CSVs

---

### Issue 4: Decomposition Tree Won't Drill Down

**Symptoms**:
- Decomposition Tree appears but is blank
- Clicking "+" does nothing

**Cause**: Wrong field types OR no quarantine data

**Fix (Step 1): Verify Data** (2 minutes):
```bash
head -n 10 data/quarantine/sales_quarantine.csv
```
- Ensure `Error_Reason` column has values
- Ensure file has > 100 rows

**Fix (Step 2): Check Field Types** (3 minutes):
1. In Power BI, click **Data** view (left sidebar)
2. Click on `sales_quarantine` table
3. Verify column types:
   - `Error_Reason`: Text (ABC icon)
   - `Sales_Dollars`: Decimal (123.45 icon)
   - If wrong, click column → **Transform** → **Data Type** → Change

**Fix (Step 3): Rebuild Visual** (5 minutes):
1. Delete the Decomposition Tree
2. **Insert** → **Decomposition Tree** (fresh start)
3. **Analyze**: Select the MEASURE `[Quarantine Rows]` (NOT a column)
4. **Explain by**: Drag `sales_quarantine[Error_Reason]` FIRST
5. Test by clicking the visual

**Alternative**: Use a **Table** visual instead
- Shows quarantine records sortable by Error_Reason
- Less fancy, but still effective for demo

---

## ⚠️ WARNING ISSUES (Not Demo Stoppers)

### Issue 5: Data Generation is Slow

**Symptoms**:
- `01_generate_synthetic_data.py` takes > 10 minutes

**Cause**: Large transaction count OR slow machine

**Fix**: **Reduce transaction count** (1 minute):

Edit `scripts/01_generate_synthetic_data.py`:
```python
# Change this line:
num_transactions=10000  # Original
# To:
num_transactions=5000  # Faster generation
```

**Impact**: Smaller dataset, but demo still works fine

---

### Issue 6: File Not Found Errors

**Symptoms**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/master/product_master.csv'
```

**Cause**: Working directory is wrong OR data not generated

**Fix (Step 1): Check Location** (1 minute):
```bash
pwd
# Should be in: .../QC-Dashboard/
ls data/master/
# Should see: product_master.csv, store_master.csv
```

**Fix (Step 2): Change Directory**:
```bash
cd /path/to/QC-Dashboard/
python scripts/01_generate_synthetic_data.py
```

**Fix (Step 3): Create Missing Directories**:
```bash
mkdir -p data/master data/bronze data/silver data/quarantine data/gold
```

---

### Issue 7: Power BI Can't Open .pbix File

**Symptoms**:
- "This file was created with a newer version of Power BI"

**Cause**: Version mismatch

**Fix**: **Update Power BI Desktop** (10 minutes):
1. Uninstall current version
2. Download latest from: https://aka.ms/pbidesktopstore
3. Install and retry

**Workaround**: Start with blank .pbix
- Rebuild dashboard from scratch using this guide
- Takes 30-40 minutes, but you'll understand it better

---

### Issue 8: Sankey Diagram Custom Visual Won't Install

**Symptoms**:
- "Can't connect to AppSource" OR IT policy blocks downloads

**Cause**: Corporate firewall OR Power BI restrictions

**Fix (Option A): Use Waterfall Chart** (5 minutes):
1. **Insert** → **Waterfall Chart** (built-in visual)
2. **Category**: `reconciliation_summary[layer_name]`
3. **Y-axis**: `reconciliation_summary[row_count_actual]`
4. Not as pretty, but shows data flow concept

**Fix (Option B): Use Stacked Bar Chart** (3 minutes):
1. **Insert** → **Stacked Bar Chart**
2. **Axis**: `layer_name`
3. **Values**: `row_count_actual`
4. **Legend**: `status` (Clean/Quarantine)

---

## 💡 OPTIMIZATION TIPS

### Tip 1: Speed Up Data Generation

**Before**:
```python
# Generates 10,000 rows one-by-one (slow)
for i in range(num_transactions):
    transactions.append({...})
```

**After** (already implemented in provided code):
```python
# Uses vectorized operations (fast)
df = pd.DataFrame.from_records(transactions)
```

**Result**: 5x faster generation

---

### Tip 2: Reduce Power BI File Size

**Problem**: .pbix file is > 100 MB, slow to open

**Fix**: Use **Import** mode instead of **DirectQuery**
1. **File** → **Options** → **Data Load**
2. Check "Import data by default"
3. This caches data locally (faster)

**Result**: Dashboard loads instantly

---

### Tip 3: Improve Visual Performance

**Problem**: Visuals are laggy when filtering

**Fix (Step 1): Reduce data in visuals**
- Use **TOP N** filter to show only top 10 errors
- Apply slicer defaults to latest week only

**Fix (Step 2): Optimize DAX measures**
```dax
// SLOW (re-calculates for every row)
Slow Trust Score = 
DIVIDE(
    CALCULATE(SUM(audit_log[valid_rows])),
    CALCULATE(SUM(audit_log[input_rows]))
)

// FAST (pre-aggregated)
Fast Trust Score = 
DIVIDE(
    SUM(audit_log[valid_rows]),
    SUM(audit_log[input_rows])
)
```

---

## 🐛 DEBUGGING TECHNIQUES

### Debug 1: Verify Data Pipeline

**Run this checklist after each step**:

```bash
# After data generation
ls -lh data/bronze/sales_transactions.csv  # Should be ~1.5 MB
wc -l data/bronze/sales_transactions.csv   # Should show ~10,001 lines (10K + header)

# After validation
ls -lh data/quarantine/sales_quarantine.csv  # Should be ~150 KB
wc -l data/quarantine/sales_quarantine.csv   # Should show 800+ lines

# After gold creation
ls -lh data/gold/brand_analytics.csv  # Should be ~10 KB
```

**If any file is missing**: Re-run the previous script

---

### Debug 2: Inspect Quarantine Records

**See what errors were generated**:
```bash
cat data/quarantine/sales_quarantine.csv | grep -o '"upc_exists"' | wc -l
# Shows count of UPC errors

cat data/quarantine/sales_quarantine.csv | grep -o '"sales_positive"' | wc -l
# Shows count of negative sales errors
```

---

### Debug 3: Verify Trust Score Calculation

**Manual verification**:
```python
import pandas as pd

audit = pd.read_csv('data/audit_log.csv')
valid = audit['valid_rows'].iloc[0]
total = audit['input_rows'].iloc[0]
trust_score = (valid / total) * 100

print(f"Trust Score: {trust_score:.2f}%")
# Should be ~92%

if trust_score > 98:
    print("⚠️ WARNING: Trust Score too high! Re-generate data with errors.")
```

---

## 📞 ESCALATION PATH

### Level 1: Self-Service (This Document)
- Check this troubleshooting guide first
- 90% of issues are covered here

### Level 2: Community Support (30 min response time)
- **Databricks Community**: https://community.databricks.com/
- **Power BI Community**: https://community.powerbi.com/
- **Stack Overflow**: Tag `databricks` or `powerbi`

### Level 3: Internal Support (Same-day response)
- Tag your team's senior data engineer
- Share:
  - Error message (screenshot)
  - What you were trying to do
  - What step you're on (from the 6-hour playbook)

### Level 4: Vendor Support (Next-day response)
- Databricks: Open support ticket (if Enterprise account)
- Microsoft: Power BI support (if Premium license)

---

## 🎯 QUICK WINS (If You're Behind Schedule)

### If You Have 3 Hours Left:

**Skip**:
- Gold layer (use Silver directly)
- Reconciliation framework (focus on quarantine analysis)
- Advanced visuals (Sankey, Decomposition Tree)

**Focus On**:
- Trust Score gauge (RED indicator)
- Revenue at Risk card
- Simple table of quarantine records with Error_Reason
- Practice your pitch (the story matters more than fancy visuals)

---

### If You Have 1 Hour Left:

**Absolute Minimum Viable Demo**:

1. **Single Card Visual**: Trust Score %
   - Shows 92% in RED
   - Position: Center of screen, HUGE font size

2. **Single Table Visual**: Top 20 Quarantine Records
   - Columns: UPC, Error_Reason, Sales_Dollars
   - Sortable by Error_Reason

3. **Your Voice**: Explain what it means
   - "This 92% means 8% of our data has quality issues"
   - "This table shows exactly which records failed and why"
   - "Without this dashboard, we'd have no visibility"

**Time Required**: 15 minutes to build, still convincing!

---

## ✅ PRE-DEMO FINAL CHECKS

**30 Minutes Before Demo**:

- [ ] Open Power BI file → No errors
- [ ] Click Refresh → Data updates successfully
- [ ] Trust Score is < 98% (ideally ~92%)
- [ ] Quarantine table has > 500 rows
- [ ] At least one visual is interactive (click to filter)
- [ ] Screen share tested (if virtual demo)
- [ ] Backup: PDF export of dashboard ready
- [ ] Backup: Screenshots of key visuals saved
- [ ] Phone on silent
- [ ] Deep breath 🧘

---

## 🚑 EMERGENCY BACKUP PLAN

### If Everything Breaks:

**Option 1: Screenshot Demo** (No-code option)
1. Take screenshots of each dashboard page from this repo's examples
2. Import screenshots into PowerPoint
3. Present as "design mockup" instead of live demo
4. Say: "This is the vision - I need resources to build the live version"

**Option 2: Excel Mockup** (1-hour option)
1. Open `data/quarantine/sales_quarantine.csv` in Excel
2. Create a Pivot Table:
   - Rows: Error_Reason
   - Values: Count of Transaction_ID
3. Add conditional formatting (Red for high counts)
4. Calculate Trust Score manually:
   - =(10000-800)/10000 = 92%
5. Present from Excel: "Proof of concept with real generated data"

**Option 3: Reschedule** (Professional option)
- Email leadership: "Encountered a technical issue with the demo environment. I want to give you the best experience possible. Can we reschedule for [DATE]?"
- Use extra time to perfect the demo
- Better to delay than deliver a broken demo

---

## 📚 Additional Resources

### Documentation
- [Databricks Community Edition Docs](https://docs.databricks.com/getting-started/community-edition.html)
- [Power BI Desktop Guide](https://docs.microsoft.com/en-us/power-bi/fundamentals/desktop-getting-started)
- [Delta Lake Documentation](https://docs.delta.io/)

### Video Tutorials
- [Databricks Medallion Architecture (YouTube)](https://www.youtube.com/results?search_query=databricks+medallion+architecture)
- [Power BI Decomposition Tree (YouTube)](https://www.youtube.com/results?search_query=power+bi+decomposition+tree)

### Sample Data
- [Faker Library Docs](https://faker.readthedocs.io/) - For custom data generation
- [Pandas Cheat Sheet](https://pandas.pydata.org/Pandas_Cheat_Sheet.pdf)

---

## 💪 ENCOURAGEMENT

**Remember**:
- Even a partially working demo proves the concept
- The goal is to show the VALUE, not perfection
- Leadership cares about:
  - "Will this save us money?" (Yes)
  - "Will this prevent mistakes?" (Yes)
  - "Is it feasible?" (Yes, you're showing it works)

**You've got this!** 🚀

If you're stuck for > 15 minutes on any single issue, **SKIP IT** and move on. Circle back if you have time. Momentum is more important than perfection.

---

**Last Updated**: January 2026  
**Feedback**: Please update this guide with any new issues you encounter!
