# Data Quality Control Tower - User Guide

## For Business Analysts and Data Consumers

### What is the Control Tower?

The Data Quality Control Tower is your "health dashboard" for data pipelines. Just like a doctor checks your vital signs before diagnosing you, the Control Tower checks data health before you make business decisions.

**Key Question it Answers:** *"Can I trust the numbers in my sales report?"*

---

## Quick Start: Reading the Dashboard

### The Trust Score (Your North Star)

**Location:** Top-left gauge

**What it means:**
- **Green (98-100%)**: Data is highly reliable. Safe to make decisions.
- **Yellow (95-98%)**: Minor issues present. Review with caution.
- **Red (<95%)**: Significant data quality issues. Investigate before deciding.

**Example:**
- Trust Score of 96% means 4% of your data had quality issues and was quarantined for review.

### Revenue at Risk (The Business Impact)

**Location:** Top-right card

**What it means:**
- Dollar value of transactions that failed quality checks
- This is NOT lost money—it's **unverified** money
- Shows the potential error in your reports if quality issues weren't caught

**Example:**
- "$52,347 at Risk" means if you made decisions without the Control Tower, your numbers could be off by $52K.

### The Data Flow (Sankey Diagram)

**Location:** Center of dashboard

**What it shows:**
- How data flows from Bronze (raw) → Silver (validated) → Gold (reporting)
- The "split" shows how much data passed validation vs. was quarantined

**How to read it:**
- **Thick green line**: Healthy data flow
- **Thick red line**: High quarantine rate (investigate!)

### Root Cause Analysis (Decomposition Tree)

**Location:** Bottom of dashboard

**What it does:**
- Automatically finds patterns in data quality issues
- Click to drill down: Error Type → Region → Brand → Store

**Example workflow:**
1. See red Trust Score
2. Click Decomposition Tree
3. See "Orphan UPC" is the top error (500 records)
4. Click to expand
5. See it's all in "Northeast" region
6. Click to expand
7. See it's all for "Summer Seltzer" brand
8. **Insight:** New product launch, Master Data not updated!

---

## Common Scenarios

### Scenario 1: Weekly Data Review

**Every Monday morning:**

1. Open Control Tower dashboard
2. Check Trust Score
   - Green? → Proceed to your sales analysis
   - Yellow/Red? → Continue to step 3
3. Check "Revenue at Risk"
   - < $10K? → Note and proceed
   - > $10K? → Investigate
4. Look at error types (table below tree)
   - Are they new issues or ongoing?
5. Document findings and escalate if needed

**Time required:** 5 minutes

### Scenario 2: Investigating a Quality Issue

**You see Trust Score at 94% (Red):**

1. **Quantify the impact**
   - Check Revenue at Risk: $52K
   - Check Quarantined Records: 625

2. **Find the root cause**
   - Click Decomposition Tree
   - Drill: Error Type → "upc_in_master" (522 records)
   - Drill: Region → "Northeast" (480 records)
   - Drill: Brand → "Summer Seltzer" (450 records)

3. **Understand the issue**
   - New product "Summer Seltzer" launched
   - UPCs not in Product Master
   - Impacting Northeast region stores

4. **Take action**
   - Contact Master Data team
   - Provide UPC list (from quarantine table)
   - Request urgent update

5. **Monitor resolution**
   - Check next week's Trust Score
   - Verify "Summer Seltzer" transactions now in Silver layer

**Time required:** 15 minutes

### Scenario 3: Preparing for Executive Meeting

**Your VP asks: "Is the Circana data accurate this week?"**

1. Open Control Tower
2. Screenshot the dashboard
3. Prepare your talking points:

**If Green:**
- "Yes, Trust Score is 98.5%"
- "All data passed validation"
- "Safe to proceed with forecasts"

**If Yellow/Red:**
- "Trust Score is 94%, here's why..."
- "We have $52K in quarantined data"
- "Root cause: [specific issue from tree]"
- "ETA for resolution: [date]"
- "Recommendation: Wait for clean data OR proceed with caveat"

**Time required:** 5 minutes

---

## Understanding Error Types

### Critical Errors (Must Fix Immediately)

**Orphan UPC** (`upc_in_master`)
- **What:** UPC code not in Product Master
- **Impact:** Can't attribute sales to brands/categories
- **Fix:** Update Product Master OR investigate data source

**Missing Store** (`store_in_master`)
- **What:** Store ID not in Store Master
- **Impact:** Can't attribute sales to regions
- **Fix:** Update Store Master OR investigate store closures

**Null Sales** (`sales_not_null`)
- **What:** Sales dollar amount is missing
- **Impact:** Revenue calculations incomplete
- **Fix:** Investigate data extraction process

### High Severity Errors (Should Fix Soon)

**Negative Sales** (`non_negative_sales`)
- **What:** Sales amount is negative
- **Impact:** Skews totals and averages
- **Likely cause:** Returns processing error
- **Fix:** Review returns logic OR verify intentional

**Null Units** (`units_not_null`)
- **What:** Units sold is missing
- **Impact:** Volume analysis incomplete
- **Fix:** Check data completeness

### Medium Severity Errors (Monitor)

**Extreme Price** (`reasonable_price`)
- **What:** Unit price exceeds $100
- **Impact:** May indicate decimal error ($5.99 → $599)
- **Fix:** Validate pricing OR confirm luxury item

---

## Dashboard Filters and Slicers

### Available Filters

**Date Range**
- Default: Last 4 weeks
- Use to compare trends over time

**Region**
- Filter to your specific market
- See region-specific quality issues

**Brand**
- Focus on specific product lines
- Useful for category managers

**Batch ID**
- Technical filter for IT
- Tracks specific pipeline runs

### How to Use Filters

