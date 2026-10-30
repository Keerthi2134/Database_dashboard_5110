"""
OLAP Analytical Narratives module for Tour de France Analytics System.
Implements the 15 OLAP Demonstration Prompts E1 through E15 using SQLite backend.
"""

import pandas as pd
import numpy as np
from db import execute_query, format_seconds, format_gap

# ==============================================================================
# E1. GC LEADERBOARD WITH CONTEXTUAL DESCENT
# ==============================================================================

def get_gc_leaderboard(up_to_stage: int = 21) -> pd.DataFrame:
    """Computes GC leaderboard after up_to_stage ordered by cumulative adjusted time."""
    q = """
    WITH stage_filter AS (
        SELECT 
            r.bib_number,
            rd.rider_name,
            rd.team_name,
            rd.country_code,
            rd.role,
            rd.is_leader,
            COUNT(r.stage_id) AS stages_completed,
            SUM(r.finish_time) AS total_finish_time,
            SUM(r.bonus) AS total_bonus,
            SUM(r.penalty) AS total_penalty,
            SUM(r.adj_time) AS total_adj_time
        FROM result_with_adj_time r
        JOIN rider rd ON r.bib_number = rd.bib_number
        WHERE r.stage_id <= ?
        GROUP BY r.bib_number
        HAVING stages_completed = ?
    )
    SELECT 
        bib_number,
        rider_name,
        team_name,
        country_code,
        role,
        is_leader,
        stages_completed,
        total_finish_time,
        total_bonus,
        total_penalty,
        total_adj_time,
        RANK() OVER (ORDER BY total_adj_time ASC) AS gc_rank
    FROM stage_filter
    ORDER BY gc_rank ASC;
    """
    df = execute_query(q, (up_to_stage, up_to_stage))
    if not df.empty:
        leader_time = df.loc[0, "total_adj_time"]
        df["gap_to_leader"] = df["total_adj_time"] - leader_time
        df["time_formatted"] = df["total_adj_time"].apply(format_seconds)
        df["gap_formatted"] = df["gap_to_leader"].apply(format_gap)
    return df

def get_rider_stage_descent(bib_number: int) -> pd.DataFrame:
    """Returns stage-grain results and progressive GC rank for a chosen contender."""
    q = """
    WITH cum_results AS (
        SELECT 
            r.stage_id,
            r.bib_number,
            r.rank AS stage_rank,
            r.finish_time,
            r.bonus,
            r.penalty,
            r.adj_time,
            SUM(r.adj_time) OVER (PARTITION BY r.bib_number ORDER BY r.stage_id) AS cum_adj_time,
            COUNT(r.stage_id) OVER (PARTITION BY r.bib_number ORDER BY r.stage_id) AS stages_so_far
        FROM result_with_adj_time r
    ),
    stage_leaders AS (
        SELECT stage_id, MIN(cum_adj_time) AS leader_cum_time
        FROM cum_results
        GROUP BY stage_id
    ),
    all_gc_ranks AS (
        SELECT 
            c.stage_id,
            c.bib_number,
            c.stage_rank,
            c.finish_time,
            c.bonus,
            c.penalty,
            c.adj_time,
            c.cum_adj_time,
            (c.cum_adj_time - l.leader_cum_time) AS gap_to_leader,
            RANK() OVER (PARTITION BY c.stage_id ORDER BY c.cum_adj_time ASC) AS gc_rank_stage
        FROM cum_results c
        JOIN stage_leaders l ON c.stage_id = l.stage_id
    ),
    with_lags AS (
        SELECT 
            a.*,
            LAG(a.gc_rank_stage) OVER (PARTITION BY a.bib_number ORDER BY a.stage_id) AS prev_gc_rank,
            LAG(a.gap_to_leader) OVER (PARTITION BY a.bib_number ORDER BY a.stage_id) AS prev_gap
        FROM all_gc_ranks a
    )
    SELECT 
        w.stage_id,
        s.stage_date,
        s.stage_type,
        s.distance_km,
        s.start_location,
        s.finish_location,
        w.stage_rank,
        w.finish_time,
        w.bonus,
        w.penalty,
        w.adj_time,
        w.cum_adj_time,
        w.gc_rank_stage,
        w.gap_to_leader,
        COALESCE(w.prev_gc_rank - w.gc_rank_stage, 0) AS rank_change,
        COALESCE(w.gap_to_leader - w.prev_gap, 0) AS gap_change
    FROM with_lags w
    JOIN stage s ON w.stage_id = s.stage_id
    WHERE w.bib_number = ?
    ORDER BY w.stage_id ASC;
    """
    df = execute_query(q, (bib_number,))
    if not df.empty:
        df["adj_time_formatted"] = df["adj_time"].apply(format_seconds)
        df["cum_time_formatted"] = df["cum_adj_time"].apply(format_seconds)
        df["gap_formatted"] = df["gap_to_leader"].apply(format_gap)
        df["gap_change_formatted"] = df["gap_change"].apply(format_gap)
    return df

