# Team Roles & Responsibilities
## Who Does What: Control Tower Implementation

---

## Executive Summary

The Control Tower requires collaboration across 5 key teams. Each team has specific responsibilities and expertise areas. This document clarifies who does what to avoid confusion and ensure smooth execution.

---

## Team Structure

```
┌─────────────────────────────────────────────────┐
│         STEERING COMMITTEE                      │
│   (VP Analytics, Director Data Engineering)     │
└─────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬─────────────┐
        ▼             ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Data      │ │  Platform   │ │  BI/Report  │ │  Business   │
│ Engineering │ │  Team (IT)  │ │  Dev Team   │ │  Analysts   │
│   Team      │ │             │ │             │ │   (BAs)     │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
       │               │               │               │
       └───────────────┴───────────────┴───────────────┘
                       │
                ┌──────▼──────┐
                │   Data      │
                │   Steward   │
                └─────────────┘
```

---

## Role 1: Data Engineering Team

### Primary Responsibilities
Build and maintain the data pipeline (Circana → ADLS → Databricks → Power BI)

### Specific Tasks

**Phase 1: Design (Month 1)**
- [ ] Design Medallion Architecture (Bronze/Silver/Gold)
- [ ] Define validation rules and thresholds
- [ ] Create Shadow DLT logic specification
- [ ] Design quarantine pattern
- [ ] Define reconciliation checks
- [ ] Document data lineage

**Phase 2: Build (Month 2)**
- [ ] Set up Databricks workspace and clusters
- [ ] Implement Bronze layer ingestion (Auto Loader)
- [ ] Build Quality Guard (Shadow DLT) with validation rules
- [ ] Create Silver Valid and Silver Quarantine tables
- [ ] Implement Gold layer aggregations
- [ ] Build audit logging system
- [ ] Create reconciliation validation queries

**Phase 3: Automate (Month 3)**
- [ ] Convert notebook to Delta Live Tables (DLT)
- [ ] Set up Databricks Jobs for scheduling
- [ ] Implement alerting (email/Teams)
- [ ] Create Monday morning automated check
- [ ] Build data lineage visualization
- [ ] Performance tuning and optimization

### Key Skills Required
- PySpark (Python + Spark)
- Delta Lake / Databricks
- SQL
- Data modeling
- ETL/ELT patterns
- YAML configuration

### Tools Used
- Databricks (Community Edition for demo → Enterprise for production)
- Python 3.10+
- Delta Lake
- Azure Data Lake Storage Gen2
- Git for version control

### Deliverables
1. **Bronze Pipeline**: Ingests files from ADLS to Delta tables
2. **Quality Guard**: Validates data and routes to Valid/Quarantine
3. **Gold Pipeline**: Aggregates clean data for reporting
4. **Audit System**: Logs all transformations and metrics
5. **Documentation**: Technical design docs, runbooks

### Time Estimate
- Demo/POC: 40 hours (1 week)
- Production: 320 hours (2 engineers × 2 months)

---

## Role 2: Platform/Infrastructure Team (IT)

### Primary Responsibilities
Provision and maintain the Azure infrastructure

### Specific Tasks

**Phase 1: Provisioning (Weeks 1-2)**
- [ ] Create Azure Databricks workspace (Premium tier)
- [ ] Set up ADLS Gen2 storage accounts
- [ ] Configure networking (VNet, Private Link if needed)
- [ ] Create service principals for authentication
- [ ] Set up Azure Key Vault for secrets
- [ ] Enable Azure Monitor and Application Insights

**Phase 2: Configuration (Weeks 3-4)**
- [ ] Configure Unity Catalog
- [ ] Set up RBAC (Role-Based Access Control)
- [ ] Create managed identities
- [ ] Configure data retention policies
- [ ] Set up backup and disaster recovery
- [ ] Enable audit logging

**Phase 3: Operations (Ongoing)**
- [ ] Monitor cluster health
- [ ] Manage costs and autoscaling
- [ ] Apply security patches
- [ ] Manage user access
- [ ] Handle incidents and support tickets
- [ ] Generate infrastructure reports

