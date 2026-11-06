# Task: Improve Tour de France OLAP Dashboard Visualizations (E1–E15)

## Project Context

I have already developed a Tour de France 2025 OLAP dashboard using **Streamlit, Python, SQLite, Pandas, and Altair** for my BT5110 Data Management & Warehousing project.

The dashboard already covers all 15 analytical requirements (E1–E15). However, many sections rely too heavily on tables, making the dashboard less visually engaging and analytical insights difficult to identify.

I want you to **enhance the existing dashboard using appropriate visualizations, without forcing every analytical requirement into a chart.**

**Important:** Do not rebuild the dashboard from scratch. Preserve its existing architecture, navigation, database queries, and working functionality.

---

## 1. Visualization Strategy

Follow these three categories.

### Category A — Chart-First (10 Requirements)

| E | Recommended Visualization | Analytical Purpose |
|---|---|---|
| E1 | Horizontal gap-to-leader bar chart + GC rank evolution line | Compare GC contenders and identify pivotal stages |
| E3 | 100% stacked horizontal bar chart | Show rider contributions to team aggregate time |
| E4 | Dumbbell / connected dot plot | Compare Overall GC, Young Rider GC, and Mountain GC Proxy |
| E5 | Bubble scatter plot | Compare mountain podium frequency and average time gap |
| E6 | Multi-line terrain profile | Compare rider/team speed across stage types |
| E7 | Interactive slope chart | Compare actual and counterfactual GC rankings |
| E9 | Bubble scatter plot | Compare national participation and podium performance |
| E10 | Multi-line time-series chart | Track GC time-gap evolution across stages |
| E12 | Rider × stage heatmap | Identify riders consistently finishing in the top 10 |
| E14 | Stacked bar chart by stage type | Compare team top-10 intensity across terrain |

**Implementation requirements:**

- Place the primary visualization prominently at the top of each section.
- Use meaningful axis labels, sorting, legends, and tooltips.
- Provide interactive filters and drill-down functionality.
- Keep detailed tables available in expandable sections where appropriate.
- Retain and improve existing charts when they already serve the analytical objective effectively.
- Do not duplicate visualizations unnecessarily.

### Category B — Hybrid: Chart + Table (4 Requirements)

#### E2 — A Stage in Focus

**Primary visualization:** Lollipop chart showing the top-10 finishers' adjusted time gaps to the stage winner.

**Secondary visualization:** Horizontal bar chart showing the number of top-10 finishers per team.

**Detail table:** Rider name, rank, team, adjusted time, and time gap.

**Interactions:**
- Select a stage.
- Switch between rider-level and team-level views.
- Display stage metadata: date, distance, terrain, origin, and destination.

#### E8 — Participation by Nation

**Primary visualization:** Ranked horizontal bar chart showing the number of riders per nation.

**Secondary metric:** Number of teams based in each country.

**Detail table:** Riders and their associated teams for a selected country.

**Interactions:**
- Select a country.
- Drill down from national participation to individual riders.
- Clearly distinguish rider nationality from team country.

#### E13 — Depth of Squads

**Primary visualization:** Segmented horizontal bar chart showing riders who completed the race versus riders who exited.

**Detail table:** Rider roster, nationality, role, and completion/exit status.

**Interactions:**
- Select a team to inspect its riders.
- Show completion ratios such as 7/8 or 6/8.
- Emphasize roster retention rather than initial roster size, because each team initially has eight riders.

#### E15 — The Long Day

**Primary visualization:** Ranked horizontal bar chart showing stage distances.

**Summary card:**
- Longest stage number
- Date
- Distance
- Terrain
- Origin and destination

**Detail table:** Leading finishers and their adjusted times.

**Interactions:**
- Highlight the longest stage.
- Allow users to select other stages for comparison.

**Category B implementation rules:**

- Place charts above detail tables.
- Use tables for exact records that cannot be communicated clearly through charts.
- Avoid redundant information.
- Ensure visual selections and filters update the corresponding tables.

### Category C — Table/Cards-First (1 Requirement)

#### E11 — Against the Clock (Individual Time Trials)

Do not force this requirement into a large chart.

The dataset contains only two ITT stages, so a compact catalogue is more appropriate.

**Recommended layout:** Two side-by-side comparison cards for Stage 5 and Stage 13.

Each card should display:
- Stage number and date
- Distance
- Start and finish locations
- Winner
- Winner's adjusted time
- Top-three finishers

Optionally include small horizontal bars showing the top-three finishers' time gaps.

Keep a compact table for exact stage and result information.