def get_pivotal_moment(df_descent: pd.DataFrame) -> dict:
    """Identifies the single day that most altered GC standing for the rider."""
    if df_descent.empty:
        return {}
    
    # Exclude stage 1 for change metric since prev is NaN/0
    sub = df_descent[df_descent["stage_id"] > 1]
    if sub.empty:
        piv = df_descent.iloc[0]
        return {
            "stage_id": piv["stage_id"],
            "type": piv["stage_type"],
            "distance": piv["distance_km"],
            "reason": "Stage 1 Opening Baseline",
            "gap_change": piv["gap_to_leader"],
            "rank_change": 0,
            "final_rank": piv["gc_rank_stage"]
        }
    
    # Pivot criterion: Maximum absolute gap change to leader or largest rank shift
    sub = sub.copy()
    sub["abs_gap_change"] = sub["gap_change"].abs()
    sub["abs_rank_change"] = sub["rank_change"].abs()
    
    # Prioritize large gap change (time lost or gained on a mountain/ITT day)
    idx_max_gap = sub["abs_gap_change"].idxmax()
    idx_max_rank = sub["abs_rank_change"].idxmax()
    
    piv = sub.loc[idx_max_gap]
    piv_rank = sub.loc[idx_max_rank]
    
    gap_val = piv["gap_change"]
    if gap_val < 0:
        narrative = f"Pivotal breakthrough on Stage {piv['stage_id']} ({piv['stage_type'].title()}): Gained {format_gap(abs(gap_val))} on the GC leader!"
    elif gap_val > 0:
        narrative = f"Pivotal ordeal on Stage {piv['stage_id']} ({piv['stage_type'].title()}): Lost {format_gap(gap_val)} to the GC leader."
    else:
        narrative = f"Key moment on Stage {piv['stage_id']}: Steady time hold in {piv['stage_type']} terrain."

    return {
        "stage_id": int(piv["stage_id"]),
        "stage_date": piv["stage_date"],
        "stage_type": piv["stage_type"],
        "route": f"{piv['start_location']} → {piv['finish_location']}",
        "distance_km": piv["distance_km"],
        "stage_rank": int(piv["stage_rank"]),
        "gc_rank_after": int(piv["gc_rank_stage"]),
        "gap_change": int(piv["gap_change"]),
        "rank_change": int(piv["rank_change"]),
        "narrative": narrative
    }

# ==============================================================================
# E2. A STAGE IN FOCUS (STAGE VIGNETTE & TEAM PERSPECTIVE)
# ==============================================================================

def get_stage_vignette(stage_id: int) -> dict:
    """Returns stage metadata."""
    q = "SELECT * FROM stage WHERE stage_id = ?;"
    df = execute_query(q, (stage_id,))
    if df.empty:
        return {}
    row = df.iloc[0]
    return {
        "stage_id": int(row["stage_id"]),
        "stage_date": row["stage_date"],
        "distance_km": float(row["distance_km"]),
        "stage_type": row["stage_type"],
        "start_location": row["start_location"],
        "finish_location": row["finish_location"]
    }

def get_stage_finishers(stage_id: int, top_n: int = 15) -> pd.DataFrame:
    """Returns top finishers for a specific stage with times and gaps."""
    q = """
    SELECT 
        r.rank,
        r.bib_number,
        rd.rider_name,
        rd.team_name,
        rd.country_code,
        r.finish_time,
        r.bonus,
        r.penalty,
        r.adj_time
    FROM result_with_adj_time r
    JOIN rider rd ON r.bib_number = rd.bib_number
    WHERE r.stage_id = ?
    ORDER BY r.rank ASC
    LIMIT ?;
    """
    df = execute_query(q, (stage_id, top_n))
    if not df.empty:
        winner_adj = df.loc[0, "adj_time"]
        df["gap"] = df["adj_time"] - winner_adj
        df["time_formatted"] = df["adj_time"].apply(format_seconds)
        df["gap_formatted"] = df["gap"].apply(format_gap)
    return df