### Key Skills Required
- Azure administration
- Infrastructure as Code (Terraform/ARM templates)
- Networking
- Security and compliance
- Cost management

### Tools Used
- Azure Portal
- Azure CLI
- Terraform (optional)
- Azure DevOps

### Deliverables
1. **Databricks Workspace**: Configured and secured
2. **ADLS Storage**: Set up with proper access controls
3. **Unity Catalog**: Enabled for governance
4. **Documentation**: Infrastructure architecture, runbooks
5. **Cost Monitoring**: Dashboards and alerts

### Time Estimate
- Initial setup: 40 hours (1 week)
- Ongoing support: 4 hours/week

---

## Role 3: BI/Report Development Team (Power BI Experts)

### Primary Responsibilities
Build and maintain the Control Tower Power BI dashboard

### Specific Tasks

**Phase 1: Data Model (Weeks 1-2)**
- [ ] Connect Power BI to Databricks (JDBC/DirectQuery)
- [ ] Import Gold, Quarantine, and Audit tables
- [ ] Create star schema relationships
- [ ] Define date dimension
- [ ] Create dimension tables (Product, Store)
- [ ] Set up incremental refresh

**Phase 2: Measures & Calculations (Weeks 3-4)**
- [ ] Create DAX measures:
  - Trust Score %
  - Revenue at Risk
  - Quarantined Records
  - Reconciliation metrics
  - Trend calculations
- [ ] Create calculated columns as needed
- [ ] Build KPI scorecard logic

**Phase 3: Dashboard Design (Weeks 5-6)**
- [ ] Design Control Tower overview page
- [ ] Create Trust Score gauge visual
- [ ] Build Revenue at Risk card
- [ ] Add Decomposition Tree for root cause analysis
- [ ] Create Sankey diagram for data flow
- [ ] Build error analysis page
- [ ] Add trend charts and tables

**Phase 4: Publishing & Deployment (Week 7-8)**
- [ ] Publish to Power BI Service
- [ ] Create Power BI App
- [ ] Configure Row-Level Security (RLS)
- [ ] Set up scheduled refresh
- [ ] Create user documentation
- [ ] Conduct user training

### Key Skills Required
- Power BI Desktop & Service
- DAX (Data Analysis Expressions)
- Power Query M
- Data visualization best practices
- UX/UI design

### Tools Used
- Power BI Desktop
- Power BI Service
- DAX Studio (for testing)
- Tabular Editor (for advanced modeling)

### Deliverables
1. **Control Tower Dashboard**: Interactive Power BI report
2. **Power BI App**: Published and secured
3. **DAX Measures**: 40+ measures documented
4. **User Guide**: How to read and use the dashboard
5. **Training Materials**: Videos, presentations

### Time Estimate
- Demo: 16 hours (2 days)
- Production: 160 hours (1 developer × 1 month)

---

## Role 4: Business Analysts (BAs)

### Primary Responsibilities
Validate requirements, test the system, and become power users

### Specific Tasks

**Phase 1: Requirements (Weeks 1-2)**
- [ ] Document current manual Monday check process
- [ ] Define data quality criteria and thresholds
- [ ] Identify critical data elements to validate
- [ ] Specify error types and severity levels
- [ ] Define alert recipients and escalation paths

**Phase 2: Testing (Weeks 6-7)**
- [ ] Test Trust Score calculations
- [ ] Validate quarantine logic with sample errors
- [ ] Verify Decomposition Tree drill-down
- [ ] Test Power BI dashboard usability
- [ ] Validate reconciliation accuracy
- [ ] Provide feedback on UI/UX

**Phase 3: User Acceptance (Week 8)**
- [ ] Run parallel testing (Control Tower vs. manual checks)
- [ ] Document discrepancies
- [ ] Sign off on accuracy
- [ ] Participate in training
- [ ] Create cheat sheets and quick reference guides

**Phase 4: Adoption (Month 3+)**
- [ ] Use Control Tower for weekly Monday checks
- [ ] Log issues and enhancement requests
- [ ] Train other BAs and stakeholders
- [ ] Provide feedback for continuous improvement

### Key Skills Required
- Understanding of Circana data structure
- Data quality analysis
- Business domain knowledge (CPG/retail)
- Excel/SQL (basic)
- Attention to detail

