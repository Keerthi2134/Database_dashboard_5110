import sys
sys.stdout.reconfigure(encoding="utf-8")
import sqlite3
import pandas as pd
import numpy as np

def build():
    df_res = pd.read_csv("references/individual_results.csv", encoding="utf-8")
    df_riders = pd.read_csv("references/riders.csv", encoding="utf-8")
    df_exits = pd.read_csv("references/exits.csv", encoding="utf-8")

    # 1. Countries
    countries = {}
    for _, r in df_riders.iterrows():
        if pd.notna(r["rider_country_code"]):
            countries[r["rider_country_code"].strip()] = r["rider_country_name"].strip()
        if pd.notna(r["team_country_code"]):
            countries[r["team_country_code"].strip()] = r["team_country_name"].strip()
    for _, r in df_res.iterrows():
        if pd.notna(r["start_country_code"]):
            countries[r["start_country_code"].strip()] = r["start_country_name"].strip()
        if pd.notna(r["finish_country_code"]):
            countries[r["finish_country_code"].strip()] = r["finish_country_name"].strip()
    
    # Aleksandr Vlasov
    countries["RUS"] = "Russia"

    # 2. Locations
    locations = {}
    for _, r in df_res.iterrows():
        locations[r["start_location"].strip()] = r["start_country_code"].strip()
        locations[r["finish_location"].strip()] = r["finish_country_code"].strip()

    # 3. Teams
    teams = {}
    for _, r in df_riders.iterrows():
        teams[r["team"].strip()] = r["team_country_code"].strip()

    # 4. Stages
    stages_df = df_res[["day", "start_location", "finish_location", "length", "type"]].drop_duplicates().sort_values("day").reset_index(drop=True)
    stages_df["stage_id"] = stages_df.index + 1
    
    # Map day -> stage_id
    day_to_stage = dict(zip(stages_df["day"], stages_df["stage_id"]))
    df_res["stage_id"] = df_res["day"].map(day_to_stage)

    # 5. Riders & Roles
    # Determine rider roles:
    # Leaders have bib % 10 == 1
    # Check top finishes by type:
    flat_pts = df_res[df_res["type"] == "flat"].groupby("rider")["rank"].apply(lambda s: (s <= 10).sum())
    mtn_pts = df_res[df_res["type"] == "mountain"].groupby("rider")["rank"].apply(lambda s: (s <= 15).sum())
    itt_pts = df_res[df_res["type"] == "individual time-trial"].groupby("rider")["rank"].apply(lambda s: (s <= 10).sum())
    hilly_pts = df_res[df_res["type"] == "hilly"].groupby("rider")["rank"].apply(lambda s: (s <= 10).sum())

    riders_data = []
    for _, r in df_riders.iterrows():
        bib = int(r["bib"])
        name = r["rider_name"].strip()
        dob = r["dob"].strip()
        team = r["team"].strip()
        ccode = r["rider_country_code"].strip() if pd.notna(r["rider_country_code"]) else "RUS"
        
        is_leader = (bib % 10 == 1)
        if is_leader:
            role = "Leader"
        elif flat_pts.get(bib, 0) >= 2:
            role = "Sprinter"
        elif mtn_pts.get(bib, 0) >= 2:
            role = "Climber"
        elif itt_pts.get(bib, 0) >= 1:
            role = "Time Trialist"
        elif hilly_pts.get(bib, 0) >= 2:
            role = "Puncheur"
        else:
            role = "Domestique"
            
        riders_data.append((bib, name, dob, role, 1 if is_leader else 0, team, ccode))

    # 6. Results
    results_data = []
    for _, r in df_res.iterrows():
        results_data.append((
            int(r["rider"]),
            int(r["stage_id"]),
            int(r["rank"]),
            int(r["time"]),
            int(r["bonus"]),
            int(r["penalty"])
        ))

    # 7. Exits
    exits_data = []
    for _, r in df_exits.iterrows():
        exits_data.append((
            int(r["bib"]),
            int(r["stage"]),
            r["reason"].strip()
        ))

    # 8. Awards
    awards_data = [
        (1, "Maillot Jaune (General Classification Winner)", 1, None),
        (2, "Maillot Blanc (Best Young Rider)", 72, None),
        (3, "Maillot Vert (Points Classification)", 81, None),
        (4, "Maillot à Pois (Mountains Classification)", 1, None),
        (5, "Prix de la Combativité (Super Combativity)", 31, None),
        (6, "Classement par Équipes (Team Classification)", None, "TEAM VISMA | LEASE A BIKE"),
    ]
    # Add stage winner awards
    award_idx = 7
    for _, r in stages_df.iterrows():
        sid = int(r["stage_id"])
        w = df_res[(df_res["stage_id"] == sid) & (df_res["rank"] == 1)].iloc[0]
        awards_data.append((
            award_idx,
            f"Vainqueur d'Étape {sid} ({r['type'].capitalize()})",
            int(w["rider"]),
            None
        ))
        award_idx += 1

    # Connect to SQLite
    db_path = "tdf.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = OFF;") # Temporarily drop/create tables

    # Drop existing tables
    cur.executescript("""
    DROP VIEW IF EXISTS result_with_adj_time;
    DROP TABLE IF EXISTS award;
    DROP TABLE IF EXISTS exit;
    DROP TABLE IF EXISTS result;
    DROP TABLE IF EXISTS stage;
    DROP TABLE IF EXISTS rider;
    DROP TABLE IF EXISTS location;
    DROP TABLE IF EXISTS team;
    DROP TABLE IF EXISTS country;
    """)

    # Create Tables matching Group 39 Schema
    cur.executescript("""
    CREATE TABLE country (
        country_code CHAR(3) PRIMARY KEY,
        country_name VARCHAR(100) NOT NULL,
        CHECK (length(country_code) = 3)
    );

    CREATE TABLE team (
        team_name VARCHAR(100) PRIMARY KEY,
        country_code CHAR(3) NOT NULL,
        FOREIGN KEY (country_code) REFERENCES country(country_code)
    );

    CREATE TABLE location (
        location_name VARCHAR(100) PRIMARY KEY,
        country_code CHAR(3) NOT NULL,
        FOREIGN KEY (country_code) REFERENCES country(country_code)
    );

    CREATE TABLE rider (
        bib_number INTEGER PRIMARY KEY,
        rider_name VARCHAR(100) NOT NULL,
        dob DATE NOT NULL,
        role VARCHAR(50) NOT NULL,
        is_leader BOOLEAN NOT NULL,
        team_name VARCHAR(100) NOT NULL,
        country_code CHAR(3) NOT NULL,
        FOREIGN KEY (team_name) REFERENCES team(team_name),
        FOREIGN KEY (country_code) REFERENCES country(country_code)
    );

    CREATE TABLE stage (
        stage_id INTEGER PRIMARY KEY,
        stage_date DATE NOT NULL,
        distance_km NUMERIC(5, 2) NOT NULL,
        stage_type VARCHAR(30) NOT NULL,
        start_location VARCHAR(100) NOT NULL,
        finish_location VARCHAR(100) NOT NULL,
        FOREIGN KEY (start_location) REFERENCES location(location_name),
        FOREIGN KEY (finish_location) REFERENCES location(location_name),
        CHECK (distance_km > 0),
        CHECK (stage_type IN ('flat', 'hilly', 'mountain', 'individual time-trial'))
    );

    CREATE TABLE result (
        bib_number INTEGER NOT NULL,
        stage_id INTEGER NOT NULL,
        rank INTEGER NOT NULL,
        finish_time INTEGER NOT NULL,
        bonus INTEGER NOT NULL DEFAULT 0,
        penalty INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (bib_number, stage_id),
        FOREIGN KEY (bib_number) REFERENCES rider(bib_number),
        FOREIGN KEY (stage_id) REFERENCES stage(stage_id),
        CHECK (rank > 0),
        CHECK (finish_time >= 0),
        CHECK (bonus >= 0),
        CHECK (penalty >= 0)
    );

    CREATE VIEW result_with_adj_time AS
    SELECT
        bib_number,
        stage_id,
        rank,
        finish_time,
        bonus,
        penalty,
        (finish_time - bonus + penalty) AS adj_time
    FROM result;

    CREATE TABLE exit (
        bib_number INTEGER PRIMARY KEY,
        stage_id INTEGER NOT NULL,
        reason VARCHAR(255) NOT NULL,
        FOREIGN KEY (bib_number) REFERENCES rider(bib_number),
        FOREIGN KEY (stage_id) REFERENCES stage(stage_id)
    );

    CREATE TABLE award (
        award_id INTEGER PRIMARY KEY,
        award_name VARCHAR(100) NOT NULL,
        bib_number INTEGER,
        team_name VARCHAR(100),
        FOREIGN KEY (bib_number) REFERENCES rider(bib_number),
        FOREIGN KEY (team_name) REFERENCES team(team_name),
        CHECK (
            (bib_number IS NOT NULL AND team_name IS NULL)
            OR
            (bib_number IS NULL AND team_name IS NOT NULL)
        )
    );
    """)

    # Populate SQLite
    cur.executemany("INSERT INTO country VALUES (?, ?);", sorted(countries.items()))
    cur.executemany("INSERT INTO team VALUES (?, ?);", sorted(teams.items()))
    cur.executemany("INSERT INTO location VALUES (?, ?);", sorted(locations.items()))
    cur.executemany("INSERT INTO rider VALUES (?, ?, ?, ?, ?, ?, ?);", riders_data)
    
    stages_rows = [
        (int(r["stage_id"]), r["day"], float(r["length"]), r["type"], r["start_location"], r["finish_location"])
        for _, r in stages_df.iterrows()
    ]
    cur.executemany("INSERT INTO stage VALUES (?, ?, ?, ?, ?, ?);", stages_rows)
    cur.executemany("INSERT INTO result VALUES (?, ?, ?, ?, ?, ?);", results_data)
    cur.executemany("INSERT INTO exit VALUES (?, ?, ?);", exits_data)
    cur.executemany("INSERT INTO award VALUES (?, ?, ?, ?);", awards_data)

    conn.commit()
    conn.close()
    print("Database tdf.db created and populated successfully!")

    # Now write data.sql
    with open("data.sql", "w", encoding="utf-8") as f:
        f.write("-- ==========================================================================\n")
        f.write("-- Tour de France Database and Analytics System (BT5110 - Group 39)\n")
        f.write("-- Authors: James Sharon Susan, Keerthivasan Radhakrishnan, Louise, Sulistyo Agung Wibowo\n")
        f.write("-- Relational Schema DDL, View, and Population Data\n")
        f.write("-- ==========================================================================\n\n")

        f.write("-- Drop existing structures if they exist\n")
        f.write("DROP VIEW IF EXISTS result_with_adj_time;\n")
        f.write("DROP TABLE IF EXISTS award;\n")
        f.write("DROP TABLE IF EXISTS exit;\n")
        f.write("DROP TABLE IF EXISTS result;\n")
        f.write("DROP TABLE IF EXISTS stage;\n")
        f.write("DROP TABLE IF EXISTS rider;\n")
        f.write("DROP TABLE IF EXISTS location;\n")
        f.write("DROP TABLE IF EXISTS team;\n")
        f.write("DROP TABLE IF EXISTS country;\n\n")

        f.write("-- 1. COUNTRY Table\n")
        f.write("CREATE TABLE country (\n")
        f.write("    country_code CHAR(3) PRIMARY KEY,\n")
        f.write("    country_name VARCHAR(100) NOT NULL,\n")
        f.write("    CHECK (country_code ~ '^[A-Z]{3}$')\n")
        f.write(");\n\n")

        f.write("-- 2. TEAM Table\n")
        f.write("CREATE TABLE team (\n")
        f.write("    team_name VARCHAR(100) PRIMARY KEY,\n")
        f.write("    country_code CHAR(3) NOT NULL,\n")
        f.write("    FOREIGN KEY (country_code) REFERENCES country(country_code)\n")
        f.write(");\n\n")

        f.write("-- 3. LOCATION Table\n")
        f.write("CREATE TABLE location (\n")
        f.write("    location_name VARCHAR(100) PRIMARY KEY,\n")
        f.write("    country_code CHAR(3) NOT NULL,\n")
        f.write("    FOREIGN KEY (country_code) REFERENCES country(country_code)\n")
        f.write(");\n\n")

        f.write("-- 4. RIDER Table\n")
        f.write("CREATE TABLE rider (\n")
        f.write("    bib_number INTEGER PRIMARY KEY,\n")
        f.write("    rider_name VARCHAR(100) NOT NULL,\n")
        f.write("    dob DATE NOT NULL,\n")
        f.write("    role VARCHAR(50) NOT NULL,\n")
        f.write("    is_leader BOOLEAN NOT NULL,\n")
        f.write("    team_name VARCHAR(100) NOT NULL,\n")
        f.write("    country_code CHAR(3) NOT NULL,\n")
        f.write("    FOREIGN KEY (team_name) REFERENCES team(team_name),\n")
        f.write("    FOREIGN KEY (country_code) REFERENCES country(country_code)\n")
        f.write(");\n\n")

        f.write("-- 5. STAGE Table\n")
        f.write("CREATE TABLE stage (\n")
        f.write("    stage_id INTEGER PRIMARY KEY,\n")
        f.write("    stage_date DATE NOT NULL,\n")
        f.write("    distance_km NUMERIC(5, 2) NOT NULL,\n")
        f.write("    stage_type VARCHAR(30) NOT NULL,\n")
        f.write("    start_location VARCHAR(100) NOT NULL,\n")
        f.write("    finish_location VARCHAR(100) NOT NULL,\n")
        f.write("    FOREIGN KEY (start_location) REFERENCES location(location_name),\n")
        f.write("    FOREIGN KEY (finish_location) REFERENCES location(location_name),\n")
        f.write("    CHECK (distance_km > 0),\n")
        f.write("    CHECK (stage_type IN ('flat', 'hilly', 'mountain', 'individual time-trial'))\n")
        f.write(");\n\n")

        f.write("-- 6. RESULT Table\n")
        f.write("CREATE TABLE result (\n")
        f.write("    bib_number INTEGER NOT NULL,\n")
        f.write("    stage_id INTEGER NOT NULL,\n")
        f.write("    rank INTEGER NOT NULL,\n")
        f.write("    finish_time INTEGER NOT NULL,\n")
        f.write("    bonus INTEGER NOT NULL DEFAULT 0,\n")
        f.write("    penalty INTEGER NOT NULL DEFAULT 0,\n")
        f.write("    PRIMARY KEY (bib_number, stage_id),\n")
        f.write("    FOREIGN KEY (bib_number) REFERENCES rider(bib_number),\n")
        f.write("    FOREIGN KEY (stage_id) REFERENCES stage(stage_id),\n")
        f.write("    CHECK (rank > 0),\n")
        f.write("    CHECK (finish_time >= 0),\n")
        f.write("    CHECK (bonus >= 0),\n")
        f.write("    CHECK (penalty >= 0)\n")
        f.write(");\n\n")

        f.write("-- 7. RESULT_WITH_ADJ_TIME View\n")
        f.write("CREATE VIEW result_with_adj_time AS\n")
        f.write("SELECT\n")
        f.write("    bib_number,\n")
        f.write("    stage_id,\n")
        f.write("    rank,\n")
        f.write("    finish_time,\n")
        f.write("    bonus,\n")
        f.write("    penalty,\n")
        f.write("    (finish_time - bonus + penalty) AS adj_time\n")
        f.write("FROM result;\n\n")

        f.write("-- 8. EXIT Table\n")
        f.write("CREATE TABLE exit (\n")
        f.write("    bib_number INTEGER PRIMARY KEY,\n")
        f.write("    stage_id INTEGER NOT NULL,\n")
        f.write("    reason VARCHAR(255) NOT NULL,\n")
        f.write("    FOREIGN KEY (bib_number) REFERENCES rider(bib_number),\n")
        f.write("    FOREIGN KEY (stage_id) REFERENCES stage(stage_id)\n")
        f.write(");\n\n")

        f.write("-- 9. AWARD Table\n")
        f.write("CREATE TABLE award (\n")
        f.write("    award_id INTEGER PRIMARY KEY,\n")
        f.write("    award_name VARCHAR(100) NOT NULL,\n")
        f.write("    bib_number INTEGER,\n")
        f.write("    team_name VARCHAR(100),\n")
        f.write("    FOREIGN KEY (bib_number) REFERENCES rider(bib_number),\n")
        f.write("    FOREIGN KEY (team_name) REFERENCES team(team_name),\n")
        f.write("    CHECK (\n")
        f.write("        (bib_number IS NOT NULL AND team_name IS NULL)\n")
        f.write("        OR\n")
        f.write("        (bib_number IS NULL AND team_name IS NOT NULL)\n")
        f.write("    )\n")
        f.write(");\n\n")

        # INSERT DATA
        f.write("-- --------------------------------------------------------------------------\n")
        f.write("-- DATA INSERTIONS\n")
        f.write("-- --------------------------------------------------------------------------\n\n")

        def esc(val):
            return str(val).replace("'", "''")

        # Countries
        f.write("-- Insert Countries\n")
        for ccode, cname in sorted(countries.items()):
            f.write(f"INSERT INTO country (country_code, country_name) VALUES ('{esc(ccode)}', '{esc(cname)}');\n")
        f.write("\n")

        # Teams
        f.write("-- Insert Teams\n")
        for tname, ccode in sorted(teams.items()):
            f.write(f"INSERT INTO team (team_name, country_code) VALUES ('{esc(tname)}', '{esc(ccode)}');\n")
        f.write("\n")

        # Locations
        f.write("-- Insert Locations\n")
        for lname, ccode in sorted(locations.items()):
            f.write(f"INSERT INTO location (location_name, country_code) VALUES ('{esc(lname)}', '{esc(ccode)}');\n")
        f.write("\n")

        # Stages
        f.write("-- Insert Stages\n")
        for r in stages_rows:
            f.write(f"INSERT INTO stage (stage_id, stage_date, distance_km, stage_type, start_location, finish_location) VALUES ({r[0]}, '{r[1]}', {r[2]}, '{esc(r[3])}', '{esc(r[4])}', '{esc(r[5])}');\n")
        f.write("\n")

        # Riders
        f.write("-- Insert Riders\n")
        for r in riders_data:
            leader_str = "TRUE" if r[4] else "FALSE"
            f.write(f"INSERT INTO rider (bib_number, rider_name, dob, role, is_leader, team_name, country_code) VALUES ({r[0]}, '{esc(r[1])}', '{r[2]}', '{esc(r[3])}', {leader_str}, '{esc(r[5])}', '{esc(r[6])}');\n")
        f.write("\n")

        # Exits
        f.write("-- Insert Exits\n")
        for r in exits_data:
            f.write(f"INSERT INTO exit (bib_number, stage_id, reason) VALUES ({r[0]}, {r[1]}, '{esc(r[2])}');\n")
        f.write("\n")

        # Awards
        f.write("-- Insert Awards\n")
        for r in awards_data:
            b_val = str(r[2]) if r[2] is not None else "NULL"
            t_val = f"'{esc(r[3])}'" if r[3] is not None else "NULL"
            f.write(f"INSERT INTO award (award_id, award_name, bib_number, team_name) VALUES ({r[0]}, '{esc(r[1])}', {b_val}, {t_val});\n")
        f.write("\n")

        # Results
        f.write("-- Insert Results (3,602 rows)\n")
        for r in results_data:
            f.write(f"INSERT INTO result (bib_number, stage_id, rank, finish_time, bonus, penalty) VALUES ({r[0]}, {r[1]}, {r[2]}, {r[3]}, {r[4]}, {r[5]});\n")

    print(f"data.sql written successfully! Size: {pd.Series([open('data.sql', 'rb').read()]).map(len).iloc[0]} bytes")

if __name__ == "__main__":
    build()