def get_stage_team_perspective(stage_id: int, top_n: int = 10) -> pd.DataFrame:
    """Returns teams populating the top-N finishers on that stage."""
    q = """
    WITH top_finishers AS (
        SELECT 
            r.rank,
            r.bib_number,
            rd.rider_name,
            rd.team_name
        FROM result_with_adj_time r
        JOIN rider rd ON r.bib_number = rd.bib_number
        WHERE r.stage_id = ? AND r.rank <= ?
    )
    SELECT 
        team_name,
        COUNT(bib_number) AS top_finishers_count,
        MIN(rank) AS best_stage_rank,
        GROUP_CONCAT(rider_name || ' (P' || rank || ')', ', ') AS riders_in_top_n
    FROM top_finishers
    GROUP BY team_name
    ORDER BY top_finishers_count DESC, best_stage_rank ASC;
    """
    return execute_query(q, (stage_id, top_n))

# ==============================================================================
# E3. TEAM BURDEN AND CONTRIBUTION
# ==============================================================================

def get_team_summary() -> pd.DataFrame:
    """Computes aggregate team time and roster status."""
    q = """
    SELECT 
        t.team_name,
        t.country_code,
        COUNT(DISTINCT rd.bib_number) AS roster_count,
        SUM(CASE WHEN e.bib_number IS NULL THEN 1 ELSE 0 END) AS active_finishers,
        SUM(r.adj_time) AS total_aggregate_time,
        COUNT(r.stage_id) AS total_stage_results
    FROM team t
    JOIN rider rd ON t.team_name = rd.team_name
    LEFT JOIN exit e ON rd.bib_number = e.bib_number
    JOIN result_with_adj_time r ON rd.bib_number = r.bib_number
    GROUP BY t.team_name
    ORDER BY total_aggregate_time ASC;
    """
    df = execute_query(q)
    if not df.empty:
        best_time = df.loc[0, "total_aggregate_time"]
        df["time_formatted"] = df["total_aggregate_time"].apply(format_seconds)
        df["gap_to_lead_team"] = (df["total_aggregate_time"] - best_time).apply(format_gap)
    return df

def get_team_rider_contributions(team_name: str) -> pd.DataFrame:
    """Rider burden breakdown within a team."""
    q = """
    WITH team_totals AS (
        SELECT SUM(r.adj_time) AS team_total_time
        FROM result_with_adj_time r
        JOIN rider rd ON r.bib_number = rd.bib_number
        WHERE rd.team_name = ?
    )
    SELECT 
        rd.bib_number,
        rd.rider_name,
        rd.role,
        rd.is_leader,
        COUNT(r.stage_id) AS stages_completed,
        SUM(r.adj_time) AS rider_total_adj_time,
        ROUND(SUM(r.adj_time) * 100.0 / (SELECT team_total_time FROM team_totals), 2) AS pct_team_burden,
        ROUND(AVG(r.rank), 1) AS avg_stage_rank,
        MIN(r.rank) AS best_stage_rank,
        CASE WHEN e.bib_number IS NOT NULL THEN 'Exited (Stage ' || e.stage_id || ' - ' || e.reason || ')' ELSE 'Completed' END AS status
    FROM rider rd
    JOIN result_with_adj_time r ON rd.bib_number = r.bib_number
    LEFT JOIN exit e ON rd.bib_number = e.bib_number
    WHERE rd.team_name = ?
    GROUP BY rd.bib_number
    ORDER BY rider_total_adj_time ASC;
    """
    df = execute_query(q, (team_name, team_name))
    if not df.empty:
        df["time_formatted"] = df["rider_total_adj_time"].apply(format_seconds)
    return df

# ==============================================================================
# E4. PARALLEL CLASSIFICATIONS
# ==============================================================================