### Tools Used
- Power BI Desktop (view-only or read access)
- Excel (for manual validation)
- Email/Teams (for alerts)

### Deliverables
1. **Requirements Document**: Validation rules and thresholds
2. **Test Cases**: Scenarios to validate
3. **UAT Sign-off**: Formal acceptance
4. **User Feedback**: Ongoing enhancement suggestions
5. **Training**: Onboard other users

### Time Estimate
- Requirements: 16 hours (2 days)
- Testing: 24 hours (3 days)
- Ongoing: 2 hours/week (Monday checks)

---

## Role 5: Data Steward

### Primary Responsibilities
Govern data quality rules and resolve quarantine issues

### Specific Tasks

**Ongoing Operations**
- [ ] Review quarantined records weekly
- [ ] Investigate root causes of errors
- [ ] Coordinate with source system teams (Circana, IT)
- [ ] Update Product Master and Store Master data
- [ ] Approve or reject quarantine records
- [ ] Escalate critical issues
- [ ] Maintain data dictionary
- [ ] Track data quality metrics over time

**Monthly Reviews**
- [ ] Generate data quality scorecards
- [ ] Present findings to steering committee
- [ ] Recommend process improvements
- [ ] Update validation rules as needed
- [ ] Conduct data quality audits

**Ad-Hoc**
- [ ] Handle data quality incidents
- [ ] Respond to stakeholder questions
- [ ] Coordinate new product launches
- [ ] Manage schema changes

### Key Skills Required
- Data governance expertise
- Understanding of business processes
- Strong communication skills
- Problem-solving
- Project management

### Tools Used
- Power BI (Control Tower dashboard)
- Excel (for analysis)
- Databricks (view quarantine data)
- Email/Teams (for coordination)

### Deliverables
1. **Weekly Reports**: Quarantine summary and actions taken
2. **Monthly Scorecards**: Data quality trends
3. **Issue Resolution**: Document fixes and learnings
4. **Process Documentation**: Updated runbooks

### Time Estimate
- Weekly: 4 hours
- Monthly: 8 hours
- Incidents: Variable (2-20 hours)

---

## Cross-Team Collaboration Matrix

| Task | Data Eng | Platform | BI Dev | BA | Steward |
|------|----------|----------|--------|-----|---------|
| **Design Pipeline** | **Lead** | Support | Consult | Consult | - |
| **Provision Infrastructure** | Consult | **Lead** | - | - | - |
| **Build Quality Rules** | **Lead** | - | - | Consult | **Co-Lead** |
| **Create Dashboard** | Support | - | **Lead** | Consult | Consult |
| **Define Thresholds** | Consult | - | - | **Lead** | **Co-Lead** |
| **Test System** | Support | Support | Support | **Lead** | Consult |
| **Resolve Quarantine** | Support | - | - | Consult | **Lead** |
| **Monitor Production** | **Lead** | Support | Support | - | Consult |

**Legend:**
- **Lead**: Primary responsibility, drives the work
- **Co-Lead**: Shares responsibility equally
- Support: Provides technical support
- Consult: Provides input and feedback
- `-`: Not involved

---

## Communication Plan

### Daily Standups (During Build Phase)
**Who**: Data Eng, Platform, BI Dev  
**Duration**: 15 minutes  
**Format**: 
- What did you do yesterday?
- What will you do today?
- Any blockers?

### Weekly Status Meeting
**Who**: All teams + Steering Committee  
**Duration**: 30 minutes  
**Agenda**:
- Progress update
- Risks and issues
- Decisions needed
- Next week's plan

### Monthly Review
**Who**: All teams + Stakeholders  
**Duration**: 60 minutes  
**Agenda**:
- Demo of latest features
- Data quality trends
- Lessons learned
- Roadmap review

---

## Escalation Path

**Level 1: Team Lead**
- Technical issues within team
- Day-to-day decisions
- Resource allocation

**Level 2: Steering Committee**
- Cross-team conflicts
- Budget decisions
- Scope changes
- Priority conflicts

**Level 3: Executive Sponsor**
- Strategic decisions
- Major budget increases
- Organizational change