**Analytical objective:** Present the ITT stage inventory clearly without unnecessary visual complexity.

---

## 2. OLAP Functionality Requirements

The dashboard is for a Data Management & Warehousing course. Visualizations must demonstrate OLAP operations rather than simply displaying attractive charts.

Implement appropriate operations:

- **Roll-up:** Aggregate stage-level results into rider, team, or country summaries.
- **Drill-down:** Move from aggregated results to individual rider and stage records.
- **Slice:** Filter by a single dimension, such as team, rider, stage, or terrain.
- **Dice:** Filter by multiple dimensions simultaneously.
- **Pivot:** Switch analytical perspectives, such as rider-level versus team-level results.
- **What-if analysis:** Compare actual and alternative GC rankings in E7.

Where possible, follow this interaction flow:

**Summary visualization → Interactive filtering → Drill-down visualization → Detailed data table**

All charts, filters, and tables must remain connected to the same underlying data.

---

## 3. Dashboard Design and UX Requirements

1. Maintain the existing Tour de France-inspired visual identity and Streamlit layout.
2. Preserve the existing sidebar navigation and E1–E15 grouping.
3. Use consistent chart colors, fonts, labels, and formatting.
4. Avoid overcrowded charts and overlapping labels.
5. Use readable chart heights and appropriate axis scales.
6. Apply consistent terrain colors across relevant charts.
7. Provide tooltips with meaningful analytical details.
8. Use KPI cards only when they communicate useful summary metrics.
9. Move lengthy tables into `st.expander()` sections where appropriate.
10. Avoid unnecessary charts, duplicate visualizations, and excessive dashboard scrolling.
11. Ensure visualizations remain readable on typical laptop screens during a live presentation.
12. Prioritize analytical clarity over decorative elements.

---

## 4. Data Accuracy and Technical Requirements

- Use the existing SQLite database (`tdf.db`) as the source of truth.
- Review `main.py`, `olap.py`, and `db.py` before making changes.
- Preserve the existing database schema.
- Do not generate mock or synthetic data.
- Do not hardcode chart results.
- Use Altair where practical to avoid unnecessary dependencies.
- Preserve the existing adjusted-time formula:

  `adjusted_time = finish_time - bonus + penalty`

- Ensure GC rankings are calculated using the appropriate eligible riders and completed stages.
- Preserve correct calculations for bonuses, penalties, podium counts, stage rankings, and time gaps.
- Ensure riders who exited are not incorrectly included in final GC classifications.
- For E3, distinguish aggregate time contribution from rider performance.
- For E5, calculate mountain performance using Mountain stages only.
- For E9, distinguish national rider representation from team nationality.
- For E10, preserve the distinction between cumulative adjusted time and cumulative time gap to the GC leader.
- Ensure all charts are consistent with the existing OLAP queries and assignment requirements.

---

## 5. Implementation Workflow

### Step 1 — Review the Existing Implementation

Inspect the current code and identify:
- Which E1–E15 sections already have suitable visualizations.
- Which sections rely primarily on tables.
- Which charts require improvements.
- Which sections need new visualizations.
- Whether additional SQL queries or data transformations are required.

### Step 2 — Apply the Visualization Strategy

Implement Category A, B, and C according to the specifications above.

Do not replace a useful chart simply because a different chart was recommended. Evaluate whether the existing implementation already communicates the intended insight effectively.

### Step 3 — Integrate OLAP Interactions

Ensure filters, drill-downs, and scenario selectors work correctly with the new visualizations.

### Step 4 — Validate the Implementation

Verify that:
- All E1–E15 requirements remain covered.
- Charts display actual database results.
- Calculations are accurate.
- Filters and interactions work correctly.
- Tables and charts show consistent information.
- The dashboard runs without errors.

---

## 6. Expected Deliverables

1. Updated `main.py` and `olap.py`, with any necessary supporting changes.
2. All 15 analytical requirements retained and improved according to the three visualization categories.
3. Working interactive charts and drill-down functionality.
4. Preserved database integration and SQL functionality.
5. A short summary identifying which visualizations were added, improved, or retained.
6. Clear instructions for running the updated Streamlit dashboard.

---

## Final Objective

Deliver a professional, visually engaging, and analytically meaningful Tour de France OLAP dashboard.

Use charts where they improve interpretation, combine charts and tables where both are useful, and retain table/card layouts where they communicate information more effectively.

The final dashboard must demonstrate OLAP functionality clearly and remain suitable for a live university project presentation.

**Do not prioritize the number of charts. Prioritize the quality of insights, appropriateness of visualizations, and correctness of the underlying OLAP analysis.**