def get_parallel_classifications() -> pd.DataFrame:
    """Side-by-side GC rank, Young Rider GC rank, and Mountain Stage GC Proxy."""
    q = """
    WITH finisher_counts AS (
        SELECT bib_number, COUNT(stage_id) AS cnt
        FROM result_with_adj_time
        GROUP BY bib_number
        HAVING cnt = 21
    ),
    overall_gc AS (
        SELECT 
            r.bib_number,
            rd.rider_name,
            rd.team_name,
            rd.country_code,
            rd.dob,
            SUM(r.adj_time) AS total_adj_time,
            RANK() OVER (ORDER BY SUM(r.adj_time) ASC) AS gc_rank
        FROM result_with_adj_time r
        JOIN rider rd ON r.bib_number = rd.bib_number
        JOIN finisher_counts fc ON r.bib_number = fc.bib_number
        GROUP BY r.bib_number
    ),
    young_rider_gc AS (
        SELECT 
            bib_number,
            RANK() OVER (ORDER BY total_adj_time ASC) AS young_rank
        FROM overall_gc
        WHERE dob >= '2000-01-01'
    ),
    mountain_proxy AS (
        SELECT 
            r.bib_number,
            SUM(r.adj_time) AS mtn_adj_time,
            RANK() OVER (ORDER BY SUM(r.adj_time) ASC) AS mtn_proxy_rank
        FROM result_with_adj_time r
        JOIN stage s ON r.stage_id = s.stage_id
        JOIN finisher_counts fc ON r.bib_number = fc.bib_number
        WHERE s.stage_type = 'mountain'
        GROUP BY r.bib_number
    )
    SELECT 
        o.gc_rank,
        o.bib_number,
        o.rider_name,
        o.team_name,
        o.country_code,
        o.dob,
        o.total_adj_time,
        y.young_rank,
        m.mtn_proxy_rank,
        (o.gc_rank - m.mtn_proxy_rank) AS mtn_gc_divergence
    FROM overall_gc o
    LEFT JOIN young_rider_gc y ON o.bib_number = y.bib_number
    LEFT JOIN mountain_proxy m ON o.bib_number = m.bib_number
    ORDER BY o.gc_rank ASC;
    """
    df = execute_query(q)
    if not df.empty:
        df["total_time_formatted"] = df["total_adj_time"].apply(format_seconds)
    return df

# ==============================================================================
# E5. MOUNTAIN CONTOURS
# ==============================================================================

def get_mountain_contours() -> pd.DataFrame:
    """Podium frequency and mean time gap to stage winner on mountain stages."""
    q = """
    WITH mountain_stages AS (
        SELECT stage_id FROM stage WHERE stage_type = 'mountain'
    ),
    stage_winners AS (
        SELECT stage_id, MIN(adj_time) AS winner_time
        FROM result_with_adj_time
        WHERE stage_id IN (SELECT stage_id FROM mountain_stages)
        GROUP BY stage_id
    ),
    mountain_results AS (
        SELECT 
            r.bib_number,
            r.stage_id,
            r.rank,
            r.adj_time,
            (r.adj_time - sw.winner_time) AS gap_to_winner,
            CASE WHEN r.rank <= 3 THEN 1 ELSE 0 END AS is_podium
        FROM result_with_adj_time r
        JOIN stage_winners sw ON r.stage_id = sw.stage_id
        WHERE r.stage_id IN (SELECT stage_id FROM mountain_stages)
    )
    SELECT 
        mr.bib_number,
        rd.rider_name,
        rd.team_name,
        COUNT(mr.stage_id) AS mountain_stages_completed,
        SUM(mr.is_podium) AS mountain_podium_count,
        ROUND(AVG(mr.gap_to_winner), 1) AS mean_gap_to_winner_seconds,
        MIN(mr.rank) AS best_mountain_rank
    FROM mountain_results mr
    JOIN rider rd ON mr.bib_number = rd.bib_number
    GROUP BY mr.bib_number
    ORDER BY mountain_podium_count DESC, mean_gap_to_winner_seconds ASC;
    """
    df = execute_query(q)
    if not df.empty:
        df["mean_gap_formatted"] = df["mean_gap_to_winner_seconds"].apply(format_gap)
    return df