---

## Onboarding Guide for New Team Members

### For Data Engineers
1. Read: ARCHITECTURE.md
2. Clone: GitHub repository
3. Set up: Local dev environment
4. Review: Databricks notebooks
5. Run: Demo pipeline on Community Edition
6. Shadow: Existing engineer for 1 week

### For Platform Engineers
1. Read: Infrastructure requirements
2. Access: Azure Portal and Databricks workspace
3. Review: Terraform configs (if used)
4. Shadow: Existing platform engineer
5. Complete: Azure Databricks certification (optional)

### For BI Developers
1. Read: USER_GUIDE.md and PPT_OUTLINE.md
2. Install: Power BI Desktop
3. Download: Sample .pbix file
4. Review: DAX measures
5. Build: Sample visual from scratch

### For Business Analysts
1. Read: USER_GUIDE.md
2. Watch: Demo video (create this)
3. Access: Power BI App (read-only)
4. Shadow: Senior BA for Monday check
5. Practice: Finding root causes with Decomposition Tree

### For Data Stewards
1. Read: Data governance policies
2. Access: Power BI Control Tower + Databricks
3. Review: Historical quarantine patterns
4. Shadow: Current steward for 2 weeks
5. Document: First resolved issue

---

## Success Metrics by Role

### Data Engineering
- Pipeline runs successfully: 99.9% success rate
- Processing time: < 30 minutes per batch
- Code coverage: > 80%
- Documentation: 100% of code documented

### Platform
- Uptime: 99.95%
- Incident response time: < 15 minutes
- Cost: Within budget ±10%
- Security: Zero breaches

### BI Development
- Dashboard load time: < 3 seconds
- User satisfaction: > 4.5/5
- Refresh success rate: 99%
- Training completion: 100% of users

### Business Analysts
- Monday check completion: 100% on time
- False positive rate: < 5%
- Issue escalation time: < 2 hours
- User adoption: 90%+ active users

### Data Steward
- Quarantine resolution time: < 24 hours
- Data quality score: > 95% Trust Score
- Documentation: 100% of issues logged
- Stakeholder satisfaction: > 4.5/5

---

## Handoff Checklist (Between Phases)

### Design → Build
- [ ] Architecture approved by all teams
- [ ] Requirements documented and signed off
- [ ] Infrastructure provisioned
- [ ] Dev environment set up
- [ ] Code repository created

### Build → Test
- [ ] All pipelines complete and unit tested
- [ ] Dashboard visuals built
- [ ] Documentation written
- [ ] Test data generated
- [ ] Test environment ready

### Test → Deploy
- [ ] UAT completed and signed off
- [ ] Performance tested
- [ ] Security scan passed
- [ ] Production environment ready
- [ ] Rollback plan documented

### Deploy → Operate
- [ ] Production deployment successful
- [ ] Users trained
- [ ] Runbooks finalized
- [ ] Monitoring enabled
- [ ] Support handoff complete

---

## Tools & Accounts Matrix

| Tool/System | Data Eng | Platform | BI Dev | BA | Steward |
|-------------|----------|----------|--------|-----|---------|
| **Databricks** | Full Access | Admin | Read-Only | - | Read-Only |
| **ADLS** | Read/Write | Admin | Read-Only | - | - |
| **Power BI** | View | - | Full Access | View | View |
| **Azure Portal** | View | Admin | - | - | - |
| **Git/GitHub** | Full | Full | Full | View | - |
| **Teams** | Yes | Yes | Yes | Yes | Yes |

---

## Final Checklist: Are All Teams Aligned?

Before starting implementation, verify:

- [ ] All teams have reviewed this document
- [ ] Roles and responsibilities are clear
- [ ] Everyone knows who to escalate to
- [ ] Communication channels are set up (Teams, Slack, etc.)
- [ ] Weekly meeting scheduled
- [ ] Access to tools and systems granted
- [ ] Budget approved
- [ ] Timeline agreed upon
- [ ] Success metrics defined
- [ ] Risks identified and mitigation plans in place

---

**Remember**: The Control Tower is a team effort. Clear communication and collaboration across teams is the key to success!
