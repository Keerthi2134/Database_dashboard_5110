# 🚴 Tour de France Database and Interactive Analytics System
### BT5110 – Data Management & Warehousing (Group 39)

**Group Members:**
1. James Sharon Susan
2. Keerthivasan Radhakrishnan
3. Louise
4. Sulistyo Agung Wibowo

---

## 📌 Project Overview
This project presents an enterprise-grade multidimensional database and analytical OLAP dashboard for the **Tour de France**. 

Building upon the relational database design, minimal cover analysis, and BCNF normalization from **Project 2**, this platform integrates:
- Complete relational storage in SQLite (`tdf.db`) and PostgreSQL-compatible DDL (`data.sql`).
- Over **3,602** stage finish results, **184** riders across **23** professional teams, **39** locations, **30** nations, and **21** stages.
- An interactive **Streamlit OLAP Dashboard** covering all **15 Presentation-Time Demonstration Prompts (E1 through E15)** specified in the course requirements.
- An **Interactive SQL Studio** allowing ad-hoc queries, relational schema inspection, and data export.

---

## 🏗️ Architecture & Relational Schema

The relational schema implements 8 tables and 1 dynamic view designed to satisfy Boyce-Codd Normal Form (**BCNF**) without update, insertion, or deletion anomalies:

1. **`COUNTRY`** (`country_code` PK, `country_name`)
2. **`TEAM`** (`team_name` PK, `country_code` FK $\rightarrow$ `COUNTRY`)
3. **`RIDER`** (`bib_number` PK, `rider_name`, `dob`, `role`, `is_leader`, `team_name` FK $\rightarrow$ `TEAM`, `country_code` FK $\rightarrow$ `COUNTRY`)
4. **`LOCATION`** (`location_name` PK, `country_code` FK $\rightarrow$ `COUNTRY`)
5. **`STAGE`** (`stage_id` PK, `stage_date`, `distance_km`, `stage_type`, `start_location` FK $\rightarrow$ `LOCATION`, `finish_location` FK $\rightarrow$ `LOCATION`)
6. **`RESULT`** (`bib_number` FK $\rightarrow$ `RIDER`, `stage_id` FK $\rightarrow$ `STAGE`, `rank`, `finish_time`, `bonus`, `penalty`, PK: `(bib_number, stage_id)`)
7. **`RESULT_WITH_ADJ_TIME`** (View): Calculates derived attribute $\text{adj\_time} = \text{finish\_time} - \text{bonus} + \text{penalty}$ dynamically.
8. **`EXIT`** (`bib_number` PK $\rightarrow$ `RIDER`, `stage_id` FK $\rightarrow$ `STAGE`, `reason`)
9. **`AWARD`** (`award_id` PK, `award_name`, `bib_number` FK, `team_name` FK, XOR constraint ensuring recipient is either a rider or team)

---

## 🎯 15 OLAP Demonstration Prompts (E1 – E15)

The dashboard is structured into interactive modules addressing every analytical requirement:

### Module 1: General Classification & Storylines
- **E1. GC Leaderboard with Contextual Descent:** Overall General Classification ordered by lowest $\sum \text{adjusted\_time}$. Interactive drilldown following a chosen contender to stage grain, automatically surfacing the **single pivotal day** that most altered their race (e.g., stage rank swings or gap shifts).
- **E4. Parallel Classifications:** Side-by-side comparison of GC rank, Young Rider GC rank (filtered for riders born $\ge$ 2000-01-01), and Mountain-Stage GC Proxy (time on 'mountain' stages). Surfaces divergences where climbers excel compared to all-rounders.
- **E7. Bonuses, Penalties, and Counterfactuals:** Cumulative bonuses and penalties per rider. Replay GC leaderboard under counterfactual toggles (Actual vs. Without Bonuses vs. Without Penalties vs. Raw Elapsed Time) to illuminate movements into/out of the top 10.
- **E10. Temporal GC Storyline:** Interactive multi-line narrative tracing cumulative time gaps to the leader stage-by-stage for user-selected contenders, annotating decisive inflection points across mountain and time-trial stages.