def get_rider_mountain_traces(bib_number: int) -> pd.DataFrame:
    """Daily mountain traces for a specific rider."""
    q = """
    WITH stage_winners AS (
        SELECT stage_id, MIN(adj_time) AS winner_time
        FROM result_with_adj_time
        GROUP BY stage_id
    )
    SELECT 
        s.stage_id,
        s.stage_date,
        s.distance_km,
        s.start_location,
        s.finish_location,
        r.rank,
        r.adj_time,
        sw.winner_time,
        (r.adj_time - sw.winner_time) AS gap_to_stage_winner
    FROM result_with_adj_time r
    JOIN stage s ON r.stage_id = s.stage_id
    JOIN stage_winners sw ON r.stage_id = sw.stage_id
    WHERE r.bib_number = ? AND s.stage_type = 'mountain'
    ORDER BY s.stage_id ASC;
    """
    df = execute_query(q, (bib_number,))
    if not df.empty:
        df["adj_time_formatted"] = df["adj_time"].apply(format_seconds)
        df["gap_formatted"] = df["gap_to_stage_winner"].apply(format_gap)
    return df

# ==============================================================================
# E6. SPEED AS A SIMPLE RATIO
# ==============================================================================

def get_speed_by_stage_type() -> pd.DataFrame:
    """Computes proxy speed length / time across stage types for riders and teams."""
    q = """
    SELECT 
        r.bib_number,
        rd.rider_name,
        rd.team_name,
        s.stage_type,
        ROUND(SUM(s.distance_km) * 3600.0 / SUM(r.finish_time), 2) AS avg_speed_kmh
    FROM result r
    JOIN stage s ON r.stage_id = s.stage_id
    JOIN rider rd ON r.bib_number = rd.bib_number
    GROUP BY r.bib_number, s.stage_type;
    """
    return execute_query(q)

def get_team_speed_profile() -> pd.DataFrame:
    """Average speed by team across stage types."""
    q = """
    SELECT 
        rd.team_name,
        s.stage_type,
        ROUND(SUM(s.distance_km) * 3600.0 / SUM(r.finish_time), 2) AS avg_speed_kmh
    FROM result r
    JOIN stage s ON r.stage_id = s.stage_id
    JOIN rider rd ON r.bib_number = rd.bib_number
    GROUP BY rd.team_name, s.stage_type;
    """
    return execute_query(q)

# ==============================================================================
# E7. BONUSES, PENALTIES, AND COUNTERFACTUALS
# ==============================================================================

def get_counterfactual_gc(up_to_stage: int = 21) -> pd.DataFrame:
    """Compares Actual GC vs No-Bonuses vs No-Penalties vs Raw Time."""
    q = """
    WITH stage_filter AS (
        SELECT 
            r.bib_number,
            rd.rider_name,
            rd.team_name,
            COUNT(r.stage_id) AS stages_completed,
            SUM(r.finish_time) AS raw_time,
            SUM(r.bonus) AS total_bonus,
            SUM(r.penalty) AS total_penalty,
            SUM(r.finish_time - r.bonus + r.penalty) AS actual_adj_time,
            SUM(r.finish_time + r.penalty) AS no_bonus_time,
            SUM(r.finish_time - r.bonus) AS no_penalty_time
        FROM result r
        JOIN rider rd ON r.bib_number = rd.bib_number
        WHERE r.stage_id <= ?
        GROUP BY r.bib_number
        HAVING stages_completed = ?
    )
    SELECT 
        bib_number,
        rider_name,
        team_name,
        total_bonus,
        total_penalty,
        actual_adj_time,
        RANK() OVER (ORDER BY actual_adj_time ASC) AS actual_rank,
        no_bonus_time,
        RANK() OVER (ORDER BY no_bonus_time ASC) AS no_bonus_rank,
        no_penalty_time,
        RANK() OVER (ORDER BY no_penalty_time ASC) AS no_penalty_rank,
        raw_time,
        RANK() OVER (ORDER BY raw_time ASC) AS raw_rank
    FROM stage_filter
    ORDER BY actual_rank ASC;
    """
    df = execute_query(q, (up_to_stage, up_to_stage))
    if not df.empty:
        df["shift_no_bonus"] = df["actual_rank"] - df["no_bonus_rank"]
        df["shift_no_penalty"] = df["actual_rank"] - df["no_penalty_rank"]
        df["shift_raw"] = df["actual_rank"] - df["raw_rank"]
        df["actual_time_formatted"] = df["actual_adj_time"].apply(format_seconds)
        df["no_bonus_time_formatted"] = df["no_bonus_time"].apply(format_seconds)
    return df

