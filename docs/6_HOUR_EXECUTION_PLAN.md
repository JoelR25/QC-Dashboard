# 6-Hour Execution Plan: Control Tower Demo
## Personal Account Setup for Today's Practice

**Goal**: Have a working Control Tower demo ready in 6 hours for leadership presentation

---

## Hour 0-1: Environment Setup (60 minutes)

### Minute 0-15: Databricks Setup
1. Go to https://community.cloud.databricks.com/signup.html
2. Sign up with personal email (FREE)
3. Verify email
4. Log in

**Checkpoint**: You're logged into Databricks

### Minute 15-30: Create Cluster
1. Click "Compute" in left sidebar
2. Click "Create Cluster"
3. Settings:
   - Name: `ControlTower`
   - Runtime: `13.3 LTS` (default)
   - Mode: `Single Node`
   - Node type: Default (15GB memory)
4. Click "Create Cluster"
5. **Wait 5 minutes** for cluster to start (GREEN indicator)

**Checkpoint**: Cluster is running (green light)

### Minute 30-40: Install Libraries
1. Go to your cluster page
2. Click "Libraries" tab
3. Click "Install New"
4. Select "PyPI"
5. Package name: `faker`
6. Click "Install"
7. Wait for "Installed" status
8. Repeat for `pyyaml`

**Checkpoint**: Both libraries show "Installed" status

### Minute 40-50: Power BI Setup
1. Download Power BI Desktop: https://aka.ms/pbidesktop
2. Run installer (10 minutes)
3. Launch Power BI Desktop
4. Close welcome screen

**Checkpoint**: Power BI Desktop is open

### Minute 50-60: Create Working Folder
On your computer:
```
C:\ControlTower\
  ├── data\           (for CSV exports)
  ├── screenshots\    (for demo screenshots)
  └── reports\        (for Monday check reports)
```

**Checkpoint**: Folders created, ready to work

---

## Hour 1-2: Data Generation in Databricks (60 minutes)

### Minute 60-75: Create Notebook
1. In Databricks, click "Workspace"
2. Click your email folder
3. Click "⋮" → "Create" → "Notebook"
4. Name: `Control_Tower_Demo`
5. Language: Python
6. Cluster: Select `ControlTower`
7. Click "Create"

**Checkpoint**: Empty notebook open

### Minute 75-90: Copy Pipeline Code
1. Go to the GitHub repo file: `databricks/Control_Tower_Pipeline.py`
2. Copy ALL content
3. Paste into your notebook (it will create cells automatically)
4. Save (Ctrl+S)

**Checkpoint**: Notebook has ~15 code cells

### Minute 90-110: Execute Pipeline
1. Click "Run All" at top
2. Watch cells execute (green checkmarks)
3. Look for key outputs:
   - "DATA GENERATION COMPLETE" ✓
   - "Bronze layer created" ✓
   - "Trust Score: XX.XX%" ✓ (should be ~94-96%)
   - "Quarantined Records: XXX" ✓ (should be 500-700)

**IMPORTANT**: If Trust Score = 100%, something is wrong. Re-run the notebook.

**Checkpoint**: Pipeline completes, Trust Score shows ~94-96%

### Minute 110-120: Verify Output
Run these queries in a new cell:
```python
# Quick verification
print(f"Bronze: {spark.read.format('delta').load('/tmp/control_tower/bronze').count():,}")
print(f"Silver: {spark.read.format('delta').load('/tmp/control_tower/silver').count():,}")
print(f"Quarantine: {spark.read.format('delta').load('/tmp/control_tower/silver_quarantine').count():,}")
print(f"Gold: {spark.read.format('delta').load('/tmp/control_tower/gold').count():,}")
```

Expected output:
- Bronze: ~10,500
- Silver: ~9,800-9,900
- Quarantine: ~500-700
- Gold: ~400-500

**Checkpoint**: Numbers look reasonable, quarantine > 0

---

## Hour 2-3: Export and Power BI Setup (60 minutes)

### Minute 120-135: Download Data Files
1. Open browser to: https://community.cloud.databricks.com/files/
2. You should see files:
   - `control_tower_gold.csv`
   - `control_tower_quarantine.csv`
   - `control_tower_audit.csv`
   - `control_tower_products.csv`
   - `control_tower_stores.csv`