1. Click the filter icon (funnel) on any visual
2. Select your criteria
3. Click "Apply filter"
4. Dashboard updates across all visuals
5. Click "Clear filters" to reset

---

## Alerts and Notifications

### When You'll Be Notified

The system sends alerts when:
- Trust Score drops below 95%
- Revenue at Risk exceeds $10,000
- Critical errors appear
- Data is older than 26 hours (stale)

### How to Respond

**Trust Score Alert:**
1. Open dashboard immediately
2. Find root cause (Decomposition Tree)
3. Contact responsible team
4. Monitor resolution

**Revenue at Risk Alert:**
1. Assess impact to your analysis
2. Decide: Wait for fix OR proceed with caveat
3. Document decision

**Critical Error Alert:**
1. Halt any decision-making
2. Escalate to Data Ops team
3. Wait for resolution confirmation

---

## FAQs

**Q: What does "quarantine" mean? Is the data lost?**
A: No! Quarantined data is preserved for investigation. It's set aside because it failed validation, but it's not deleted. Think of it like "pending review."

**Q: Can I see the actual quarantined records?**
A: Yes! Click on the "Quarantine Details" page (Tab 2). You'll see every record with error codes.

**Q: Why isn't Trust Score 100%?**
A: Real-world data always has some quality issues. 98%+ is considered excellent. Focus on the trend, not perfection.

**Q: What if I disagree with an error classification?**
A: Contact the Data Quality team. Validation rules can be adjusted if business logic changes.

**Q: How often is the dashboard updated?**
A: Weekly, aligned with Circana data delivery schedule (every Monday 6 AM).

**Q: Can I export quarantine data?**
A: Yes! Right-click the quarantine table → Export Data → CSV.

**Q: What's the difference between Bronze, Silver, and Gold?**
- **Bronze**: Raw data as received from Circana
- **Silver**: Cleaned and validated data
- **Gold**: Aggregated data for reporting (what you see in sales dashboards)

**Q: Who do I contact if I see a red Trust Score?**
A: 
1. First: Check Decomposition Tree for obvious issues
2. If unclear: Email dataops@company.com
3. If urgent: Call Data Ops hotline

---

## Best Practices

### Daily
- ✓ Glance at Trust Score before using sales data
- ✓ Note any yellow/red status
- ✓ Bookmark the dashboard

### Weekly
- ✓ Review Trust Score trend
- ✓ Check top error types
- ✓ Document any recurring issues
- ✓ Attend Data Quality review meeting (Fridays 10 AM)

### Monthly
- ✓ Compare Trust Score month-over-month
- ✓ Identify improvement opportunities
- ✓ Suggest new validation rules

### Don't
- ✗ Ignore a red Trust Score
- ✗ Make major decisions during quality issues
- ✗ Assume the error will fix itself
- ✗ Filter out the quarantine data to "make it look better"

---

## Keyboard Shortcuts (Power BI)

- **Ctrl + S**: Save dashboard
- **Ctrl + F**: Search within visuals
- **Ctrl + Click**: Select multiple items
- **Alt + F5**: Refresh data
- **Ctrl + →**: Navigate to next page

---

## Troubleshooting

**Issue: Dashboard is blank**
- **Solution**: Click "Refresh" button (top menu)

**Issue: Trust Score shows "N/A"**
- **Solution**: No data for selected date range. Adjust date filter.

**Issue: Decomposition Tree won't expand**
- **Solution**: No sub-categories exist. This is the most granular level.

**Issue: Revenue at Risk seems too high**
- **Solution**: This is correct! It's showing actual business impact. Investigate the errors.

**Issue: Can't see last week's data**
- **Solution**: Pipeline runs Monday 6 AM. Data available by 9 AM.

---

## Glossary

| Term | Definition |
|------|------------|
| **Bronze Layer** | Raw data as received from source system |
| **Silver Layer** | Cleaned, validated data |
| **Gold Layer** | Business-ready, aggregated data |
| **Quarantine** | Data set aside for failing validation rules |
| **Trust Score** | Percentage of records passing all quality checks |
| **Revenue at Risk** | Dollar value of quarantined transactions |
| **Orphan UPC** | Product code not found in master data |
| **Batch ID** | Unique identifier for each pipeline run |
| **Medallion Architecture** | Bronze → Silver → Gold data flow pattern |
| **Shadow DLT** | Quality validation logic (technical term) |
| **Reconciliation** | Verifying no data was lost between layers |

---

## Support

**For Dashboard Issues:**
- Email: bi-support@company.com
- Teams: BI-Support channel

**For Data Quality Issues:**
- Email: dataops@company.com
- Teams: DataOps channel
- Hotline: x1234 (urgent only)

**For Training:**
- Monthly workshop: First Tuesday, 2 PM
- 1:1 training: Book via calendar

---

## Appendix: Sample Error Investigation Report

```
Date: January 20, 2026
Analyst: Jane Smith
Issue: Low Trust Score (94.2%)

FINDINGS:
- Quarantined Records: 625
- Revenue at Risk: $52,347
- Root Cause: Orphan UPCs for "Summer Seltzer"
- Affected Region: Northeast
- Affected Stores: 12

ANALYSIS:
New product launch on Jan 15. Marketing team 
launched before Master Data team added UPCs to system.

ACTION TAKEN:
1. Contacted Master Data team (John Doe)
2. Provided list of missing UPCs (22 codes)
3. ETA for update: Jan 21, 10 AM

IMPACT:
Northeast sales reports understated by ~$50K for week 
of Jan 15-21. Corrected data will be available Jan 22.

RECOMMENDATION:
Update new product launch process to include Master
Data update 1 week before commercial launch.
```

---

**Remember: The Control Tower doesn't tell you WHAT to do. It tells you IF your data is trustworthy enough to make decisions.**