# ==============================================================================
# E8. PARTICIPATION BY NATION
# ==============================================================================

def get_nation_participation() -> pd.DataFrame:
    """Summarizes nations by count of teams and count of riders."""
    q = """
    WITH rider_counts AS (
        SELECT country_code, COUNT(bib_number) AS rider_count
        FROM rider
        GROUP BY country_code
    ),
    team_counts AS (
        SELECT country_code, COUNT(team_name) AS team_count
        FROM team
        GROUP BY country_code
    )
    SELECT 
        c.country_code,
        c.country_name,
        COALESCE(tc.team_count, 0) AS team_count,
        COALESCE(rc.rider_count, 0) AS rider_count,
        ROUND(COALESCE(rc.rider_count, 0) * 100.0 / 184.0, 1) AS pct_peloton
    FROM country c
    LEFT JOIN team_counts tc ON c.country_code = tc.country_code
    LEFT JOIN rider_counts rc ON c.country_code = rc.country_code
    WHERE COALESCE(tc.team_count, 0) > 0 OR COALESCE(rc.rider_count, 0) > 0
    ORDER BY rider_count DESC, team_count DESC, c.country_name ASC;
    """
    return execute_query(q)

def get_nation_riders(country_code: str) -> pd.DataFrame:
    """Full rider list and squads for a chosen country."""
    q = """
    SELECT 
        rd.bib_number,
        rd.rider_name,
        rd.dob,
        rd.role,
        rd.is_leader,
        rd.team_name,
        CASE WHEN e.bib_number IS NOT NULL THEN 'Exited Stage ' || e.stage_id || ' (' || e.reason || ')' ELSE 'Active / Finished' END AS status
    FROM rider rd
    LEFT JOIN exit e ON rd.bib_number = e.bib_number
    WHERE rd.country_code = ?
    ORDER BY rd.bib_number ASC;
    """
    return execute_query(q, (country_code,))

# ==============================================================================
# E9. NATIONAL OUTCOMES
# ==============================================================================

def get_national_outcomes() -> pd.DataFrame:
    """Best GC rank, stage wins, and podiums for each nation."""
    q = """
    WITH finisher_counts AS (
        SELECT bib_number, COUNT(stage_id) AS cnt
        FROM result_with_adj_time
        GROUP BY bib_number
        HAVING cnt = 21
    ),
    rider_final_gc AS (
        SELECT 
            r.bib_number,
            rd.country_code,
            RANK() OVER (ORDER BY SUM(r.adj_time) ASC) AS gc_rank
        FROM result_with_adj_time r
        JOIN rider rd ON r.bib_number = rd.bib_number
        JOIN finisher_counts fc ON r.bib_number = fc.bib_number
        GROUP BY r.bib_number
    ),
    nation_best_gc AS (
        SELECT country_code, MIN(gc_rank) AS best_gc_rank
        FROM rider_final_gc
        GROUP BY country_code
    ),
    stage_wins_podiums AS (
        SELECT 
            rd.country_code,
            SUM(CASE WHEN r.rank = 1 THEN 1 ELSE 0 END) AS stage_wins,
            SUM(CASE WHEN r.rank <= 3 THEN 1 ELSE 0 END) AS stage_podiums,
            SUM(CASE WHEN r.rank <= 10 THEN 1 ELSE 0 END) AS stage_top10s
        FROM result_with_adj_time r
        JOIN rider rd ON r.bib_number = rd.bib_number
        GROUP BY rd.country_code
    )
    SELECT 
        c.country_code,
        c.country_name,
        COALESCE(nb.best_gc_rank, 999) AS best_gc_rank,
        COALESCE(swp.stage_wins, 0) AS stage_wins,
        COALESCE(swp.stage_podiums, 0) AS stage_podiums,
        COALESCE(swp.stage_top10s, 0) AS stage_top10s
    FROM country c
    JOIN (
        SELECT DISTINCT country_code FROM rider
    ) rc ON c.country_code = rc.country_code
    LEFT JOIN nation_best_gc nb ON c.country_code = nb.country_code
    LEFT JOIN stage_wins_podiums swp ON c.country_code = swp.country_code
    ORDER BY stage_wins DESC, stage_podiums DESC, best_gc_rank ASC;
    """
    df = execute_query(q)
    df["best_gc_rank_str"] = df["best_gc_rank"].apply(lambda x: str(int(x)) if x < 999 else "No 21-stage finisher")
    return df

