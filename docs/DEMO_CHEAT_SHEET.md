# Quick Reference Card: Control Tower Demo
## Print this and keep it with you during the demo!

---

## YOUR KEY NUMBERS (Memorize These!)

```
Trust Score:        94.2% (RED - below 95% threshold)
Revenue at Risk:    $52,347
Quarantined Records: 625
Products Affected:  "Summer Seltzer" (new product launch)
Region Affected:    Northeast
Root Cause:         Orphan UPCs (not in Product Master)
```

---

## 15-MINUTE DEMO SCRIPT (Bullet Points)

### Minutes 0-3: The Problem
- "We make million-dollar decisions on Circana data"
- "Pipeline says 'success' but doesn't check data quality"
- "Recent example: Missed $200K trend for 3 days"
- "This is 'flying blind'"

### Minutes 3-6: The Solution
- "Control Tower introduces Quarantine Pattern"
- "Don't drop bad data - set it aside for investigation"
- "Trust Score = one number answering 'Can I trust this?'"
- "Complete visibility from Circana to dashboard"

### Minutes 6-12: Live Demo
**[Switch to Power BI]**

1. **Point to RED gauge**
   - "See this? 94.2%. Red means don't decide yet."

2. **Point to $52K card**
   - "This is what we would have missed without Control Tower."

3. **Click Decomposition Tree**
   - "Watch this. I click Error Type..."
   - "522 missing UPCs"
   - "Click Region... Northeast"
   - "Click Brand... Summer Seltzer"
   - "30 seconds from problem to solution"

4. **Point to flow diagram**
   - "Nothing lost. Everything accounted for."

### Minutes 12-14: The Ask
- "Year 1: $480K investment"
- "ROI: 146% - prevent one $500K error and we've paid for it"
- "Timeline: 3 months to go live"

### Minutes 14-15: The Close
- "Choice: Status quo (reactive) vs Control Tower (proactive)"
- "Question: Can we afford to make million-dollar decisions on unverified data?"
- "I'm asking for approval to turn this POC into production"

---

## BODY LANGUAGE REMINDERS

- ✓ **STAND** during demo (command the room)
- ✓ **POINT** at visuals (engage them)
- ✓ **PAUSE** after $52K number (let it sink in - 3 seconds)
- ✓ **EYE CONTACT** during clicks (watch them react)
- ✓ **SMILE** when tree expands (you just showed them magic)
- ✗ Don't fidget
- ✗ Don't apologize
- ✗ Don't read slides word-for-word

---

## IF DEMO BREAKS - STAY CALM

**Screen freezes:**
- "Let me show you the screenshot backup"
- [Switch to PowerPoint, show screenshot]

**Tree won't expand:**
- "The pattern is: 522 errors, all Northeast, all Summer Seltzer"
- [Point to bar chart instead]

**Trust Score = 100%:**
- "This simulation shows perfect data"
- "In production, we typically see 94-97%"
- "Even at 100%, the audit trail provides value"

---

## Q&A CHEAT SHEET

**Q: "Why not fix at source?"**
A: "We should! But we don't control Circana. This is our last line of defense for transmission errors, schema changes, and new products."

**Q: "Cost too high?"**
A: "Prevent ONE $500K decision error and we've paid for the year. Everything else is ROI."

**Q: "Can we pilot first?"**
A: "Absolutely! 2-month pilot with one product, then scale. Budget includes this."

**Q: "Engineering time?"**
A: "2 engineers × 3 months to build. Then 1 FTE for maintenance."

**Q: "What if Trust Score is always 100%?"**
A: "Great! Proves data quality. The audit trail still provides compliance value."

**Q: "Who else does this?"**
A: "Netflix, Uber, Airbnb built similar systems. We're bringing this to CPG."

---

## PRE-DEMO CHECKLIST (5 minutes before)

- [ ] Laptop charged + power cable ready
- [ ] HDMI cable connected and tested
- [ ] Power BI file opens (`ControlTower_Demo.pbix`)
- [ ] All tables loaded (5 tables: Sales, Quarantine, Audit, Products, Stores)
- [ ] Trust Score gauge shows RED or YELLOW (not green!)
- [ ] Decomposition Tree expands when clicked
- [ ] Water bottle nearby (dry mouth is common)
- [ ] This cheat sheet in hand
- [ ] Backup PowerPoint with screenshots open (just in case)
- [ ] Phone on silent

---

## YOUR CONFIDENT OPENER

> "Good morning. Thank you for your time. I'm going to show you how we can prevent data quality issues from costing us hundreds of thousands in bad decisions. This will take 15 minutes and I have a live demo."

**[Pause 2 seconds. Make eye contact. Smile.]**

---

## YOUR CONFIDENT CLOSER

> "So here's the choice.
> 
> We can continue with the status quo - react to data issues 3-5 days too late.
> 
> Or we invest in the Control Tower and shift to proactive data quality.
> 
> The question isn't 'Can we afford $480K?'
> 
> The question is: **'Can we afford to make million-dollar decisions on data we can't verify?'**
> 
> I've shown you we currently have a $52K blind spot - and that's just ONE source, ONE week.
> 
> I'm asking for approval to turn this proof of concept into our competitive advantage.
> 
> Thank you. I'm happy to take questions."

**[Pause. Stand still. Make eye contact. Wait for response.]**

---

## POST-DEMO ACTIONS

**If they approve:**
- [ ] Schedule follow-up within 48 hours
- [ ] Send one-pager summary with ROI
- [ ] Propose pilot timeline
- [ ] Request Azure/Databricks access

**If they say "let us think about it":**
- [ ] Send email summary with screenshots
- [ ] Offer 1:1 walkthrough
- [ ] Share architecture documentation
- [ ] Follow up in 1 week

**If they reject:**
- [ ] Ask: "What's the biggest concern?"
- [ ] Listen carefully
- [ ] Address concern specifically
- [ ] Offer smaller pilot or phased approach

---

## POWER PHRASES TO USE

✓ "Flying blind on data quality"  
✓ "Revenue at risk"  
✓ "Can I trust this report?"  
✓ "30 seconds from problem to solution"  
✓ "Nothing was lost"  
✓ "Proactive vs reactive"  
✓ "Competitive advantage"  

---

## PHRASES TO AVOID

✗ "I think this will work"  → Say: "This WILL prevent $500K errors"
✗ "Maybe we should"     → Say: "I recommend we"
✗ "Sorry if this is unclear" → Say: "Let me clarify"
✗ "It's just a demo"    → Say: "This is a working prototype"

---

## TIMING CHECKPOINT

**At 5 minutes**: Should be showing Power BI  
**At 10 minutes**: Should be clicking Decomposition Tree  
**At 13 minutes**: Should be showing the investment slide  
**At 15 minutes**: Should be closing and opening for Q&A  

If ahead of schedule: Add more context during demo  
If behind schedule: Skip the Sankey diagram, focus on Tree  

---

## REMEMBER

**They don't care about:**
- Technology stack details
- How Delta Lake works
- Python vs Scala

**They DO care about:**
- Preventing bad decisions ($52K mistake)
- Saving time (30 sec vs 2 hours)
- ROI (146% year 1)
- Risk mitigation

**Your job:** Translate tech into business value

---

## FINAL PEP TALK

✓ You've prepared well  
✓ You know your numbers  
✓ The demo works  
✓ The ROI is strong  
✓ You have backup plans  

**Trust your preparation.**

**Speak with confidence.**

**Show them the art of the possible.**

**You've got this!** 🚀

---

**Now go show them how to stop flying blind!**
