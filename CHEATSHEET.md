# 📋 Quick Reference Cheat Sheet

## One-Page Guide for Demo Day

---

### ⚡ SETUP COMMANDS

```bash
# 1. Clone & Setup
git clone https://github.com/JoelR25/QC-Dashboard.git
cd QC-Dashboard
pip install -r requirements.txt

# 2. Generate Data
python scripts/01_generate_synthetic_data.py

# 3. Validate Quality
python scripts/02_validate_data_quality.py

# 4. Create Gold Layer
python scripts/03_create_gold_layer.py

# 5. Verify Data
ls -lh data/quarantine/sales_quarantine.csv  # Must be ~150KB
wc -l data/quarantine/sales_quarantine.csv   # Must show ~800 lines
```

---

### 📊 POWER BI: KEY DAX MEASURES

```dax
Trust Score % = 
DIVIDE(SUM(audit_log[valid_rows]), SUM(audit_log[input_rows]), 0) * 100

Revenue at Risk = 
SUMX(sales_quarantine, ABS(sales_quarantine[Sales_Dollars]))

Quarantine Rows = 
SUM(audit_log[quarantine_rows])

Trust Score Color = 
SWITCH(TRUE(), [Trust Score %] >= 98, "Green", [Trust Score %] >= 95, "Yellow", "Red")
```

---

### 🎯 DASHBOARD MUST-HAVES

**Zone A (Top-Left)**: Trust Score Gauge (RED, ~92%)  
**Zone B (Top-Right)**: Revenue at Risk Card ($50K)  
**Zone C (Middle)**: Quarantine Table (sortable by Error_Reason)  
**Zone D (Bottom)**: Decomposition Tree (Error → Region → Brand)

---

### 🎤 15-MINUTE PITCH SCRIPT

**0:00-2:30 - The Problem**:
> "Last quarter, we lost $200K because data was silently dropped. Our monitoring only tells us if the pipeline ran, not if the data is correct."

**2:30-5:00 - The Solution**:
> "The Control Tower introduces: Quarantine Pattern, Trust Score KPI, and Root Cause Drill-Down."

**5:00-12:00 - Live Demo**:
1. Point to RED Trust Score → "94% means 6% has issues"
2. Point to Revenue at Risk → "$50K in unattributed sales"
3. Click Decomposition Tree → Drill 3 levels
4. "Three clicks from 'something's wrong' to 'exactly what and who fixes it'"

**12:00-15:00 - The Ask**:
> "I need approval for production Databricks. Investment: 2 weeks, 1 engineer. ROI: 40% time savings, prevent $200K mistakes."

---

### 🚨 EMERGENCY FIXES

| Problem | Quick Fix |
|---------|-----------|
| Trust Score = 100% | Force errors: `df.loc[:500, 'UPC'] = '999999001'` |
| Blank visuals | Home → Refresh data |
| Decomposition Tree won't click | Rebuild: Use MEASURE not column in "Analyze" |
| Power BI crash | Show PDF backup from desktop |
| Out of time | Minimum: Trust Score gauge + Quarantine table only |

---

### ✅ PRE-DEMO CHECKLIST

- [ ] Trust Score shows ~92% (RED)
- [ ] Quarantine table has 800+ rows
- [ ] Decomposition Tree expands on click
- [ ] Screen share tested
- [ ] Phone on silent
- [ ] Water bottle ready
- [ ] Backup: PDF export saved
- [ ] Pitch script open on 2nd monitor

---

### 📁 FILE LOCATIONS

```
data/
├── master/
│   ├── product_master.csv      # 100 products
│   └── store_master.csv         # 50 stores
├── bronze/
│   └── sales_transactions.csv   # 10,000 rows (with errors)
├── silver/
│   └── sales_clean.csv          # 9,200 valid rows
├── quarantine/
│   └── sales_quarantine.csv     # 800 invalid rows ⚠️ CRITICAL
├── gold/
│   └── brand_analytics.csv      # Aggregated data
└── audit_log.csv                # Trust Score source
```

---

### 🔢 EXPECTED NUMBERS

| Metric | Expected Value |
|--------|----------------|
| Total Transactions | 10,000 |
| Valid Rows | 9,200 (92%) |
| Quarantine Rows | 800 (8%) |
| Trust Score | ~92% (RED) |
| Revenue at Risk | ~$50,000 |
| Orphan UPCs | 500 (5%) |
| Negative Sales | 100 (1%) |
| Missing Stores | 200 (2%) |

---

### 📞 HELP RESOURCES

**Documentation**:
- Full Guide: `docs/6_hour_engineer_playbook.md`
- Troubleshooting: `docs/troubleshooting.md`
- Pitch Script: `docs/executive_pitch_outline.md`

**Community**:
- Power BI: https://community.powerbi.com/
- Databricks: https://community.databricks.com/
- Stack Overflow: Tag `powerbi` or `databricks`

---

### 💡 DEMO TIPS

1. **Practice out loud** - Silence kills demos
2. **Narrate actions** - "I'm clicking Error_Reason..."
3. **Pause after key points** - Let insights sink in
4. **Have backup** - Screenshots saved
5. **Stay calm** - If something breaks, laugh it off: "This is why we need production!"

---

### 🎬 THE MONEY LINE

> **"This went from 'something's wrong' to 'exactly what's wrong and who fixes it' in three clicks."**

Use this line when demonstrating the Decomposition Tree. It's your mic drop moment.

---

### ⏱️ TIME ALLOCATION

| Activity | Time | Can Skip? |
|----------|------|-----------|
| Setup | 1 hour | ❌ NO |
| Data Generation | 1 hour | ❌ NO |
| Power BI Build | 2 hours | ⚠️ Simplify if needed |
| Polish & Test | 1 hour | ⚠️ Minimum 30 min |
| Dry Run | 1 hour | ✅ YES (but don't) |

---

### 🏆 SUCCESS METRICS

**Demo Success**:
- ✅ Leadership asks: "When can we start?"
- ✅ You get approval email within 48 hours
- ✅ Follow-up meeting scheduled

**Personal Win**:
- ✅ You finished in 6 hours
- ✅ You delivered a coherent pitch
- ✅ You learned something valuable

---

### 🙏 FINAL ENCOURAGEMENT

**You've done the work. Trust your prep.**

Even if the demo isn't perfect, you're solving a real problem. The concept is sound. The value is clear. Leadership will see that.

**Go show them what's possible!** 🚀

---

**Print this page and keep it next to you during demo day.**