# ==============================================================================
# E10. TEMPORAL GC STORYLINE
# ==============================================================================

def get_temporal_gc_storyline(bib_list: list = None) -> pd.DataFrame:
    """Progressive cumulative time and GC rank stage-by-stage."""
    q = """
    WITH cum_results AS (
        SELECT 
            r.stage_id,
            r.bib_number,
            SUM(r.adj_time) OVER (PARTITION BY r.bib_number ORDER BY r.stage_id) AS cum_time
        FROM result_with_adj_time r
    ),
    stage_leaders AS (
        SELECT stage_id, MIN(cum_time) AS leader_cum_time
        FROM cum_results
        GROUP BY stage_id
    )
    SELECT 
        c.stage_id,
        s.stage_type,
        s.distance_km,
        c.bib_number,
        rd.rider_name,
        rd.team_name,
        c.cum_time,
        (c.cum_time - l.leader_cum_time) AS gap_to_leader,
        RANK() OVER (PARTITION BY c.stage_id ORDER BY c.cum_time ASC) AS gc_rank
    FROM cum_results c
    JOIN stage_leaders l ON c.stage_id = l.stage_id
    JOIN rider rd ON c.bib_number = rd.bib_number
    JOIN stage s ON c.stage_id = s.stage_id
    ORDER BY c.stage_id ASC, gc_rank ASC;
    """
    df = execute_query(q)
    if bib_list:
        df = df[df["bib_number"].isin(bib_list)]
    return df

# ==============================================================================
# E11. AGAINST THE CLOCK (ITT CATALOGUE)
# ==============================================================================

def get_itt_catalogue() -> pd.DataFrame:
    """Compact catalogue of ITT stages, essentials, and winners."""
    q = """
    WITH itt_stages AS (
        SELECT * FROM stage WHERE stage_type = 'individual time-trial'
    ),
    itt_winners AS (
        SELECT 
            r.stage_id,
            r.bib_number,
            rd.rider_name,
            rd.team_name,
            r.adj_time,
            ROUND(s.distance_km * 3600.0 / r.finish_time, 2) AS winner_speed_kmh
        FROM result_with_adj_time r
        JOIN rider rd ON r.bib_number = rd.bib_number
        JOIN stage s ON r.stage_id = s.stage_id
        WHERE r.rank = 1 AND s.stage_type = 'individual time-trial'
    )
    SELECT 
        i.stage_id,
        i.stage_date,
        i.distance_km,
        i.start_location,
        i.finish_location,
        w.rider_name AS winner_name,
        w.team_name AS winner_team,
        w.adj_time AS winning_time,
        w.winner_speed_kmh
    FROM itt_stages i
    JOIN itt_winners w ON i.stage_id = w.stage_id
    ORDER BY i.stage_id ASC;
    """
    df = execute_query(q)
    if not df.empty:
        df["winning_time_formatted"] = df["winning_time"].apply(format_seconds)
    return df

# ==============================================================================
# E12. CONSISTENCY NEAR THE FRONT
# ==============================================================================

def get_consistency_ranking(top_n: int = 15) -> pd.DataFrame:
    """Riders who most often appear in the top 10."""
    q = """
    SELECT 
        r.bib_number,
        rd.rider_name,
        rd.team_name,
        rd.country_code,
        COUNT(r.stage_id) AS top10_finishes_count,
        ROUND(AVG(r.rank), 1) AS avg_rank_in_top10,
        MIN(r.rank) AS best_finish
    FROM result_with_adj_time r
    JOIN rider rd ON r.bib_number = rd.bib_number
    WHERE r.rank <= 10
    GROUP BY r.bib_number
    ORDER BY top10_finishes_count DESC, avg_rank_in_top10 ASC
    LIMIT ?;
    """
    return execute_query(q, (top_n,))

def get_rider_contributing_stages(bib_number: int) -> pd.DataFrame:
    """Stages where a rider placed in top 10."""
    q = """
    SELECT 
        s.stage_id,
        s.stage_date,
        s.stage_type,
        s.distance_km,
        s.start_location || ' → ' || s.finish_location AS route,
        r.rank,
        r.adj_time
    FROM result_with_adj_time r
    JOIN stage s ON r.stage_id = s.stage_id
    WHERE r.bib_number = ? AND r.rank <= 10
    ORDER BY s.stage_id ASC;
    """
    df = execute_query(q, (bib_number,))
    if not df.empty:
        df["adj_time_formatted"] = df["adj_time"].apply(format_seconds)
    return df