3. Right-click each → Save As → `C:\ControlTower\data\`

**Checkpoint**: 5 CSV files in your data folder

### Minute 135-160: Import to Power BI
1. Open Power BI Desktop
2. Click "Get Data" → "Text/CSV"
3. Navigate to `C:\ControlTower\data\`
4. Select `control_tower_gold.csv` → Open
5. Click "Transform Data"
6. Rename table (right-click) → `Fact_Sales`
7. Click "Close & Apply"
8. Repeat for:
   - `control_tower_quarantine.csv` → `Fact_Quarantine`
   - `control_tower_audit.csv` → `Fact_Audit_Log`
   - `control_tower_products.csv` → `Dim_Product`
   - `control_tower_stores.csv` → `Dim_Store`

**Checkpoint**: 5 tables loaded in Power BI

### Minute 160-180: Create Relationships
1. Click "Model" view (left sidebar, icon looks like tables)
2. Drag to create relationships:
   - `Fact_Sales[Brand]` → `Dim_Product[Brand]`
   - `Fact_Sales[Region]` → `Dim_Store[Region]`
   - `Fact_Quarantine[Store_ID]` → `Dim_Store[Store_ID]`
3. All relationships should be "Many to One (*:1)"

**Checkpoint**: 3 relationship lines visible in model view

---

## Hour 3-4: Build Dashboard Visuals (60 minutes)

### Minute 180-195: Create Trust Score Gauge
1. Click "Report" view (left sidebar)
2. Click "Visualizations" pane → Select "Gauge"
3. Drag to create large gauge (top-left of canvas)
4. Click "New Measure" in ribbon
5. Paste this DAX:
```dax
Trust Score % = 
DIVIDE(
    SUM(Fact_Audit_Log[valid_rows]),
    SUM(Fact_Audit_Log[input_rows]),
    0
) * 100
```
6. Drag `Trust Score %` to Value field
7. Set Maximum: 100
8. Format → Data colors → Conditional formatting → Rules:
   - If value >= 98: Green
   - If value >= 95: Yellow
   - If value < 95: Red

**Checkpoint**: Gauge shows ~94-96% in RED/YELLOW

### Minute 195-210: Create Revenue at Risk Card
1. Click blank area
2. Select "Card" visual
3. Click "New Measure":
```dax
Revenue at Risk = SUM(Fact_Quarantine[Sales_Dollars])
```
4. Drag `Revenue at Risk` to card
5. Format as Currency ($)
6. Make font large and RED

**Checkpoint**: Card shows ~$50,000-60,000

### Minute 210-225: Create Quarantine Count Card
1. Add another "Card" visual
2. New Measure:
```dax
Quarantined Records = COUNTROWS(Fact_Quarantine)
```
3. Drag to card
4. Format number with comma separator
5. Add title: "Quarantined Records"

**Checkpoint**: Card shows ~500-700 records

### Minute 225-240: Create Error Type Bar Chart
1. Add "Clustered Bar Chart"
2. Y-axis: `Fact_Quarantine[Error_Details]` (split by first part before "|")
3. X-axis: Count of rows
4. Sort descending by count
5. Add data labels

**Checkpoint**: Bar chart shows error types, "upc_in_master" likely #1

---

## Hour 4-5: Advanced Visuals & Polish (60 minutes)

### Minute 240-260: Add Decomposition Tree (THE KEY VISUAL!)
1. In Visualizations pane, click "Get more visuals"
2. Search "Decomposition Tree"
3. Install the official Microsoft visual
4. Add to canvas (bottom half)
5. Make it LARGE (this is your "wow" visual)
6. Configure:
   - Analyze: `Quarantined Records` (the measure you created)
   - Explain By (in order):
     - `Error_Details`
     - `Dim_Store[Region]`
     - `Dim_Product[Brand]`
     - `Fact_Quarantine[Store_ID]`

**Checkpoint**: Tree shows with expandable nodes

### Minute 260-280: Test Decomposition Tree
1. In report view, click the tree
2. Click on the largest bar (likely an error type)
3. Tree should expand showing regions
4. Click a region → expands to brands
5. Click a brand → expands to stores

**This is your "Aha!" moment for the demo**

**Checkpoint**: Tree expands and shows drill-down path

### Minute 280-300: Add Trend Line Chart
1. Add "Line Chart"
2. X-axis: `Fact_Audit_Log[timestamp]` (convert to Date)
3. Y-axis: `Trust Score %`
4. Title: "Trust Score Trend"

**Checkpoint**: Line shows trend over time

---

## Hour 5: Demo Preparation (60 minutes)

### Minute 300-320: Create Demo Scenario Card
1. Add a Text Box at top of dashboard
2. Type:
```
SCENARIO: Week of Jan 15, 2026
New Product Launch: "Summer Seltzer"
Marketing launched before Master Data team updated UPCs
Result: 500+ orphan UPCs detected in Northeast region
Trust Score: 94.2% (below 95% threshold)
```
3. Make it stand out with yellow background

**Checkpoint**: Scenario card visible

### Minute 320-340: Take Screenshots
1. Take screenshot of full dashboard → Save to `C:\ControlTower\screenshots\dashboard_overview.png`
2. Expand Decomposition Tree to show drill-down → Screenshot → `drill_down_example.png`
3. Screenshot of gauge showing red → `trust_score_alert.png`

**Checkpoint**: 3 screenshots saved

### Minute 340-360: Practice Demo Script

**Read this out loud 3 times:**

> "Good morning. What you're seeing is our Data Quality Control Tower. 
> 
> See this red gauge? That's our Trust Score - 94.2%. It's telling us we have a data quality issue THIS WEEK.
> 
> Look at this number - $52,000. That's the revenue we would have MISSED if we didn't catch this.
> 
> Now watch this - I click on this Decomposition Tree. It tells me the error is 'Missing UPCs in Master Data.' I click again - it's all in the Northeast. One more click - it's all the new Summer Seltzer brand.
> 
> We just went from 'something's wrong' to 'call the Master Data team about Summer Seltzer UPCs in Northeast' in 30 seconds.
> 
> That's the Control Tower. It doesn't tell you WHAT to buy. It tells you IF the data is trustworthy."

**Checkpoint**: You can deliver this smoothly

---

## Hour 6: Final Polish & Backup Plan (60 minutes)

### Minute 360-375: Create Backup Slides
In case demo fails, create PowerPoint with screenshots:
1. Slide 1: "The Problem" - blurred dashboard
2. Slide 2: "The Solution" - architecture diagram
3. Slide 3: Screenshot of dashboard overview
4. Slide 4: Screenshot of decomposition tree drill-down
5. Slide 5: "The Ask" - investment request

**Checkpoint**: 5-slide backup deck ready

### Minute 375-390: Save Everything
1. Save Power BI file: `ControlTower_Demo.pbix` in `C:\ControlTower\`
2. Export Databricks notebook:
   - Click "⋮" next to notebook name
   - Export → DBC Archive
   - Save to `C:\ControlTower\`
3. Create a README.txt with your setup notes

**Checkpoint**: All files backed up

### Minute 390-405: Practice Full Demo
1. Close Power BI
2. Reopen `ControlTower_Demo.pbix`
3. Walk through your script with the visuals
4. Time yourself - should be 10-12 minutes
5. Practice clicking through Decomposition Tree smoothly

**Checkpoint**: Demo runs smoothly under 15 minutes

### Minute 405-420: Contingency Planning
Write down answers to these likely questions:
- "How much does this cost?" → $180K first year
- "How long to implement?" → 3 months
- "Why not just fix the source data?" → We can't control Circana's processes
- "What if Trust Score is always 100%?" → That proves quality (still valuable)
- "Can we try it with one product first?" → Yes! Perfect pilot approach

**Checkpoint**: You have crisp answers ready

---

## CRITICAL SUCCESS FACTORS

### ✓ Trust Score MUST be < 100%
If it shows 100%, you have no "crisis" to demonstrate. Re-run the Databricks notebook with different seed.

### ✓ Quarantine table must have data
If quarantine is empty, there's nothing to analyze. Verify the data generation injected errors.

### ✓ Decomposition Tree must drill down
This is your "wow" moment. Practice clicking through the path multiple times.

### ✓ Know your numbers
- Trust Score: ~94-96%
- Revenue at Risk: ~$50K
- Quarantined Records: ~600
- Products affected: Focus on one (e.g., "Summer Seltzer")

---

## DEMO DAY CHECKLIST (15 minutes before presentation)

- [ ] Power BI file opens without errors
- [ ] All visuals load (5 tables loaded)
- [ ] Trust Score gauge shows RED or YELLOW (not green)
- [ ] Decomposition Tree expands when clicked
- [ ] You've practiced your script 3+ times
- [ ] Screenshots available as backup
- [ ] Laptop charged + power adapter ready
- [ ] HDMI cable for projector tested
- [ ] Demo runs in < 15 minutes

---

## IF SOMETHING BREAKS

**Power BI won't open file:**
- Use your screenshots in PowerPoint backup deck

**Decomposition Tree won't expand:**
- Use bar chart instead, manually explain the pattern

**Trust Score shows 100%:**
- Say "This simulation shows perfect data, but in production we see 94-97%"

**Forgot your script:**
- Point, click, and narrate what you see: "This red gauge shows a problem... this tree shows where..."

---

## POST-DEMO ACTIONS

If leadership approves:
1. Schedule follow-up meeting within 48 hours
2. Send one-pager with ROI calculations
3. Propose pilot with one product category
4. Request access to Azure/Databricks accounts

If they want to "think about it":
1. Send email summary with screenshots
2. Offer 1:1 walkthrough
3. Share links to architecture documentation
4. Follow up in 1 week

---

## QUICK REFERENCE: File Locations

**Databricks:**
- Notebook: `/Users/your.email@email.com/Control_Tower_Demo`
- Data: `/tmp/control_tower/`

**Local Computer:**
- Power BI: `C:\ControlTower\ControlTower_Demo.pbix`
- CSV Data: `C:\ControlTower\data\*.csv`
- Screenshots: `C:\ControlTower\screenshots\*.png`
- Backup: `C:\ControlTower\backup\`

**Browser Bookmarks:**
- Databricks: https://community.cloud.databricks.com/
- Databricks Files: https://community.cloud.databricks.com/files/
- Power BI Download: https://aka.ms/pbidesktop

---

## SUCCESS METRICS

You're ready to demo if:
- ✓ Demo runs start-to-finish in under 15 minutes
- ✓ You can explain Trust Score in one sentence
- ✓ Decomposition Tree drill-down works smoothly
- ✓ You know the "Summer Seltzer" story cold
- ✓ You can answer the 5 key objections
- ✓ Everything is backed up

---

**Good luck! You've got this!** 🚀

The key to a great demo is not perfection—it's telling a story that resonates. Your story: "We found a $52K blind spot in our data, and here's how we caught it in real-time."