### Module 2: Stages & Terrain Dynamics
- **E2. A Stage in Focus:** Vignette view of any of the 21 stages (distance, start/finish locations, terrain profile) with leading finishers and a team perspective revealing which squads populated the top 10 on that day.
- **E5. Mountain Contours:** Identifies elite climbers via two signals: podium frequency (top-3 finishes) on mountain stages and mean time gap to the stage winner, with instant drilldown to daily traces.
- **E6. Speed Profiles as Simple Ratio:** Computes proxy speed ($\text{km/h} = \text{distance} / \text{time}$) across Flat, Hilly, Mountain, and ITT, highlighting riders and teams that retain speed when terrain shifts to mountains.
- **E11. Against the Clock:** Compact catalogue of Individual Time Trial (ITT) stages (Stage 5 Caen and Stage 13 Loudenvielle $\rightarrow$ Peyragudes), date, distance, winner, speed, and podium leaderboards.
- **E15. The Long Day:** All 21 stages sorted by distance, spotlighting the longest route (Stage 2: 209.1 km, Lauwin-Planque $\rightarrow$ Boulogne-Sur-Mer), its endurance profile, and leading finishers.

### Module 3: Teams & Squad Dynamics
- **E3. Team Burden and Contribution:** Rollup of each team's aggregate adjusted time, opened to reveal which riders carried the time load (% share of team total time) and how their roles shaped squad outcomes.
- **E13. Depth of Squads:** Squad depth metrics across all 23 teams (initial roster of 8, active finishers, attrition/exits), with an expandable doorway to full rosters and rider statuses.
- **E14. Top-Ten Intensity by Team:** Aggregate top-ten finishes per squad broken down by stage type (Flat, Hilly, Mountain, ITT) with drilldown links to specific stages and riders.

### Module 4: Nations & Rider Consistency
- **E8. Participation by Nation:** Rollup of all 30 nations by presence (count of teams and riders), opening into individual athlete lists and squad affiliations.
- **E9. National Outcomes:** Best GC rank, stage wins, and podiums for each nation, with a clear pathway back to underlying stages and athletes.
- **E12. Consistency Near the Front:** Leaderboard of riders who most frequently appeared in the top 10 across all 21 stages, accompanied by contributing stages and terrain types.

### Module 5: Data Warehouse & SQL Studio
- **Interactive SQL Console:** Run custom SQL queries directly against `tdf.db` with sample queries, execution timer, and CSV export.
- **Live Table Browser:** Inspect rows from all 8 relational tables and the dynamic view.
- **Relational Schema & BCNF Justifications:** Complete schema documentation and normalization analysis.

---

## 🚀 How to Run the Dashboard

### 1. Requirements
Ensure Python 3.10+ is installed with the required libraries:
```bash
pip install streamlit pandas numpy altair
```

### 2. Launch the Streamlit App
Run the following command in the project directory:
```bash
streamlit run main.py
```
Or execute the companion launcher:
```bash
python subapp.py
```

The application will open in your default web browser at `http://localhost:8501`.

---

## 📁 Repository Structure
```text
Database_dashboard_5110/
├── main.py                  # Main Streamlit Interactive Dashboard
├── olap.py                  # OLAP Analytical functions implementing E1 - E15
├── db.py                    # SQLite database connection & query helpers
├── build_database.py        # Automated ETL script creating tdf.db & data.sql
├── data.sql                 # Complete SQL DDL, view, and INSERT statements (459 KB)
├── tdf.db                   # SQLite database (8 tables, 1 view, 3,602 results)
├── subapp.py                # Companion quick launcher
├── README.md                # Project documentation and guide
└── references/              # Project reference materials & source datasets
    ├── Group 39_Project2_V2.pdf
    ├── project dashboard suggested functions-1.pdf
    ├── individual_results.csv
    ├── riders.csv
    └── exits.csv
```