# ==============================================================================
# E13. DEPTH OF SQUADS
# ==============================================================================

def get_squad_depth() -> pd.DataFrame:
    """Portrays team depth via distinct rider counts and survival."""
    q = """
    SELECT 
        t.team_name,
        t.country_code,
        COUNT(DISTINCT rd.bib_number) AS starting_riders,
        SUM(CASE WHEN e.bib_number IS NULL THEN 1 ELSE 0 END) AS active_finishers,
        SUM(CASE WHEN e.bib_number IS NOT NULL THEN 1 ELSE 0 END) AS exit_count,
        ROUND(SUM(CASE WHEN e.bib_number IS NULL THEN 1.0 ELSE 0.0 END) * 100.0 / COUNT(DISTINCT rd.bib_number), 1) AS survival_rate_pct
    FROM team t
    JOIN rider rd ON t.team_name = rd.team_name
    LEFT JOIN exit e ON rd.bib_number = e.bib_number
    GROUP BY t.team_name
    ORDER BY active_finishers DESC, survival_rate_pct DESC, t.team_name ASC;
    """
    return execute_query(q)

def get_team_roster(team_name: str) -> pd.DataFrame:
    """Full squad roster for a team."""
    q = """
    SELECT 
        rd.bib_number,
        rd.rider_name,
        rd.dob,
        rd.country_code,
        rd.role,
        rd.is_leader,
        CASE WHEN e.bib_number IS NOT NULL THEN 'Exit Stage ' || e.stage_id || ' (' || e.reason || ')' ELSE 'Active / Completed' END AS status
    FROM rider rd
    LEFT JOIN exit e ON rd.bib_number = e.bib_number
    WHERE rd.team_name = ?
    ORDER BY rd.bib_number ASC;
    """
    return execute_query(q, (team_name,))

# ==============================================================================
# E14. TOP-TEN INTENSITY BY TEAM
# ==============================================================================

def get_team_top10_intensity() -> pd.DataFrame:
    """Aggregates top-ten presences at the team level broken down by stage type."""
    q = """
    SELECT 
        rd.team_name,
        SUM(CASE WHEN s.stage_type = 'flat' THEN 1 ELSE 0 END) AS flat_top10,
        SUM(CASE WHEN s.stage_type = 'hilly' THEN 1 ELSE 0 END) AS hilly_top10,
        SUM(CASE WHEN s.stage_type = 'mountain' THEN 1 ELSE 0 END) AS mountain_top10,
        SUM(CASE WHEN s.stage_type = 'individual time-trial' THEN 1 ELSE 0 END) AS itt_top10,
        COUNT(r.stage_id) AS total_top10_presences
    FROM result_with_adj_time r
    JOIN stage s ON r.stage_id = s.stage_id
    JOIN rider rd ON r.bib_number = rd.bib_number
    WHERE r.rank <= 10
    GROUP BY rd.team_name
    ORDER BY total_top10_presences DESC;
    """
    return execute_query(q)

def get_team_top10_drilldown(team_name: str) -> pd.DataFrame:
    """Specific top-10 stage finishes for a chosen team."""
    q = """
    SELECT 
        s.stage_id,
        s.stage_date,
        s.stage_type,
        r.rank,
        rd.bib_number,
        rd.rider_name
    FROM result_with_adj_time r
    JOIN stage s ON r.stage_id = s.stage_id
    JOIN rider rd ON r.bib_number = rd.bib_number
    WHERE rd.team_name = ? AND r.rank <= 10
    ORDER BY s.stage_id ASC, r.rank ASC;
    """
    return execute_query(q, (team_name,))

# ==============================================================================
# E15. THE LONG DAY
# ==============================================================================

def get_stages_by_distance() -> pd.DataFrame:
    """All stages sorted by distance in descending order."""
    q = """
    SELECT 
        stage_id,
        stage_date,
        distance_km,
        stage_type,
        start_location,
        finish_location
    FROM stage
    ORDER BY distance_km DESC;
    """
    return execute_query(q)
