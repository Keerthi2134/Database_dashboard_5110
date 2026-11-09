"""
Tour de France Analytics System - Interactive OLAP Dashboard
BT5110: Data Management & Warehousing (Group 39)
Authors: James Sharon Susan, Keerthivasan Radhakrishnan, Louise, Sulistyo Agung Wibowo
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import time
from db import execute_query, format_seconds, format_gap
import olap

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Tour de France Analytics | BT5110 Group 39",
    page_icon="🚴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# CUSTOM CSS STYLING
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Main container styling */
    .main-header {
        background: linear-gradient(135deg, #0e1b2a 0%, #1a2f4c 100%);
        color: #ffffff;
        padding: 24px 30px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        border-left: 8px solid #ffcc00;
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0 0 6px 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #cfd8dc;
        font-size: 1.05rem;
        margin: 0;
    }
    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 6px;
        margin-top: 8px;
    }
    .badge-yellow { background-color: #ffcc00; color: #111; }
    .badge-blue { background-color: #1976d2; color: #fff; }
    .badge-green { background-color: #2e7d32; color: #fff; }
    .badge-red { background-color: #c62828; color: #fff; }
    .badge-purple { background-color: #6a1b9a; color: #fff; }

    /* Metric card styling */
    .metric-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 18px 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 12px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(0,0,0,0.08);
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 1.7rem;
        font-weight: 800;
        color: #0f172a;
        margin: 4px 0;
    }
    .metric-sub {
        font-size: 0.85rem;
        color: #475569;
    }

    /* Narrative Alert Card */
    .narrative-box {
        background: #f8fafc;
        border-left: 5px solid #2563eb;
        border-radius: 6px;
        padding: 16px 20px;
        margin: 15px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .narrative-box h4 {
        margin: 0 0 6px 0;
        color: #1e3a8a;
        font-weight: 700;
        font-size: 1.05rem;
    }
    .narrative-box p {
        margin: 0;
        color: #334155;
        font-size: 0.95rem;
        line-height: 1.5;
    }

    /* Stage Pill */
    .stage-pill {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .stage-flat { background-color: #dcfce7; color: #166534; }
    .stage-hilly { background-color: #fef9c3; color: #854d0e; }
    .stage-mountain { background-color: #fee2e2; color: #991b1b; }
    .stage-itt { background-color: #e0e7ff; color: #3730a3; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/e/eb/Tour_de_France_logo.svg/300px-Tour_de_France_logo.svg.png", width=110)
    st.title("Tour de France OLAP")
    st.caption("BT5110 Data Management & Warehousing")
    st.markdown("**Group 39:**")
    st.caption("• James Sharon Susan\n• Keerthivasan Radhakrishnan\n• Louise\n• Sulistyo Agung Wibowo")
    st.markdown("---")

    menu = st.radio(
        "Navigation",
        [
            "📊 Race Overview & Awards",
            "🏆 GC & Storylines (E1, E4, E7, E10)",
            "🏔️ Stages & Terrain (E2, E5, E6, E11, E15)",
            "👥 Teams & Squads (E3, E13, E14)",
            "🌍 Nations & Consistency (E8, E9, E12)",
            "🗄️ SQL Studio & Schema"
        ],
        index=0
    )

    st.markdown("---")
    st.info("💡 **Dataset Stats**\n\n• **21** Stages (3,492 km)\n• **184** Riders across **23** Teams\n• **30** Nations Represented\n• **3,602** Stage Results\n• **160** Final Finishers")

# -----------------------------------------------------------------------------
# HEADER BANNER
# -----------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🚴 Tour de France Analytical & OLAP Dashboard</h1>
    <p>Comprehensive Multidimensional Analytics, Relational Warehousing, and Stage-Grain Narratives</p>
    <div>
        <span class="badge-pill badge-yellow">Maillot Jaune: T. Pogacar</span>
        <span class="badge-pill badge-blue">Database: SQLite (tdf.db)</span>
        <span class="badge-pill badge-green">3,602 Results</span>
        <span class="badge-pill badge-purple">15 OLAP Prompts Covered</span>
    </div>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# MODULE 1: RACE OVERVIEW & AWARDS
# =============================================================================
if menu == "📊 Race Overview & Awards":
    st.header("Executive Summary & Classification Jerseys")

    # High-level Metrics Row
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Total Stages</div>
            <div class="metric-value">21</div>
            <div class="metric-sub">3,492.2 Total Km</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Rosters & Teams</div>
            <div class="metric-value">184 / 23</div>
            <div class="metric-sub">8 Riders per Squad</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Final Finishers</div>
            <div class="metric-value">160</div>
            <div class="metric-sub">87.0% Survival Rate (24 Exits)</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Participating Nations</div>
            <div class="metric-value">30</div>
            <div class="metric-sub">Global Representation</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Winning GC Time</div>
            <div class="metric-value">77h 02m</div>
            <div class="metric-sub">Avg Speed: 45.3 km/h</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Official Classification Winners & Honours")
    j1, j2, j3, j4 = st.columns(4)
    with j1:
        st.markdown("""
        <div style="background: #fffbeb; border: 2px solid #fde047; border-radius: 10px; padding: 18px; text-align: center;">
            <span style="font-size: 2.2rem;">💛</span>
            <h4 style="margin: 8px 0 2px 0; color: #854d0e;">Maillot Jaune</h4>
            <div style="font-size: 0.85rem; color: #a16207; font-weight: 600;">General Classification</div>
            <div style="font-size: 1.25rem; font-weight: 800; color: #1e293b; margin-top: 6px;">Tadej Pogacar</div>
            <div style="font-size: 0.85rem; color: #64748b;">UAE TEAM EMIRATES XRG</div>
            <div style="margin-top: 8px; font-weight: 700; color: #b45309;">77h 02m 29s</div>
        </div>
        """, unsafe_allow_html=True)

    with j2:
        st.markdown("""
        <div style="background: #f8fafc; border: 2px solid #cbd5e1; border-radius: 10px; padding: 18px; text-align: center;">
            <span style="font-size: 2.2rem;">🤍</span>
            <h4 style="margin: 8px 0 2px 0; color: #475569;">Maillot Blanc</h4>
            <div style="font-size: 0.85rem; color: #64748b; font-weight: 600;">Best Young Rider (≤ 25 yrs)</div>
            <div style="font-size: 1.25rem; font-weight: 800; color: #1e293b; margin-top: 6px;">Florian Lipowitz</div>
            <div style="font-size: 0.85rem; color: #64748b;">RED BULL - BORA - HANSGROHE</div>
            <div style="margin-top: 8px; font-weight: 700; color: #334155;">77h 13m 29s (+11m 00s)</div>
        </div>
        """, unsafe_allow_html=True)

    with j3:
        st.markdown("""
        <div style="background: #f0fdf4; border: 2px solid #86efac; border-radius: 10px; padding: 18px; text-align: center;">
            <span style="font-size: 2.2rem;">💚</span>
            <h4 style="margin: 8px 0 2px 0; color: #166534;">Maillot Vert</h4>
            <div style="font-size: 0.85rem; color: #15803d; font-weight: 600;">Points Classification</div>
            <div style="font-size: 1.25rem; font-weight: 800; color: #1e293b; margin-top: 6px;">Jonathan Milan</div>
            <div style="font-size: 0.85rem; color: #64748b;">LIDL-TREK</div>
            <div style="margin-top: 8px; font-weight: 700; color: #166534;">2 Stage Wins & Consistent Podium</div>
        </div>
        """, unsafe_allow_html=True)

    with j4:
        st.markdown("""
        <div style="background: #fef2f2; border: 2px solid #fca5a5; border-radius: 10px; padding: 18px; text-align: center;">
            <span style="font-size: 2.2rem;">🔴</span>
            <h4 style="margin: 8px 0 2px 0; color: #991b1b;">Maillot à Pois</h4>
            <div style="font-size: 0.85rem; color: #b91c1c; font-weight: 600;">King of the Mountains</div>
            <div style="font-size: 1.25rem; font-weight: 800; color: #1e293b; margin-top: 6px;">Tadej Pogacar</div>
            <div style="font-size: 0.85rem; color: #64748b;">UAE TEAM EMIRATES XRG</div>
            <div style="margin-top: 8px; font-weight: 700; color: #991b1b;">5 Mountain Podiums (2 Wins)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Secondary Honours Row
    h1, h2 = st.columns(2)
    with h1:
        st.markdown("""
        <div class="narrative-box" style="border-left-color: #0284c7;">
            <h4>🏆 Best Team Classification (Classement par Équipes)</h4>
            <p><strong>Winner:</strong> TEAM VISMA | LEASE A BIKE (Aggregate time of 835,226s across top 3 daily finishers). Squad demonstrated supreme collective depth, placing Jonas Vingegaard (2nd GC) and Wout Van Aert (Stage 21 Paris winner).</p>
        </div>
        """, unsafe_allow_html=True)
    with h2:
        st.markdown("""
        <div class="narrative-box" style="border-left-color: #e11d48;">
            <h4>🎖️ Super Combativity Award (Prix de la Combativité)</h4>
            <p><strong>Winner:</strong> Ben Healy (EF EDUCATION - EASYPOST, Bib 31). Winner of Stage 6 in Vire Normandie with multiple relentless long-range solo breakaways across both the Massif Central and Pyrenees.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Race Itinerary & 21 Stages Inventory")
    stages_df = execute_query("""
        SELECT 
            stage_id,
            stage_date,
            stage_type,
            distance_km,
            start_location,
            finish_location
        FROM stage
        ORDER BY stage_id ASC;
    """)
    st.dataframe(
        stages_df,
        column_config={
            "stage_id": st.column_config.NumberColumn("Stage #", format="%d"),
            "stage_date": "Date",
            "stage_type": "Terrain Type",
            "distance_km": st.column_config.NumberColumn("Distance (km)", format="%.1f km"),
            "start_location": "Origin",
            "finish_location": "Destination"
        },
        hide_index=True,
        use_container_width=True
    )


# =============================================================================
# MODULE 2: GC & STORYLINES (E1, E4, E7, E10)
# =============================================================================
elif menu == "🏆 GC & Storylines (E1, E4, E7, E10)":
    tab1, tab2, tab3, tab4 = st.tabs([
        "E1: GC Leaderboard & Contextual Descent",
        "E4: Parallel Classifications & Proxies",
        "E7: Counterfactuals & Time Adjustments",
        "E10: Temporal GC Storyline & Inflections"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: E1 (Category A: Chart-First)
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("E1. General Classification Leaderboard with Contextual Descent")
        st.markdown("""
        Compare GC contenders by cumulative adjusted time gap to the leader, then select any contender 
        to trace their stage-grain trajectory and isolate the **single pivotal day** that reshaped their Tour.
        """)

        gc_df = olap.get_gc_leaderboard(21)

        # Interactive Controls
        col_ctrl1, col_ctrl2 = st.columns([2, 1])
        with col_ctrl1:
            team_filter = st.multiselect("Filter by Team:", options=sorted(gc_df["team_name"].unique()), default=[])
        with col_ctrl2:
            top_n = st.slider("Display Top N Riders:", min_value=5, max_value=50, value=15, step=5)

        filtered_gc = gc_df.copy()
        if team_filter:
            filtered_gc = filtered_gc[filtered_gc["team_name"].isin(team_filter)]

        chart_gc = filtered_gc.head(top_n).copy()

        # Primary Visualization 1: Horizontal Gap-to-Leader Bar Chart
        st.markdown("#### 📊 General Classification: Time Gap to Leader")
        gap_bar = alt.Chart(chart_gc).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
            y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="gc_rank", order="ascending"), title="Contender (by GC Rank)"),
            x=alt.X("gap_to_leader:Q", title="Time Gap to GC Leader (Seconds)"),
            color=alt.condition(
                alt.datum.gap_to_leader == 0,
                alt.value("#eab308"),  # Yellow Jersey Leader
                alt.value("#2563eb")   # Blue Contenders
            ),
            tooltip=[
                alt.Tooltip("gc_rank:Q", title="GC Rank"),
                alt.Tooltip("rider_name:N", title="Rider"),
                alt.Tooltip("team_name:N", title="Team"),
                alt.Tooltip("country_code:N", title="Nat"),
                alt.Tooltip("time_formatted:N", title="Cumulative Time"),
                alt.Tooltip("gap_formatted:N", title="Gap to Leader"),
                alt.Tooltip("total_bonus:Q", title="Total Bonus (s)"),
                alt.Tooltip("total_penalty:Q", title="Total Penalty (s)")
            ]
        ).properties(height=max(260, len(chart_gc) * 22))

        gap_labels = alt.Chart(chart_gc).mark_text(
            align="left", baseline="middle", dx=6, fontSize=11, color="#334155"
        ).encode(
            y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="gc_rank", order="ascending")),
            x=alt.X("gap_to_leader:Q"),
            text=alt.Text("gap_formatted:N")
        )
        st.altair_chart(gap_bar + gap_labels, use_container_width=True)

        with st.expander("📋 View Full General Classification Leaderboard Table"):
            st.dataframe(
                filtered_gc.head(top_n)[[
                    "gc_rank", "bib_number", "rider_name", "team_name", "country_code", 
                    "time_formatted", "gap_formatted", "total_bonus", "total_penalty"
                ]],
                column_config={
                    "gc_rank": st.column_config.NumberColumn("GC Rank", format="%d"),
                    "bib_number": st.column_config.NumberColumn("Bib", format="%d"),
                    "rider_name": "Rider",
                    "team_name": "Team",
                    "country_code": "Nat",
                    "time_formatted": "Cumulative Time",
                    "gap_formatted": "Gap to Leader",
                    "total_bonus": st.column_config.NumberColumn("Bonus (s)", format="-%ds"),
                    "total_penalty": st.column_config.NumberColumn("Penalty (s)", format="+%ds")
                },
                hide_index=True,
                use_container_width=True
            )

        st.markdown("---")
        st.markdown("### 🔍 Contextual Descent: Stage Grain Drilldown")
        
        # Contender selector
        rider_options = {f"Bib {r['bib_number']} - {r['rider_name']} ({r['team_name']})": r["bib_number"] for _, r in gc_df.iterrows()}
        selected_label = st.selectbox("Choose a contender to inspect:", options=list(rider_options.keys()), index=0)
        selected_bib = rider_options[selected_label]

        # Stage Descent Data & Pivotal Moment
        descent_df = olap.get_rider_stage_descent(selected_bib)
        pivotal = olap.get_pivotal_moment(descent_df)

        if pivotal:
            st.markdown(f"""
            <div class="narrative-box" style="border-left-color: #f59e0b;">
                <h4>⚡ Pivotal Moment in Race: Stage {pivotal['stage_id']} ({pivotal['stage_type'].title()})</h4>
                <p><strong>Route:</strong> {pivotal['route']} ({pivotal['distance_km']} km) on {pivotal['stage_date']}<br>
                <strong>Daily Outcome:</strong> Finished P{pivotal['stage_rank']}. GC Rank moved from P{pivotal['gc_rank_after'] - pivotal['rank_change']} to P{pivotal['gc_rank_after']} (Net Rank Change: {pivotal['rank_change']:+d}).<br>
                <strong>Gap Impact:</strong> Gap to GC leader swung by <strong>{format_gap(pivotal['gap_change'])}</strong>.<br>
                <em>{pivotal['narrative']}</em></p>
            </div>
            """, unsafe_allow_html=True)

        # Primary Visualization 2: GC Rank Evolution Line Chart across 21 Stages
        st.markdown("#### 📈 Stage-by-Stage GC Rank Evolution")
        base_line = alt.Chart(descent_df).mark_line(point=True, color="#2563eb", strokeWidth=3).encode(
            x=alt.X("stage_id:O", title="Stage Number (1–21)"),
            y=alt.Y("gc_rank_stage:Q", title="Progressive GC Rank (Inverted)", scale=alt.Scale(reverse=True, zero=False)),
            tooltip=[
                alt.Tooltip("stage_id:O", title="Stage"),
                alt.Tooltip("stage_type:N", title="Terrain"),
                alt.Tooltip("distance_km:Q", title="Distance (km)"),
                alt.Tooltip("stage_rank:Q", title="Daily Finish"),
                alt.Tooltip("gc_rank_stage:Q", title="GC Rank After Stage"),
                alt.Tooltip("gap_formatted:N", title="Gap to Leader"),
                alt.Tooltip("rank_change:Q", title="Δ Rank"),
                alt.Tooltip("gap_change_formatted:N", title="Δ Gap")
            ]
        )

        if pivotal:
            piv_pt = alt.Chart(descent_df[descent_df["stage_id"] == pivotal["stage_id"]]).mark_point(
                size=220, color="#f59e0b", filled=True, shape="diamond"
            ).encode(
                x="stage_id:O",
                y="gc_rank_stage:Q",
                tooltip=[
                    alt.Tooltip("stage_id:O", title="Pivotal Stage"),
                    alt.Tooltip("stage_type:N", title="Terrain"),
                    alt.Tooltip("gap_change_formatted:N", title="Gap Swing")
                ]
            )
            stage_chart = (base_line + piv_pt).properties(title=f"GC Rank Trajectory - {selected_label} (Diamond = Pivotal Stage)", height=300)
        else:
            stage_chart = base_line.properties(title=f"GC Rank Trajectory - {selected_label}", height=300)

        st.altair_chart(stage_chart, use_container_width=True)

        with st.expander("📊 View Complete 21-Stage Daily Descent Table"):
            st.dataframe(
                descent_df[[
                    "stage_id", "stage_date", "stage_type", "distance_km", "start_location", "finish_location",
                    "stage_rank", "adj_time_formatted", "gap_formatted", "gc_rank_stage", "rank_change", "gap_change_formatted"
                ]],
                column_config={
                    "stage_id": st.column_config.NumberColumn("Stage", format="%d"),
                    "stage_date": "Date",
                    "stage_type": "Terrain",
                    "distance_km": st.column_config.NumberColumn("Km", format="%.1f"),
                    "start_location": "Start",
                    "finish_location": "Finish",
                    "stage_rank": st.column_config.NumberColumn("Stage Rank", format="%d"),
                    "adj_time_formatted": "Adjusted Time",
                    "gap_formatted": "Gap to Leader",
                    "gc_rank_stage": st.column_config.NumberColumn("GC Rank After Stage", format="%d"),
                    "rank_change": st.column_config.NumberColumn("Δ Rank", format="%+d"),
                    "gap_change_formatted": "Δ Gap"
                },
                hide_index=True,
                use_container_width=True
            )

    # -------------------------------------------------------------------------
    # TAB 2: E4 (Category A: Chart-First)
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("E4. Parallel Classifications & Mountain-Stage Proxy")
        st.markdown("""
        Compare side-by-side **Overall GC Rank**, **Young Rider GC Rank** (riders born $\ge$ 2000-01-01), 
        and **Mountain-Stage GC Proxy** (accumulating adjusted time only across the 6 high-mountain stages).
        """)

        parallel_df = olap.get_parallel_classifications()

        # Summary KPIs
        pk1, pk2, pk3 = st.columns(3)
        with pk1:
            st.metric("Total 21-Stage Finishers", len(parallel_df))
        with pk2:
            st.metric("Young Rider Contenders", len(parallel_df.dropna(subset=["young_rank"])))
        with pk3:
            st.metric("Mountain Stages Proxy Grain", "6 High Mountain Stages")

        col_p1, col_p2 = st.columns([2, 1])
        with col_p1:
            p_mode = st.radio(
                "Classification Focus:",
                ["Top Overall GC Contenders", "Young Rider Class (≤ 25 yrs)", "Highest Mountain-GC Divergence"],
                horizontal=True
            )
        with col_p2:
            p_top_n = st.slider("Display Riders:", min_value=10, max_value=35, value=15, step=5)

        # Prepare filtered subset for Dumbbell Plot
        sub_parallel = parallel_df.copy()
        if p_mode == "Young Rider Class (≤ 25 yrs)":
            sub_parallel = sub_parallel.dropna(subset=["young_rank"]).sort_values("young_rank").head(p_top_n)
        elif p_mode == "Highest Mountain-GC Divergence":
            sub_parallel["abs_div"] = sub_parallel["mtn_gc_divergence"].abs()
            sub_parallel = sub_parallel.sort_values("abs_div", ascending=False).head(p_top_n)
        else:
            sub_parallel = sub_parallel.sort_values("gc_rank").head(p_top_n)

        sub_parallel["min_rank"] = sub_parallel[["gc_rank", "mtn_proxy_rank"]].min(axis=1)
        sub_parallel["max_rank"] = sub_parallel[["gc_rank", "mtn_proxy_rank"]].max(axis=1)

        # Primary Visualization: Dumbbell / Connected Dot Plot
        st.markdown("#### 🏋️ Connected Dot Plot: Overall GC vs. Mountain Proxy vs. Young Rider")
        st.caption("Lines connect Overall GC Rank to Mountain Proxy Rank; dot spread visualizes terrain performance divergence.")

        rule_p = alt.Chart(sub_parallel).mark_rule(color="#94a3b8", strokeWidth=2).encode(
            y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="gc_rank", order="ascending"), title="Rider"),
            x=alt.X("min_rank:Q", title="Classification Rank (1 = Best)"),
            x2="max_rank:Q"
        )

        pts_gc = alt.Chart(sub_parallel).mark_circle(size=140, color="#eab308").encode(
            y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="gc_rank", order="ascending")),
            x=alt.X("gc_rank:Q"),
            tooltip=[
                alt.Tooltip("rider_name:N", title="Rider"),
                alt.Tooltip("team_name:N", title="Team"),
                alt.Tooltip("gc_rank:Q", title="Overall GC Rank"),
                alt.Tooltip("mtn_proxy_rank:Q", title="Mountain Proxy Rank"),
                alt.Tooltip("mtn_gc_divergence:Q", title="Divergence (GC - Mtn)"),
                alt.Tooltip("total_time_formatted:N", title="Total GC Time")
            ]
        )

        pts_mtn = alt.Chart(sub_parallel).mark_circle(size=140, color="#ef4444").encode(
            y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="gc_rank", order="ascending")),
            x=alt.X("mtn_proxy_rank:Q"),
            tooltip=[
                alt.Tooltip("rider_name:N", title="Rider"),
                alt.Tooltip("team_name:N", title="Team"),
                alt.Tooltip("gc_rank:Q", title="Overall GC Rank"),
                alt.Tooltip("mtn_proxy_rank:Q", title="Mountain Proxy Rank"),
                alt.Tooltip("mtn_gc_divergence:Q", title="Divergence (GC - Mtn)")
            ]
        )

        # Young rider points
        pts_young = alt.Chart(sub_parallel.dropna(subset=["young_rank"])).mark_point(
            size=120, shape="diamond", color="#6366f1", filled=True
        ).encode(
            y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="gc_rank", order="ascending")),
            x=alt.X("young_rank:Q"),
            tooltip=[
                alt.Tooltip("rider_name:N", title="Rider"),
                alt.Tooltip("young_rank:Q", title="Young Rider Rank")
            ]
        )

        dumbbell_chart = (rule_p + pts_gc + pts_mtn + pts_young).properties(height=max(320, len(sub_parallel) * 24))
        st.altair_chart(dumbbell_chart, use_container_width=True)

        st.markdown("""
        <div style="display: flex; gap: 24px; font-size: 0.85rem; color: #334155; margin-top: -8px; margin-bottom: 14px;">
            <span>🟡 <strong>Overall GC Rank</strong></span>
            <span>🔴 <strong>Mountain Proxy Rank</strong></span>
            <span>🔷 <strong>Young Rider Rank (≤ 25 yrs)</strong></span>
            <span>— <strong>Divergence Spread</strong></span>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("⛰️ Mountain Proxy Divergence Analysis & Scatter Plot"):
            st.markdown("""
            **Positive Divergence (+):** Pure climber whose mountain rank is higher than their overall GC (e.g. Lenny Martinez +36, Pablo Castrillo +31).  
            **Negative Divergence (−):** Flat / ITT specialist whose mountain rank drops relative to overall GC (e.g. Wout Van Aert −35, Matteo Trentin −30).
            """)
            scatter_chart = alt.Chart(parallel_df).mark_circle(size=80).encode(
                x=alt.X("gc_rank:Q", title="Overall GC Rank"),
                y=alt.Y("mtn_proxy_rank:Q", title="Mountain Proxy Rank"),
                color=alt.Color("mtn_gc_divergence:Q", scale=alt.Scale(scheme="redblue", domainMid=0), title="Divergence"),
                tooltip=["rider_name", "team_name", "gc_rank", "mtn_proxy_rank", "mtn_gc_divergence"]
            ).properties(title="GC Rank vs. Mountain Proxy Rank (Diagonal = Parity)", height=340)

            line_parity = alt.Chart(pd.DataFrame({'x': [1, 160], 'y': [1, 160]})).mark_line(color="gray", strokeDash=[4, 4]).encode(
                x='x:Q', y='y:Q'
            )
            st.altair_chart(scatter_chart + line_parity, use_container_width=True)

        with st.expander("📋 View Parallel Standings Data Table"):
            st.dataframe(
                parallel_df[[
                    "gc_rank", "young_rank", "mtn_proxy_rank", "mtn_gc_divergence", 
                    "bib_number", "rider_name", "team_name", "dob", "total_time_formatted"
                ]],
                column_config={
                    "gc_rank": st.column_config.NumberColumn("Overall GC Rank", format="%d"),
                    "young_rank": st.column_config.NumberColumn("Young Rider Rank", format="%d"),
                    "mtn_proxy_rank": st.column_config.NumberColumn("Mountain Proxy Rank", format="%d"),
                    "mtn_gc_divergence": st.column_config.NumberColumn("Divergence (GC - Mountain)", format="%+d"),
                    "bib_number": "Bib",
                    "rider_name": "Rider",
                    "team_name": "Team",
                    "dob": "Date of Birth",
                    "total_time_formatted": "Total GC Time"
                },
                hide_index=True,
                use_container_width=True
            )

    # -------------------------------------------------------------------------
    # TAB 3: E7 (Category A: Chart-First)
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("E7. Bonuses, Penalties, and Counterfactual GC Replay")
        st.markdown("""
        Replay the GC leaderboard under **counterfactual what-if scenarios** (removing stage/sprint bonuses, 
        removing disciplinary time penalties, or reverting strictly to raw elapsed time) to illuminate rank displacements.
        """)

        col_cf_ctrl1, col_cf_ctrl2 = st.columns([2, 1])
        with col_cf_ctrl1:
            cf_scenario = st.radio(
                "Counterfactual Scenario:",
                [
                    "No Bonuses (Sprint & Finish Bonuses Removed)",
                    "No Penalties (Time Penalties Removed)",
                    "Raw Elapsed Time (Both Bonuses & Penalties Removed)"
                ],
                horizontal=True
            )
        with col_cf_ctrl2:
            cf_stage = st.slider("Stage Grain for Replay:", min_value=1, max_value=21, value=5, step=1)

        cf_top_n = st.slider("Display Contenders in Slope Chart:", min_value=10, max_value=30, value=15, step=5)
        cf_df = olap.get_counterfactual_gc(cf_stage)

        # Determine target columns based on selection
        if cf_scenario.startswith("No Bonuses"):
            target_col = "no_bonus_rank"
            shift_col = "shift_no_bonus"
            scen_name = "No-Bonus GC"
        elif cf_scenario.startswith("No Penalties"):
            target_col = "no_penalty_rank"
            shift_col = "shift_no_penalty"
            scen_name = "No-Penalty GC"
        else:
            target_col = "raw_rank"
            shift_col = "shift_raw"
            scen_name = "Raw Time GC"

        # KPI Metrics Row
        tot_displaced = int((cf_df[shift_col] != 0).sum())
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric(f"Rank Displacements (Stage {cf_stage})", f"{tot_displaced} Riders", delta=f"{tot_displaced} shifts" if tot_displaced > 0 else "Steady")
        with col_m2:
            st.metric("Riders Awarded Bonuses", int((cf_df["total_bonus"] > 0).sum()), "10s / 6s / 4s Allocations")
        with col_m3:
            st.metric("Riders Assessed Penalties", int((cf_df["total_penalty"] > 0).sum()), "Drafting / Feed Zone Violations")

        # Primary Visualization: Interactive Slope Chart
        st.markdown(f"#### 📐 Interactive Slope Chart: Actual GC vs. {scen_name} (After Stage {cf_stage})")
        
        cf_sub = cf_df.head(cf_top_n).copy()
        melted_cf = []
        for _, r in cf_sub.iterrows():
            shift_val = int(r[shift_col])
            if shift_val > 0:
                status = "Gained Rank (+)"
            elif shift_val < 0:
                status = "Lost Rank (−)"
            else:
                status = "Unchanged (=)"

            melted_cf.append({
                "rider_name": r["rider_name"],
                "team_name": r["team_name"],
                "scenario": "1. Actual GC",
                "rank": int(r["actual_rank"]),
                "shift": shift_val,
                "shift_status": status,
                "bonus": int(r["total_bonus"]),
                "penalty": int(r["total_penalty"])
            })
            melted_cf.append({
                "rider_name": r["rider_name"],
                "team_name": r["team_name"],
                "scenario": f"2. {scen_name}",
                "rank": int(r[target_col]),
                "shift": shift_val,
                "shift_status": status,
                "bonus": int(r["total_bonus"]),
                "penalty": int(r["total_penalty"])
            })
        df_slope = pd.DataFrame(melted_cf)

        slope_chart = alt.Chart(df_slope).mark_line(point=True, strokeWidth=2.5).encode(
            x=alt.X("scenario:N", title="Classification Scenario", sort=["1. Actual GC", f"2. {scen_name}"]),
            y=alt.Y("rank:Q", scale=alt.Scale(reverse=True, zero=False), title="Classification Rank (Inverted)"),
            detail="rider_name:N",
            color=alt.Color("shift_status:N", scale=alt.Scale(
                domain=["Gained Rank (+)", "Lost Rank (−)", "Unchanged (=)"],
                range=["#10b981", "#ef4444", "#94a3b8"]
            ), title="Rank Movement"),
            tooltip=[
                alt.Tooltip("rider_name:N", title="Rider"),
                alt.Tooltip("team_name:N", title="Team"),
                alt.Tooltip("scenario:N", title="Scenario"),
                alt.Tooltip("rank:Q", title="Rank"),
                alt.Tooltip("shift:Q", title="Δ Rank Shift"),
                alt.Tooltip("bonus:Q", title="Total Bonus (s)"),
                alt.Tooltip("penalty:Q", title="Total Penalty (s)")
            ]
        ).properties(height=max(340, cf_top_n * 20))

        st.altair_chart(slope_chart, use_container_width=True)

        st.markdown(f"""
        <div class="narrative-box">
            <h4>💡 Counterfactual Insights & What-If Findings (Stage {cf_stage})</h4>
            <p>• <strong>Bonus Protection:</strong> In earlier stages (Stages 1–10), stage win and intermediate sprint bonuses created up to <strong>34 rank displacements</strong> across the peloton.<br>
            • <strong>Disciplinary Penalties:</strong> Strict enforcement of feed-zone and drafting rules shifted contenders by 10–20 seconds.<br>
            • <strong>End-of-Race Margins:</strong> By Stage 21, cumulative time gaps between top contenders widened into minutes, meaning bonus allocations insulated the podium rather than altering podium order.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("📋 View Counterfactual Replay Data Table"):
            st.dataframe(
                cf_df[[
                    "actual_rank", "bib_number", "rider_name", "team_name", "actual_time_formatted",
                    "total_bonus", "total_penalty",
                    "no_bonus_rank", "shift_no_bonus",
                    "no_penalty_rank", "shift_no_penalty",
                    "raw_rank", "shift_raw"
                ]],
                column_config={
                    "actual_rank": st.column_config.NumberColumn("Actual GC", format="%d"),
                    "bib_number": "Bib",
                    "rider_name": "Rider",
                    "team_name": "Team",
                    "actual_time_formatted": "Actual Time",
                    "total_bonus": st.column_config.NumberColumn("Bonus", format="-%ds"),
                    "total_penalty": st.column_config.NumberColumn("Pen", format="+%ds"),
                    "no_bonus_rank": st.column_config.NumberColumn("No-Bonus Rank", format="%d"),
                    "shift_no_bonus": st.column_config.NumberColumn("Δ No-Bonus", format="%+d"),
                    "no_penalty_rank": st.column_config.NumberColumn("No-Penalty Rank", format="%d"),
                    "shift_no_penalty": st.column_config.NumberColumn("Δ No-Penalty", format="%+d"),
                    "raw_rank": st.column_config.NumberColumn("Raw Time Rank", format="%d"),
                    "shift_raw": st.column_config.NumberColumn("Δ Raw", format="%+d")
                },
                hide_index=True,
                use_container_width=True
            )

    # -------------------------------------------------------------------------
    # TAB 4: E10 (Category A: Chart-First)
    # -------------------------------------------------------------------------
    with tab4:
        st.subheader("E10. Temporal GC Storyline & Inflection Points")
        st.markdown("""
        Trace cumulative adjusted time gap to the leader after each stage as an interactive multi-line narrative.
        Inflection points denote pivotal mountain stages and individual time trials that reshaped the standings.
        """)

        all_riders_df = execute_query("SELECT bib_number, rider_name, team_name FROM rider ORDER BY bib_number ASC;")
        rider_dict = {f"Bib {r['bib_number']} - {r['rider_name']} ({r['team_name']})": r["bib_number"] for _, r in all_riders_df.iterrows()}

        col_e10_1, col_e10_2 = st.columns([1, 2])
        with col_e10_1:
            metric_e10 = st.radio(
                "Y-Axis Metric:",
                ["Gap to Leader (Seconds)", "Progressive GC Rank (Inverted)", "Cumulative Time (Hours)"],
                horizontal=False
            )
        with col_e10_2:
            preset_e10 = st.selectbox(
                "Quick Selection Presets:",
                ["Podium Duel (Pogacar vs Vingegaard)", "Top 5 Contenders", "Top 10 Contenders", "All Squad Leaders", "Custom Selection"],
                index=1
            )

        # Preset logic
        if preset_e10 == "Podium Duel (Pogacar vs Vingegaard)":
            default_bibs = [1, 11]
        elif preset_e10 == "Top 5 Contenders":
            default_bibs = [1, 11, 72, 191, 151]
        elif preset_e10 == "Top 10 Contenders":
            default_bibs = [1, 11, 72, 191, 151, 221, 31, 71, 171, 131]
        elif preset_e10 == "All Squad Leaders":
            leaders_df = execute_query("SELECT bib_number FROM rider WHERE is_leader = 1;")
            default_bibs = leaders_df["bib_number"].tolist()
        else:
            default_bibs = [1, 11, 72, 191, 151]

        selected_labels = st.multiselect(
            "Select Contenders to Chart:",
            options=list(rider_dict.keys()),
            default=[k for k, v in rider_dict.items() if v in default_bibs]
        )
        selected_bibs = [rider_dict[k] for k in selected_labels]

        if selected_bibs:
            storyline_df = olap.get_temporal_gc_storyline(selected_bibs).copy()
            storyline_df["cum_hours"] = (storyline_df["cum_time"] / 3600.0).round(2)

            # Choose Y encoding
            if metric_e10 == "Progressive GC Rank (Inverted)":
                y_enc = alt.Y("gc_rank:Q", title="Progressive GC Rank (Inverted)", scale=alt.Scale(reverse=True, zero=False))
            elif metric_e10 == "Cumulative Time (Hours)":
                y_enc = alt.Y("cum_hours:Q", title="Cumulative Elapsed Time (Hours)", scale=alt.Scale(zero=False))
            else:
                y_enc = alt.Y("gap_to_leader:Q", title="Gap to GC Leader (Seconds)")

            # Primary Multi-Line Chart
            st.markdown(f"#### 📈 {metric_e10} across Stages 1–21")
            story_chart = alt.Chart(storyline_df).mark_line(point=True, strokeWidth=2.5).encode(
                x=alt.X("stage_id:O", title="Stage Number (1–21)"),
                y=y_enc,
                color=alt.Color("rider_name:N", title="Contender", scale=alt.Scale(scheme="category10")),
                tooltip=[
                    alt.Tooltip("stage_id:O", title="Stage"),
                    alt.Tooltip("stage_type:N", title="Terrain"),
                    alt.Tooltip("distance_km:Q", title="Km"),
                    alt.Tooltip("rider_name:N", title="Rider"),
                    alt.Tooltip("gap_to_leader:Q", title="Gap (s)"),
                    alt.Tooltip("cum_hours:Q", title="Cum Time (h)"),
                    alt.Tooltip("gc_rank:Q", title="GC Rank")
                ]
            ).properties(height=420)

            st.altair_chart(story_chart, use_container_width=True)

            # Structured Inflection Points Cards
            st.markdown("#### 📌 Key Inflection Points on the Course")
            inf1, inf2, inf3, inf4 = st.columns(4)
            with inf1:
                st.markdown("""
                <div class="metric-card" style="border-top: 4px solid #6366f1;">
                    <span class="stage-pill stage-itt">Stage 5 ITT</span>
                    <h4 style="margin: 6px 0 2px 0;">Caen (33.0 km)</h4>
                    <p style="font-size: 0.85rem; color: #475569;">First major time-trial test: Remco Evenepoel wins at 53.95 km/h; gaps open over 1m between TT specialists and pure climbers.</p>
                </div>
                """, unsafe_allow_html=True)
            with inf2:
                st.markdown("""
                <div class="metric-card" style="border-top: 4px solid #ef4444;">
                    <span class="stage-pill stage-mountain">Stage 10 MTN</span>
                    <h4 style="margin: 6px 0 2px 0;">Puy de Sancy</h4>
                    <p style="font-size: 0.85rem; color: #475569;">Brutal Massif Central summit finish creating the first sustained top-10 GC reshuffle before the first rest day.</p>
                </div>
                """, unsafe_allow_html=True)
            with inf3:
                st.markdown("""
                <div class="metric-card" style="border-top: 4px solid #ef4444;">
                    <span class="stage-pill stage-mountain">Stages 12 & 14</span>
                    <h4 style="margin: 6px 0 2px 0;">Pyrenean Highs</h4>
                    <p style="font-size: 0.85rem; color: #475569;">Hautacam and Superbagnères summit showdowns establish Tadej Pogacar and Jonas Vingegaard's decisive GC gap.</p>
                </div>
                """, unsafe_allow_html=True)
            with inf4:
                st.markdown("""
                <div class="metric-card" style="border-top: 4px solid #ef4444;">
                    <span class="stage-pill stage-mountain">Stages 18 & 19</span>
                    <h4 style="margin: 6px 0 2px 0;">Alpine Queens</h4>
                    <p style="font-size: 0.85rem; color: #475569;">Col de la Loze (2,304m) and La Plagne queen stages solidify podium positions heading into Paris.</p>
                </div>
                """, unsafe_allow_html=True)

            with st.expander("📋 View Temporal Stage-by-Stage Data Table"):
                st.dataframe(storyline_df, hide_index=True, use_container_width=True)
        else:
            st.info("Select at least one contender above to display the temporal storyline.")


# =============================================================================
# MODULE 3: STAGES & TERRAIN DYNAMICS (E2, E5, E6, E11, E15)
# =============================================================================
elif menu == "🏔️ Stages & Terrain (E2, E5, E6, E11, E15)":
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "E2: A Stage in Focus",
        "E5: Mountain Contours",
        "E6: Speed Profiles by Terrain",
        "E11: Against the Clock (ITT)",
        "E15: The Long Day"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: E2 (Category B: Hybrid Chart + Table)
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("E2. A Stage in Focus: Vignette & Team Perspective")
        st.markdown("""
        Examine a single stage in high definition: inspect the stage winner, time gaps of the top ten finishers, 
        and which teams populated the finale.
        """)

        stages_all = execute_query("SELECT stage_id, stage_type, distance_km, start_location, finish_location FROM stage ORDER BY stage_id ASC;")
        stage_labels = {f"Stage {r['stage_id']}: {r['start_location']} → {r['finish_location']} ({r['stage_type'].title()}, {r['distance_km']} km)": r['stage_id'] for _, r in stages_all.iterrows()}
        
        sel_label_e2 = st.selectbox("Select Stage to Inspect:", options=list(stage_labels.keys()), index=11)
        selected_stage = stage_labels[sel_label_e2]
        vignette = olap.get_stage_vignette(selected_stage)

        # Stage Metadata Header Card
        st.markdown(f"""
        <div class="narrative-box" style="border-left-color: #10b981;">
            <h4>🏁 Stage {vignette['stage_id']}: {vignette['start_location']} → {vignette['finish_location']}</h4>
            <p><strong>Date:</strong> {vignette['stage_date']} | <strong>Distance:</strong> {vignette['distance_km']} km | 
            <strong>Terrain:</strong> <span class="stage-pill stage-{vignette['stage_type'].replace(' ', '-')}">{vignette['stage_type'].upper()}</span></p>
        </div>
        """, unsafe_allow_html=True)

        finishers_df = olap.get_stage_finishers(selected_stage, top_n=10).copy()
        finishers_df["podium_cat"] = finishers_df["rank"].apply(
            lambda r: "Winner (1st)" if r == 1 else ("Podium (2nd-3rd)" if r <= 3 else "Top 10 (4th-10th)")
        )
        team_persp = olap.get_stage_team_perspective(selected_stage, top_n=10)

        # Side-by-side: Primary Lollipop Chart + Secondary Team Presence Chart
        col_st1, col_st2 = st.columns([3, 2])
        with col_st1:
            st.markdown("#### 🍭 Top-10 Finishers: Adjusted Time Gap to Winner")
            # Lollipop chart
            stem_e2 = alt.Chart(finishers_df).mark_rule(color="#cbd5e1", strokeWidth=2).encode(
                y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="rank", order="ascending"), title="Finish Position"),
                x=alt.X("gap:Q", title="Adjusted Time Gap to Winner (Seconds)"),
                x2=alt.value(0)
            )

            dot_e2 = alt.Chart(finishers_df).mark_circle(size=140).encode(
                y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="rank", order="ascending")),
                x=alt.X("gap:Q"),
                color=alt.Color("podium_cat:N", scale=alt.Scale(
                    domain=["Winner (1st)", "Podium (2nd-3rd)", "Top 10 (4th-10th)"],
                    range=["#eab308", "#2563eb", "#64748b"]
                ), title="Finish Position", legend=None),
                tooltip=[
                    alt.Tooltip("rank:Q", title="Finish Rank"),
                    alt.Tooltip("rider_name:N", title="Rider"),
                    alt.Tooltip("team_name:N", title="Team"),
                    alt.Tooltip("country_code:N", title="Nat"),
                    alt.Tooltip("time_formatted:N", title="Adjusted Time"),
                    alt.Tooltip("gap_formatted:N", title="Gap to Winner"),
                    alt.Tooltip("bonus:Q", title="Bonus (s)"),
                    alt.Tooltip("penalty:Q", title="Penalty (s)")
                ]
            )

            label_e2 = alt.Chart(finishers_df).mark_text(
                align="left", baseline="middle", dx=7, fontSize=11, color="#334155"
            ).encode(
                y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="rank", order="ascending")),
                x=alt.X("gap:Q"),
                text=alt.Text("gap_formatted:N")
            )

            st.altair_chart((stem_e2 + dot_e2 + label_e2).properties(height=320), use_container_width=True)

        with col_st2:
            st.markdown("#### 👥 Squad Representation in Top 10")
            bar_team = alt.Chart(team_persp).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color="#0284c7").encode(
                x=alt.X("top_finishers_count:Q", title="Count of Riders in Top 10", axis=alt.Axis(tickMinStep=1)),
                y=alt.Y("team_name:N", sort="-x", title="Team"),
                tooltip=[
                    alt.Tooltip("team_name:N", title="Team"),
                    alt.Tooltip("top_finishers_count:Q", title="Top 10 Riders"),
                    alt.Tooltip("riders_in_top_n:N", title="Finishers")
                ]
            ).properties(height=320)
            st.altair_chart(bar_team, use_container_width=True)

        # Detail Table below charts
        st.markdown("#### 📋 Leading Stage Finishers & Time Adjustments")
        st.dataframe(
            finishers_df[[
                "rank", "bib_number", "rider_name", "team_name", "country_code", 
                "time_formatted", "gap_formatted", "bonus", "penalty"
            ]],
            column_config={
                "rank": st.column_config.NumberColumn("Pos", format="P%d"),
                "bib_number": "Bib",
                "rider_name": "Rider",
                "team_name": "Team",
                "country_code": "Nat",
                "time_formatted": "Adjusted Time",
                "gap_formatted": "Gap to Winner",
                "bonus": st.column_config.NumberColumn("Bonus", format="-%ds"),
                "penalty": st.column_config.NumberColumn("Pen", format="+%ds")
            },
            hide_index=True,
            use_container_width=True
        )

    # -------------------------------------------------------------------------
    # TAB 2: E5 (Category A: Chart-First)
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("E5. Mountain Contours: Podiums & Time Gaps to Winner")
        st.markdown("""
        Surface two mountain-specific signals: **podium frequency on Mountain stages** (Top 3 finishes) 
        and **mean time gap to the stage winner** calculated strictly across high-mountain days.
        """)

        mtn_contours = olap.get_mountain_contours()

        # Primary Visualization: Bubble Scatter Plot
        st.markdown("#### 🫧 Mountain Performance: Podium Frequency vs. Mean Time Gap to Winner")
        st.caption("Top-left quadrant indicates elite mountain climbers (high podium count and tight time gaps to the winner).")

        bubble_e5 = alt.Chart(mtn_contours.head(30)).mark_circle().encode(
            x=alt.X("mountain_podium_count:Q", title="Mountain Stage Podiums (Top 3 Finishes)", axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("mean_gap_to_winner_seconds:Q", title="Mean Gap to Mountain Stage Winner (s, Inverted)", scale=alt.Scale(reverse=True, zero=False)),
            size=alt.Size("mountain_stages_completed:Q", title="Mountain Stages Done", scale=alt.Scale(range=[100, 500])),
            color=alt.Color("best_mountain_rank:Q", scale=alt.Scale(scheme="turbo", reverse=True), title="Best Mountain Rank"),
            tooltip=[
                alt.Tooltip("rider_name:N", title="Rider"),
                alt.Tooltip("team_name:N", title="Team"),
                alt.Tooltip("mountain_podium_count:Q", title="Mountain Podiums"),
                alt.Tooltip("mean_gap_formatted:N", title="Mean Gap to Winner"),
                alt.Tooltip("best_mountain_rank:Q", title="Best Mountain Finish"),
                alt.Tooltip("mountain_stages_completed:Q", title="Mountain Stages Done")
            ]
        ).properties(height=380)

        # Highlight labels for top mountain riders
        top_mtn_labels = alt.Chart(mtn_contours.head(7)).mark_text(
            align="left", baseline="bottom", dx=8, dy=-4, fontSize=11, fontWeight="bold", color="#1e293b"
        ).encode(
            x="mountain_podium_count:Q",
            y="mean_gap_to_winner_seconds:Q",
            text="rider_name:N"
        )

        st.altair_chart(bubble_e5 + top_mtn_labels, use_container_width=True)

        with st.expander("📋 View Mountain Contours Summary Table"):
            st.dataframe(
                mtn_contours.head(25)[[
                    "bib_number", "rider_name", "team_name", "mountain_stages_completed",
                    "mountain_podium_count", "mean_gap_formatted", "best_mountain_rank"
                ]],
                column_config={
                    "bib_number": "Bib",
                    "rider_name": "Rider",
                    "team_name": "Team",
                    "mountain_stages_completed": st.column_config.NumberColumn("Stages Done", format="%d"),
                    "mountain_podium_count": st.column_config.NumberColumn("Mountain Podiums", format="%d"),
                    "mean_gap_formatted": "Mean Gap to Winner",
                    "best_mountain_rank": st.column_config.NumberColumn("Best Finish", format="P%d")
                },
                hide_index=True,
                use_container_width=True
            )

        st.markdown("---")
        st.markdown("### 🔍 Daily Mountain Traces Drilldown")
        rider_mtn_dict = {f"Bib {r['bib_number']} - {r['rider_name']} ({r['team_name']})": r["bib_number"] for _, r in mtn_contours.head(25).iterrows()}
        selected_mtn_rider = st.selectbox("Select rider for daily mountain trace review:", options=list(rider_mtn_dict.keys()), index=0)
        sel_mtn_bib = rider_mtn_dict[selected_mtn_rider]

        traces_df = olap.get_rider_mountain_traces(sel_mtn_bib)
        if not traces_df.empty:
            traces_chart = alt.Chart(traces_df).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color="#ef4444").encode(
                y=alt.Y("finish_location:N", sort=alt.EncodingSortField(field="stage_id", order="ascending"), title="Mountain Summit"),
                x=alt.X("gap_to_stage_winner:Q", title="Gap to Stage Winner (Seconds)"),
                tooltip=[
                    alt.Tooltip("stage_id:Q", title="Stage #"),
                    alt.Tooltip("finish_location:N", title="Summit"),
                    alt.Tooltip("distance_km:Q", title="Km"),
                    alt.Tooltip("rank:Q", title="Finish Rank"),
                    alt.Tooltip("gap_formatted:N", title="Gap to Winner")
                ]
            ).properties(title=f"Time Gap to Winner across Mountain Stages - {selected_mtn_rider}", height=220)
            st.altair_chart(traces_chart, use_container_width=True)

        with st.expander("🏔️ View Daily Mountain Stage Traces Table"):
            st.dataframe(
                traces_df[[
                    "stage_id", "stage_date", "distance_km", "start_location", "finish_location",
                    "rank", "adj_time_formatted", "gap_formatted"
                ]],
                column_config={
                    "stage_id": st.column_config.NumberColumn("Stage #", format="%d"),
                    "stage_date": "Date",
                    "distance_km": st.column_config.NumberColumn("Km", format="%.1f"),
                    "start_location": "Origin",
                    "finish_location": "Destination",
                    "rank": st.column_config.NumberColumn("Finish Rank", format="P%d"),
                    "adj_time_formatted": "Adjusted Time",
                    "gap_formatted": "Gap to Stage Winner"
                },
                hide_index=True,
                use_container_width=True
            )

    # -------------------------------------------------------------------------
    # TAB 3: E6 (Category A: Chart-First)
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("E6. Speed Profiles as Simple Ratio (Distance / Time)")
        st.markdown("""
        Chart stage-type speed profiles using the ratio $\\text{km/h} = \\text{length\_km} / (\\text{time} / 3600)$ 
        across **Flat, Hilly, Mountain, and Individual Time-Trial** terrains.
        """)

        col_e6_1, col_e6_2 = st.columns([1, 2])
        with col_e6_1:
            perspective_e6 = st.radio("Speed Perspective:", ["Team Speed Profiles", "Top Contender Speed Profiles"], horizontal=False)

        team_speeds = olap.get_team_speed_profile()
        rider_speeds = olap.get_speed_by_stage_type()

        # Format terrain names
        terrain_order = ["flat", "hilly", "mountain", "individual time-trial"]
        terrain_display = {"flat": "Flat", "hilly": "Hilly", "mountain": "Mountain", "individual time-trial": "ITT"}

        if perspective_e6 == "Team Speed Profiles":
            all_teams = sorted(team_speeds["team_name"].unique())
            with col_e6_2:
                sel_teams_e6 = st.multiselect("Filter Teams:", options=all_teams, default=all_teams[:6])
            
            sub_speed = team_speeds[team_speeds["team_name"].isin(sel_teams_e6)].copy()
            sub_speed["terrain_name"] = sub_speed["stage_type"].map(terrain_display)

            # Primary Multi-Line Profile
            st.markdown("#### 📉 Team Average Speed Profile across Terrains")
            speed_chart = alt.Chart(sub_speed).mark_line(point=True, strokeWidth=2.5).encode(
                x=alt.X("terrain_name:N", sort=["Flat", "Hilly", "Mountain", "ITT"], title="Terrain Type"),
                y=alt.Y("avg_speed_kmh:Q", title="Average Speed (km/h)", scale=alt.Scale(zero=False)),
                color=alt.Color("team_name:N", title="Squad"),
                tooltip=[
                    alt.Tooltip("team_name:N", title="Team"),
                    alt.Tooltip("terrain_name:N", title="Terrain"),
                    alt.Tooltip("avg_speed_kmh:Q", title="Avg Speed (km/h)")
                ]
            ).properties(height=380)
            st.altair_chart(speed_chart, use_container_width=True)

        else:
            top_bibs_e6 = [1, 11, 72, 191, 151, 31, 101]
            avail_riders = rider_speeds.drop_duplicates(subset=["bib_number"])[["bib_number", "rider_name", "team_name"]]
            rider_map_e6 = {f"Bib {r['bib_number']} - {r['rider_name']} ({r['team_name']})": r["bib_number"] for _, r in avail_riders.iterrows()}
            
            with col_e6_2:
                sel_r_labels = st.multiselect(
                    "Filter Contenders:",
                    options=list(rider_map_e6.keys()),
                    default=[k for k, v in rider_map_e6.items() if v in top_bibs_e6]
                )
            sel_r_bibs = [rider_map_e6[k] for k in sel_r_labels]
            
            sub_r_speed = rider_speeds[rider_speeds["bib_number"].isin(sel_r_bibs)].copy()
            sub_r_speed["terrain_name"] = sub_r_speed["stage_type"].map(terrain_display)

            # Contender Multi-Line Chart
            st.markdown("#### 📉 Contender Speed Profile across Terrains")
            speed_chart = alt.Chart(sub_r_speed).mark_line(point=True, strokeWidth=2.5).encode(
                x=alt.X("terrain_name:N", sort=["Flat", "Hilly", "Mountain", "ITT"], title="Terrain Type"),
                y=alt.Y("avg_speed_kmh:Q", title="Average Speed (km/h)", scale=alt.Scale(zero=False)),
                color=alt.Color("rider_name:N", title="Contender"),
                tooltip=[
                    alt.Tooltip("rider_name:N", title="Rider"),
                    alt.Tooltip("team_name:N", title="Team"),
                    alt.Tooltip("terrain_name:N", title="Terrain"),
                    alt.Tooltip("avg_speed_kmh:Q", title="Avg Speed (km/h)")
                ]
            ).properties(height=380)
            st.altair_chart(speed_chart, use_container_width=True)

        # Pivot Speed Table
        pivot_speed = team_speeds.pivot(index="team_name", columns="stage_type", values="avg_speed_kmh").reset_index()
        pivot_speed["flat_to_mtn_ratio"] = (pivot_speed["mountain"] / pivot_speed["flat"] * 100.0).round(1)

        with st.expander("📋 View Speed by Terrain Matrix & Retention Table"):
            st.dataframe(
                pivot_speed.sort_values("mountain", ascending=False),
                column_config={
                    "team_name": "Team",
                    "flat": st.column_config.NumberColumn("Flat Speed", format="%.2f km/h"),
                    "hilly": st.column_config.NumberColumn("Hilly Speed", format="%.2f km/h"),
                    "mountain": st.column_config.NumberColumn("Mountain Speed", format="%.2f km/h"),
                    "individual time-trial": st.column_config.NumberColumn("ITT Speed", format="%.2f km/h"),
                    "flat_to_mtn_ratio": st.column_config.NumberColumn("Mountain/Flat Retention (%)", format="%.1f%%")
                },
                hide_index=True,
                use_container_width=True
            )

    # -------------------------------------------------------------------------
    # TAB 4: E11 (Category C: Table/Cards-First)
    # -------------------------------------------------------------------------
    with tab4:
        st.subheader("E11. Against the Clock: Individual Time Trial Catalogue")
        st.markdown("""
        The 2025 Tour includes **two individual time trials** with completely contrasting profiles:
        a 33.0 km flat power course in Normandy and a 10.9 km uphill mountain test in the Pyrenees.
        """)

        itt_df = olap.get_itt_catalogue()
        
        # Category C Recommended Layout: Two Side-by-Side Comparison Cards
        col_itt1, col_itt2 = st.columns(2)
        
        # Stage 5 Data
        stg5_info = itt_df[itt_df["stage_id"] == 5].iloc[0]
        df5 = olap.get_stage_finishers(5, top_n=6).copy()
        df5["speed_kmh"] = (stg5_info["distance_km"] * 3600.0 / df5["finish_time"]).round(2)
        df5["podium_cat"] = df5["rank"].apply(
            lambda r: "Winner (1st)" if r == 1 else ("Podium (2nd-3rd)" if r <= 3 else "Top 6 (4th-6th)")
        )
        df5["label_text"] = df5.apply(
            lambda r: f"Winner ({r['time_formatted']})" if r["rank"] == 1 else f"{r['gap_formatted']} ({r['speed_kmh']} km/h)",
            axis=1
        )
        max_gap5 = max(float(df5["gap"].max()), 1.0)
        x_domain_max5 = max_gap5 * 1.55 + 10

        with col_itt1:
            st.markdown(f"""
            <div class="metric-card" style="border-top: 5px solid #4f46e5; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span class="stage-pill stage-itt">ITT STAGE 5</span>
                    <span style="font-weight: 700; color: #4338ca; font-size: 0.95rem;">{stg5_info['distance_km']} km (Flat ITT)</span>
                </div>
                <h3 style="margin: 4px 0 2px 0; color: #1e1b4b; font-size: 1.35rem;">{stg5_info['start_location']} → {stg5_info['finish_location']}</h3>
                <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 8px;">
                    📅 <strong>Date:</strong> {stg5_info['stage_date']} | Flat rolling power course through Normandy
                </div>
                <div style="background: #eef2ff; border-radius: 8px; padding: 10px 14px; border: 1px solid #c7d2fe;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 0.72rem; font-weight: 700; color: #4338ca; text-transform: uppercase; letter-spacing: 0.5px;">Stage Winner</div>
                            <div style="font-size: 1.15rem; font-weight: 800; color: #0f172a;">🥇 {stg5_info['winner_name']}</div>
                            <div style="font-size: 0.82rem; color: #475569;">{stg5_info['winner_team']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.1rem; font-weight: 800; color: #3730a3;">⏱️ {stg5_info['winning_time_formatted']}</div>
                            <div style="font-size: 0.85rem; font-weight: 600; color: #4338ca;">⚡ {stg5_info['winner_speed_kmh']} km/h</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("##### ⚡ Caen Top Finishers: Time Gap & Average Speed")
            stem5 = alt.Chart(df5).mark_rule(color="#cbd5e1", strokeWidth=2).encode(
                y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="rank", order="ascending"), title=None),
                x=alt.X("gap:Q", title="Adjusted Time Gap to Winner (Seconds)", scale=alt.Scale(domain=[0, x_domain_max5])),
                x2=alt.value(0)
            )
            dot5 = alt.Chart(df5).mark_circle(size=140).encode(
                y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="rank", order="ascending")),
                x=alt.X("gap:Q"),
                color=alt.Color("podium_cat:N", scale=alt.Scale(
                    domain=["Winner (1st)", "Podium (2nd-3rd)", "Top 6 (4th-6th)"],
                    range=["#eab308", "#4f46e5", "#64748b"]
                ), legend=None),
                tooltip=[
                    alt.Tooltip("rank:Q", title="Rank"),
                    alt.Tooltip("rider_name:N", title="Rider"),
                    alt.Tooltip("team_name:N", title="Team"),
                    alt.Tooltip("time_formatted:N", title="Adjusted Time"),
                    alt.Tooltip("gap_formatted:N", title="Gap to Winner"),
                    alt.Tooltip("speed_kmh:Q", title="Avg Speed (km/h)")
                ]
            )
            txt5 = alt.Chart(df5).mark_text(align="left", baseline="middle", dx=8, fontSize=11, color="#334155").encode(
                y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="rank", order="ascending")),
                x=alt.X("gap:Q"),
                text=alt.Text("label_text:N")
            )
            chart_stg5 = (stem5 + dot5 + txt5).properties(height=240)
            st.altair_chart(chart_stg5, use_container_width=True)

        # Stage 13 Data
        stg13_info = itt_df[itt_df["stage_id"] == 13].iloc[0]
        df13 = olap.get_stage_finishers(13, top_n=6).copy()
        df13["speed_kmh"] = (stg13_info["distance_km"] * 3600.0 / df13["finish_time"]).round(2)
        df13["podium_cat"] = df13["rank"].apply(
            lambda r: "Winner (1st)" if r == 1 else ("Podium (2nd-3rd)" if r <= 3 else "Top 6 (4th-6th)")
        )
        df13["label_text"] = df13.apply(
            lambda r: f"Winner ({r['time_formatted']})" if r["rank"] == 1 else f"{r['gap_formatted']} ({r['speed_kmh']} km/h)",
            axis=1
        )
        max_gap13 = max(float(df13["gap"].max()), 1.0)
        x_domain_max13 = max_gap13 * 1.55 + 10

        with col_itt2:
            st.markdown(f"""
            <div class="metric-card" style="border-top: 5px solid #ef4444; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span class="stage-pill stage-mountain">ITT STAGE 13</span>
                    <span style="font-weight: 700; color: #b91c1c; font-size: 0.95rem;">{stg13_info['distance_km']} km (Mountain ITT)</span>
                </div>
                <h3 style="margin: 4px 0 2px 0; color: #7f1d1d; font-size: 1.35rem;">{stg13_info['start_location']} → {stg13_info['finish_location']}</h3>
                <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 8px;">
                    📅 <strong>Date:</strong> {stg13_info['stage_date']} | Steep Pyrenean mountain time-trial (8% finish)
                </div>
                <div style="background: #fef2f2; border-radius: 8px; padding: 10px 14px; border: 1px solid #fecaca;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 0.72rem; font-weight: 700; color: #b91c1c; text-transform: uppercase; letter-spacing: 0.5px;">Stage Winner</div>
                            <div style="font-size: 1.15rem; font-weight: 800; color: #0f172a;">🥇 {stg13_info['winner_name']}</div>
                            <div style="font-size: 0.82rem; color: #475569;">{stg13_info['winner_team']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.1rem; font-weight: 800; color: #991b1b;">⏱️ {stg13_info['winning_time_formatted']}</div>
                            <div style="font-size: 0.85rem; font-weight: 600; color: #b91c1c;">⚡ {stg13_info['winner_speed_kmh']} km/h</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("##### ⚡ Peyragudes Top Finishers: Time Gap & Average Speed")
            stem13 = alt.Chart(df13).mark_rule(color="#cbd5e1", strokeWidth=2).encode(
                y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="rank", order="ascending"), title=None),
                x=alt.X("gap:Q", title="Adjusted Time Gap to Winner (Seconds)", scale=alt.Scale(domain=[0, x_domain_max13])),
                x2=alt.value(0)
            )
            dot13 = alt.Chart(df13).mark_circle(size=140).encode(
                y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="rank", order="ascending")),
                x=alt.X("gap:Q"),
                color=alt.Color("podium_cat:N", scale=alt.Scale(
                    domain=["Winner (1st)", "Podium (2nd-3rd)", "Top 6 (4th-6th)"],
                    range=["#eab308", "#ef4444", "#64748b"]
                ), legend=None),
                tooltip=[
                    alt.Tooltip("rank:Q", title="Rank"),
                    alt.Tooltip("rider_name:N", title="Rider"),
                    alt.Tooltip("team_name:N", title="Team"),
                    alt.Tooltip("time_formatted:N", title="Adjusted Time"),
                    alt.Tooltip("gap_formatted:N", title="Gap to Winner"),
                    alt.Tooltip("speed_kmh:Q", title="Avg Speed (km/h)")
                ]
            )
            txt13 = alt.Chart(df13).mark_text(align="left", baseline="middle", dx=8, fontSize=11, color="#334155").encode(
                y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="rank", order="ascending")),
                x=alt.X("gap:Q"),
                text=alt.Text("label_text:N")
            )
            chart_stg13 = (stem13 + dot13 + txt13).properties(height=240)
            st.altair_chart(chart_stg13, use_container_width=True)

        st.markdown("---")
        # Detailed Leaderboards & Interactive Charts
        st.markdown("### ⏱️ Detailed ITT Stage Analysis & Leaderboards")
        itt_sel = st.radio(
            "Select Stage for Detailed Top 10 Analysis & Visual Gap Profile:",
            [5, 13],
            format_func=lambda s: f"Stage {s} ({'Caen Flat ITT — 33.0 km' if s == 5 else 'Peyragudes Mountain ITT — 10.9 km'})",
            horizontal=True
        )

        itt_finishers = olap.get_stage_finishers(itt_sel, top_n=10).copy()
        itt_dist = 33.0 if itt_sel == 5 else 10.9
        itt_finishers["speed_kmh"] = (itt_dist * 3600.0 / itt_finishers["finish_time"]).round(2)
        itt_finishers["podium_cat"] = itt_finishers["rank"].apply(
            lambda r: "Winner (1st)" if r == 1 else ("Podium (2nd-3rd)" if r <= 3 else "Top 10 (4th-10th)")
        )
        itt_finishers["display_gap"] = itt_finishers.apply(
            lambda r: f"Winner ({r['time_formatted']})" if r["rank"] == 1 else f"{r['gap_formatted']} ({r['speed_kmh']} km/h)",
            axis=1
        )

        itt_team_persp = olap.get_stage_team_perspective(itt_sel, top_n=10)

        # Side-by-side Top-10 Lollipop Gap Chart and Squad Presence Chart
        col_itt_ch1, col_itt_ch2 = st.columns([3, 2])
        with col_itt_ch1:
            st.markdown(f"#### 🍭 Stage {itt_sel} Top-10 Finishers: Adjusted Time Gap to Winner")
            stem_itt = alt.Chart(itt_finishers).mark_rule(color="#cbd5e1", strokeWidth=2).encode(
                y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="rank", order="ascending"), title="Finish Position"),
                x=alt.X("gap:Q", title="Adjusted Time Gap to Winner (Seconds)"),
                x2=alt.value(0)
            )
            dot_itt = alt.Chart(itt_finishers).mark_circle(size=140).encode(
                y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="rank", order="ascending")),
                x=alt.X("gap:Q"),
                color=alt.Color("podium_cat:N", scale=alt.Scale(
                    domain=["Winner (1st)", "Podium (2nd-3rd)", "Top 10 (4th-10th)"],
                    range=["#eab308", "#2563eb", "#64748b"]
                ), title="Finish Position", legend=None),
                tooltip=[
                    alt.Tooltip("rank:Q", title="Finish Rank"),
                    alt.Tooltip("rider_name:N", title="Rider"),
                    alt.Tooltip("team_name:N", title="Team"),
                    alt.Tooltip("country_code:N", title="Nat"),
                    alt.Tooltip("time_formatted:N", title="Adjusted Time"),
                    alt.Tooltip("gap_formatted:N", title="Gap to Winner"),
                    alt.Tooltip("speed_kmh:Q", title="Average Speed (km/h)")
                ]
            )
            label_itt = alt.Chart(itt_finishers).mark_text(
                align="left", baseline="middle", dx=7, fontSize=11, color="#334155"
            ).encode(
                y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="rank", order="ascending")),
                x=alt.X("gap:Q"),
                text=alt.Text("display_gap:N")
            )
            st.altair_chart((stem_itt + dot_itt + label_itt).properties(height=320), use_container_width=True)

        with col_itt_ch2:
            st.markdown(f"#### 👥 Squad Representation in Stage {itt_sel} Top 10")
            bar_itt_team = alt.Chart(itt_team_persp).mark_bar(
                cornerRadiusTopRight=4, cornerRadiusBottomRight=4,
                color="#4f46e5" if itt_sel == 5 else "#ef4444"
            ).encode(
                x=alt.X("top_finishers_count:Q", title="Count of Riders in Top 10", axis=alt.Axis(tickMinStep=1)),
                y=alt.Y("team_name:N", sort="-x", title="Team"),
                tooltip=[
                    alt.Tooltip("team_name:N", title="Team"),
                    alt.Tooltip("top_finishers_count:Q", title="Top 10 Riders"),
                    alt.Tooltip("riders_in_top_n:N", title="Finishers")
                ]
            ).properties(height=320)
            st.altair_chart(bar_itt_team, use_container_width=True)

        # Detail Data Table
        st.markdown(f"#### 📋 Stage {itt_sel} Full Leaderboard & Performance Metrics")
        st.dataframe(
            itt_finishers[[
                "rank", "bib_number", "rider_name", "team_name", "country_code",
                "time_formatted", "gap_formatted", "speed_kmh"
            ]],
            column_config={
                "rank": st.column_config.NumberColumn("Rank", format="P%d"),
                "bib_number": "Bib",
                "rider_name": "Rider",
                "team_name": "Team",
                "country_code": "Nat",
                "time_formatted": "Adjusted Time",
                "gap_formatted": "Gap to Winner",
                "speed_kmh": st.column_config.NumberColumn("Avg Speed", format="%.2f km/h")
            },
            hide_index=True,
            use_container_width=True
        )

        with st.expander("⚡ Dual-ITT Head-to-Head Comparison: Flat vs Mountain Contender Speeds"):
            st.markdown("""
            Compare how top time-trialists and GC contenders performed across the contrasting flat power terrain 
            of Stage 5 (Caen) versus the steep mountain ascent of Stage 13 (Peyragudes).
            """)
            q_dual = """
            SELECT 
                r.bib_number,
                rd.rider_name,
                rd.team_name,
                s.stage_id,
                CASE WHEN s.stage_id = 5 THEN 'Stage 5 (Flat ITT, 33.0 km)' ELSE 'Stage 13 (Mountain ITT, 10.9 km)' END AS stage_label,
                r.rank,
                r.adj_time,
                ROUND(s.distance_km * 3600.0 / r.finish_time, 2) AS speed_kmh
            FROM result_with_adj_time r
            JOIN rider rd ON r.bib_number = rd.bib_number
            JOIN stage s ON r.stage_id = s.stage_id
            WHERE s.stage_type = 'individual time-trial'
            AND r.bib_number IN (
                SELECT bib_number FROM result_with_adj_time WHERE stage_id IN (5, 13) AND rank <= 8
            )
            ORDER BY r.bib_number, s.stage_id;
            """
            df_dual = execute_query(q_dual)
            if not df_dual.empty:
                dual_chart = alt.Chart(df_dual).mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3).encode(
                    y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="speed_kmh", op="max", order="descending"), title="Rider"),
                    x=alt.X("speed_kmh:Q", title="Average Speed (km/h)"),
                    color=alt.Color("stage_label:N", scale=alt.Scale(
                        domain=["Stage 5 (Flat ITT, 33.0 km)", "Stage 13 (Mountain ITT, 10.9 km)"],
                        range=["#6366f1", "#ef4444"]
                    ), title="Time Trial Stage"),
                    yOffset="stage_label:N",
                    tooltip=[
                        alt.Tooltip("rider_name:N", title="Rider"),
                        alt.Tooltip("team_name:N", title="Team"),
                        alt.Tooltip("stage_label:N", title="Stage"),
                        alt.Tooltip("rank:Q", title="Finish Rank"),
                        alt.Tooltip("speed_kmh:Q", title="Speed (km/h)")
                    ]
                ).properties(height=340)
                st.altair_chart(dual_chart, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 5: E15 (Category B: Hybrid Chart + Table)
    # -------------------------------------------------------------------------
    with tab5:
        st.subheader("E15. The Long Day: Spotlight on Longest Routes")
        st.markdown("""
        Spotlight the longest route on the Tour de France itinerary, its geographic endurance profile, 
        and leading finishers.
        """)

        dist_stages = olap.get_stages_by_distance().copy()
        longest = dist_stages.iloc[0]

        # Stage selector for comparison
        stage_names_map = {f"Stage {r['stage_id']}: {r['start_location']} → {r['finish_location']} ({r['distance_km']} km)": r['stage_id'] for _, r in dist_stages.iterrows()}
        selected_long_label = st.selectbox("Highlight Stage for Inspection:", options=list(stage_names_map.keys()), index=0)
        sel_stage_dist = stage_names_map[selected_long_label]
        sel_row = dist_stages[dist_stages["stage_id"] == sel_stage_dist].iloc[0]

        # Summary Spotlight Card
        is_longest_sel = (sel_stage_dist == int(longest["stage_id"]))
        st.markdown(f"""
        <div class="narrative-box" style="border-left-color: {'#8b5cf6' if is_longest_sel else '#0284c7'};">
            <h4>👑 {'The Longest Day of the Tour' if is_longest_sel else f'Stage Spotlight: Stage {sel_row["stage_id"]}'} ({sel_row['distance_km']} km)</h4>
            <p><strong>Route:</strong> {sel_row['start_location']} → {sel_row['finish_location']} on {sel_row['stage_date']}<br>
            <strong>Terrain:</strong> {sel_row['stage_type'].title()} Stage<br>
            <strong>Endurance Challenge:</strong> At <strong>{sel_row['distance_km']} km</strong>, this route demanded immense stamina and bunch positioning over 4.5 hours of racing.</p>
        </div>
        """, unsafe_allow_html=True)

        # Primary Visualization: Ranked Horizontal Bar Chart showing Stage Distances
        st.markdown("#### 📏 All 21 Stages Ranked by Distance (km)")
        
        dist_stages["is_highlighted"] = dist_stages["stage_id"] == sel_stage_dist
        dist_stages["stage_label"] = "Stage " + dist_stages["stage_id"].astype(str) + " (" + dist_stages["stage_type"].str.title() + ")"

        bar_e15 = alt.Chart(dist_stages).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
            y=alt.Y("stage_label:N", sort=alt.EncodingSortField(field="distance_km", order="descending"), title="Stage (Type)"),
            x=alt.X("distance_km:Q", title="Distance (km)"),
            color=alt.Color("is_highlighted:N", scale=alt.Scale(domain=[True, False], range=["#f59e0b", "#3b82f6"]), legend=None),
            tooltip=[
                alt.Tooltip("stage_id:Q", title="Stage #"),
                alt.Tooltip("distance_km:Q", title="Distance (km)"),
                alt.Tooltip("stage_type:N", title="Terrain"),
                alt.Tooltip("stage_date:N", title="Date"),
                alt.Tooltip("start_location:N", title="Origin"),
                alt.Tooltip("finish_location:N", title="Destination")
            ]
        ).properties(height=450)

        st.altair_chart(bar_e15, use_container_width=True)

        # Detail Table for Stage Finishers
        st.markdown(f"#### 🏆 Leading Finishers: Stage {sel_stage_dist} ({sel_row['distance_km']} km)")
        long_finishers = olap.get_stage_finishers(int(sel_stage_dist), top_n=10)
        st.dataframe(
            long_finishers[["rank", "bib_number", "rider_name", "team_name", "country_code", "time_formatted", "gap_formatted"]],
            column_config={
                "rank": st.column_config.NumberColumn("Rank", format="P%d"),
                "bib_number": "Bib",
                "rider_name": "Rider",
                "team_name": "Team",
                "country_code": "Nat",
                "time_formatted": "Adjusted Time",
                "gap_formatted": "Gap to Winner"
            },
            hide_index=True,
            use_container_width=True
        )

        with st.expander("📋 View Complete 21-Stage Distance Ranking Table"):
            st.dataframe(
                dist_stages[["stage_id", "stage_date", "distance_km", "stage_type", "start_location", "finish_location"]],
                column_config={
                    "stage_id": "Stage #",
                    "distance_km": st.column_config.NumberColumn("Distance (km)", format="%.1f km"),
                    "stage_type": "Terrain",
                    "stage_date": "Date",
                    "start_location": "Origin",
                    "finish_location": "Destination"
                },
                hide_index=True,
                use_container_width=True
            )


# =============================================================================
# MODULE 4: TEAMS & SQUAD DYNAMICS (E3, E13, E14)
# =============================================================================
elif menu == "👥 Teams & Squads (E3, E13, E14)":
    tab1, tab2, tab3 = st.tabs([
        "E3: Team Burden & Contribution",
        "E13: Depth of Squads & Attrition",
        "E14: Top-Ten Intensity by Team"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: E3 (Category A: Chart-First)
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("E3. Team Burden and Contribution")
        st.markdown("""
        Roll up each team's aggregate adjusted time across the entire Tour, then open the aggregation to reveal 
        which riders carried the time load.
        """)

        team_sum = olap.get_team_summary()
        all_burden = olap.get_all_teams_rider_contributions()

        col_e3_1, col_e3_2 = st.columns([1, 2])
        with col_e3_1:
            e3_view = st.radio("Visualization Mode:", ["100% Stacked Squad Comparison", "Single Squad Deep Dive"], horizontal=False)

        if e3_view == "100% Stacked Squad Comparison":
            with col_e3_2:
                top_teams_e3 = st.slider("Display Teams:", min_value=5, max_value=23, value=12, step=1)

            top_team_names = team_sum.head(top_teams_e3)["team_name"].tolist()
            sub_burden = all_burden[all_burden["team_name"].isin(top_team_names)].copy()

            # Primary Visualization: 100% Stacked Horizontal Bar Chart
            st.markdown(f"#### 📊 100% Stacked Bar Chart: Rider Contributions to Team Aggregate Time (Top {top_teams_e3} Squads)")
            st.caption("Each bar sums to 100% of squad aggregate time; segments illustrate rider roles and attrition impact.")

            e3_stacked = alt.Chart(sub_burden).mark_bar().encode(
                y=alt.Y("team_name:N", sort=top_team_names, title="Team (Ordered by Aggregate Time)"),
                x=alt.X("pct_team_burden:Q", stack="zero", title="Share of Total Squad Time (%)", axis=alt.Axis(format=".0f")),
                color=alt.Color("role:N", scale=alt.Scale(scheme="tableau10"), title="Rider Squad Role"),
                tooltip=[
                    alt.Tooltip("team_name:N", title="Team"),
                    alt.Tooltip("rider_name:N", title="Rider"),
                    alt.Tooltip("role:N", title="Role"),
                    alt.Tooltip("is_leader:N", title="Is Leader"),
                    alt.Tooltip("pct_team_burden:Q", title="Share of Team Time (%)"),
                    alt.Tooltip("stages_completed:Q", title="Stages Done"),
                    alt.Tooltip("status:N", title="Status")
                ]
            ).properties(height=max(320, top_teams_e3 * 26))

            st.altair_chart(e3_stacked, use_container_width=True)

        else:
            with col_e3_2:
                sel_team_e3 = st.selectbox("Select Squad to Deep Dive:", options=team_sum["team_name"].tolist(), index=0)

            team_riders_e3 = olap.get_team_rider_contributions(sel_team_e3).copy()
            def get_rider_status_cat(r):
                if r["is_leader"] == 1:
                    return "Leader"
                elif "Completed" in str(r["status"]):
                    return "Completed"
                else:
                    return "Exited"
            team_riders_e3["status_cat"] = team_riders_e3.apply(get_rider_status_cat, axis=1)

            # Single squad breakdown chart
            st.markdown(f"#### 🚴 Rider Time Burden Distribution: {sel_team_e3}")
            single_e3_bar = alt.Chart(team_riders_e3).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="pct_team_burden", order="descending"), title="Rider"),
                x=alt.X("pct_team_burden:Q", title="Share of Squad Aggregate Time (%)"),
                color=alt.Color("status_cat:N", scale=alt.Scale(
                    domain=["Leader", "Completed", "Exited"],
                    range=["#eab308", "#2563eb", "#ef4444"]
                ), title="Status", legend=None),
                tooltip=[
                    alt.Tooltip("rider_name:N", title="Rider"),
                    alt.Tooltip("role:N", title="Role"),
                    alt.Tooltip("is_leader:N", title="Is Leader"),
                    alt.Tooltip("pct_team_burden:Q", title="Share of Team Time (%)"),
                    alt.Tooltip("time_formatted:N", title="Cumulative Time"),
                    alt.Tooltip("stages_completed:Q", title="Stages Done"),
                    alt.Tooltip("status:N", title="Status")
                ]
            ).properties(height=260)

            label_single_e3 = alt.Chart(team_riders_e3).mark_text(
                align="left", baseline="middle", dx=6, fontSize=11, color="#334155"
            ).encode(
                y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="pct_team_burden", order="descending")),
                x=alt.X("pct_team_burden:Q"),
                text=alt.Text("pct_team_burden:Q", format=".2f")
            )
            st.altair_chart(single_e3_bar + label_single_e3, use_container_width=True)

        st.markdown("""
        <div class="narrative-box">
            <h4>💡 Analytical Insight: Aggregate Time Contribution vs. Performance</h4>
            <p>• <strong>Aggregate Burden vs. GC Performance:</strong> In a team aggregate time calculation, riders who survive all 21 stages each contribute approximately <strong>12.5% to 15.0%</strong> of the team's total seconds.<br>
            • <strong>Attrition Discrepancy:</strong> Riders who exit mid-race (DNS/DNF) contribute a disproportionately lower percentage of total seconds (e.g. 1% to 10%) simply because they logged fewer stages—clarifying why aggregate time must be analyzed alongside individual completion status.</p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("📋 View Team Aggregate Standings Table"):
            st.dataframe(
                team_sum[[
                    "team_name", "country_code", "roster_count", "active_finishers", 
                    "time_formatted", "gap_to_lead_team", "total_stage_results"
                ]],
                column_config={
                    "team_name": "Team",
                    "country_code": "Country",
                    "roster_count": st.column_config.NumberColumn("Roster", format="%d"),
                    "active_finishers": st.column_config.NumberColumn("Finishers", format="%d"),
                    "time_formatted": "Cumulative Adjusted Time",
                    "gap_to_lead_team": "Gap to Lead Squad",
                    "total_stage_results": "Total Results Count"
                },
                hide_index=True,
                use_container_width=True
            )

        with st.expander("🚴 View Rider Burden Details Table"):
            sel_exp_team = st.selectbox("Inspect Full Squad Burden Table:", options=team_sum["team_name"].tolist(), index=0, key="exp_team_e3")
            b_df = olap.get_team_rider_contributions(sel_exp_team)
            st.dataframe(
                b_df[[
                    "bib_number", "rider_name", "role", "is_leader", "status",
                    "stages_completed", "time_formatted", "pct_team_burden", "avg_stage_rank", "best_stage_rank"
                ]],
                column_config={
                    "bib_number": "Bib",
                    "rider_name": "Rider",
                    "role": "Role",
                    "is_leader": "Is Leader",
                    "status": "Status",
                    "stages_completed": st.column_config.NumberColumn("Stages", format="%d"),
                    "time_formatted": "Rider Time",
                    "pct_team_burden": st.column_config.NumberColumn("Share of Team Time (%)", format="%.2f%%"),
                    "avg_stage_rank": st.column_config.NumberColumn("Avg Rank", format="%.1f"),
                    "best_stage_rank": st.column_config.NumberColumn("Best Rank", format="P%d")
                },
                hide_index=True,
                use_container_width=True
            )

    # -------------------------------------------------------------------------
    # TAB 2: E13 (Category B: Hybrid Chart + Table)
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("E13. Depth of Squads & Roster Attrition")
        st.markdown("""
        Every team initially starts with **8 riders**. Trace roster attrition and squad retention 
        by comparing riders who completed all 21 stages against mid-race exits (DNS/DNF).
        """)

        squad_df = olap.get_squad_depth().copy()

        # Summary KPIs
        sq1, sq2, sq3 = st.columns(3)
        with sq1:
            st.metric("Total Starting Rosters", "23 Squads (184 Riders)", "8 Riders per Squad")
        with sq2:
            st.metric("Squads with 100% Retention (8/8)", "5 Squads Intact", "Arkéa, Israel, Picnic, Visma, Tudor")
        with sq3:
            st.metric("Total Race Exits", "24 Exited Riders", "87.0% Overall Pelton Survival Rate")

        # Primary Visualization: Segmented Horizontal Bar Chart
        st.markdown("#### 🛡️ Squad Depth & Roster Survival (8-Rider Initial Roster)")
        
        melted_sq = []
        for _, r in squad_df.iterrows():
            c_ratio = f"{int(r['active_finishers'])}/8"
            melted_sq.append({
                "team_name": r["team_name"],
                "status": "Completed (21 Stages)",
                "count": int(r["active_finishers"]),
                "ratio": c_ratio,
                "rate": float(r["survival_rate_pct"])
            })
            melted_sq.append({
                "team_name": r["team_name"],
                "status": "Exited (DNS/DNF)",
                "count": int(r["exit_count"]),
                "ratio": c_ratio,
                "rate": float(r["survival_rate_pct"])
            })
        df_sq_melt = pd.DataFrame(melted_sq)

        bar_e13 = alt.Chart(df_sq_melt).mark_bar().encode(
            y=alt.Y("team_name:N", sort=alt.EncodingSortField(field="count", op="max", order="descending"), title="Team"),
            x=alt.X("count:Q", title="Roster Breakdown (Max 8 Riders)", scale=alt.Scale(domain=[0, 8])),
            color=alt.Color("status:N", scale=alt.Scale(
                domain=["Completed (21 Stages)", "Exited (DNS/DNF)"],
                range=["#10b981", "#f43f5e"]
            ), title="Status"),
            tooltip=[
                alt.Tooltip("team_name:N", title="Team"),
                alt.Tooltip("status:N", title="Status"),
                alt.Tooltip("count:Q", title="Count"),
                alt.Tooltip("ratio:N", title="Roster Ratio"),
                alt.Tooltip("rate:Q", title="Survival Rate (%)")
            ]
        ).properties(height=480)

        st.altair_chart(bar_e13, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 🚪 Doorway to Full Squad Rosters")
        door_team = st.selectbox("Select Team to Inspect Full Roster:", options=squad_df["team_name"].tolist(), index=0)
        roster_df = olap.get_team_roster(door_team)

        # Team specific retention ratio badge
        active_cnt = (roster_df["status"] == "Active / Completed").sum()
        st.markdown(f"**Roster Retention Ratio:** `{active_cnt}/8 Riders Completed` ({active_cnt * 12.5:.1f}%)")

        st.dataframe(
            roster_df,
            column_config={
                "bib_number": "Bib",
                "rider_name": "Rider",
                "dob": "Date of Birth",
                "country_code": "Nationality",
                "role": "Squad Role",
                "is_leader": "Is Leader",
                "status": "Race Status"
            },
            hide_index=True,
            use_container_width=True
        )

        with st.expander("📋 View Full Squad Survival & Depth Summary Table"):
            st.dataframe(
                squad_df,
                column_config={
                    "team_name": "Team",
                    "country_code": "Country",
                    "starting_riders": st.column_config.NumberColumn("Starting Roster", format="%d"),
                    "active_finishers": st.column_config.NumberColumn("21-Stage Finishers", format="%d"),
                    "exit_count": st.column_config.NumberColumn("Exits", format="%d"),
                    "survival_rate_pct": st.column_config.NumberColumn("Survival Rate", format="%.1f%%")
                },
                hide_index=True,
                use_container_width=True
            )

    # -------------------------------------------------------------------------
    # TAB 3: E14 (Category A: Chart-First)
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("E14. Top-Ten Intensity by Team across Terrains")
        st.markdown("""
        Aggregate top-ten stage presences at the squad level broken down by stage terrain 
        (**Flat, Hilly, Mountain, ITT**), highlighting which teams dominate specific profiles.
        """)

        intensity_df = olap.get_team_top10_intensity()

        # Reshape for stacked chart
        melted_int = pd.melt(
            intensity_df,
            id_vars=["team_name", "total_top10_presences"],
            value_vars=["flat_top10", "hilly_top10", "mountain_top10", "itt_top10"],
            var_name="stage_type",
            value_name="top10_count"
        )
        terrain_label_map = {
            "flat_top10": "Flat",
            "hilly_top10": "Hilly",
            "mountain_top10": "Mountain",
            "itt_top10": "ITT"
        }
        melted_int["terrain_name"] = melted_int["stage_type"].map(terrain_label_map)

        col_e14_1, col_e14_2 = st.columns([1, 1])
        with col_e14_1:
            e14_stack_mode = st.radio("Display Mode:", ["Total Top-10 Count", "100% Normalized Terrain Share"], horizontal=True)
        with col_e14_2:
            terrains_sel = st.multiselect("Filter Terrains:", ["Flat", "Hilly", "Mountain", "ITT"], default=["Flat", "Hilly", "Mountain", "ITT"])

        filtered_int = melted_int[melted_int["terrain_name"].isin(terrains_sel)].copy()

        # Primary Visualization: Stacked Bar Chart by Stage Type
        st.markdown("#### 📊 Top-10 Stage Presences by Team and Terrain")
        
        stack_param = "normalize" if e14_stack_mode == "100% Normalized Terrain Share" else "zero"
        x_title = "Share of Top-10 Presences (%)" if stack_param == "normalize" else "Top-10 Stage Presences"
        x_format = "%" if stack_param == "normalize" else "d"

        stacked_chart = alt.Chart(filtered_int).mark_bar().encode(
            y=alt.Y("team_name:N", sort="-x", title="Team"),
            x=alt.X("top10_count:Q", stack=stack_param, title=x_title, axis=alt.Axis(format=x_format)),
            color=alt.Color("terrain_name:N", title="Terrain Type", scale=alt.Scale(
                domain=["Flat", "Hilly", "Mountain", "ITT"],
                range=["#10b981", "#f59e0b", "#ef4444", "#6366f1"]
            )),
            tooltip=[
                alt.Tooltip("team_name:N", title="Team"),
                alt.Tooltip("terrain_name:N", title="Terrain"),
                alt.Tooltip("top10_count:Q", title="Top 10 Count")
            ]
        ).properties(height=460)

        st.altair_chart(stacked_chart, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 🔗 Drilldown to Specific Top-10 Finishes")
        drill_team = st.selectbox("Select Team for finish links:", options=intensity_df["team_name"].tolist(), index=0)
        drill_df = olap.get_team_top10_drilldown(drill_team)

        st.dataframe(
            drill_df,
            column_config={
                "stage_id": st.column_config.NumberColumn("Stage #", format="%d"),
                "stage_date": "Date",
                "stage_type": "Terrain",
                "rank": st.column_config.NumberColumn("Finish Rank", format="P%d"),
                "bib_number": "Bib",
                "rider_name": "Rider"
            },
            hide_index=True,
            use_container_width=True
        )

        with st.expander("📋 View Complete Team Top-10 Intensity Matrix Table"):
            st.dataframe(
                intensity_df,
                column_config={
                    "team_name": "Team",
                    "flat_top10": st.column_config.NumberColumn("Flat Top 10", format="%d"),
                    "hilly_top10": st.column_config.NumberColumn("Hilly Top 10", format="%d"),
                    "mountain_top10": st.column_config.NumberColumn("Mountain Top 10", format="%d"),
                    "itt_top10": st.column_config.NumberColumn("ITT Top 10", format="%d"),
                    "total_top10_presences": st.column_config.NumberColumn("Total Presences", format="%d")
                },
                hide_index=True,
                use_container_width=True
            )


# =============================================================================
# MODULE 5: NATIONS & OUTCOMES (E8, E9, E12)
# =============================================================================
elif menu == "🌍 Nations & Consistency (E8, E9, E12)":
    tab1, tab2, tab3 = st.tabs([
        "E8: Participation by Nation",
        "E9: National Outcomes & Honours",
        "E12: Consistency Near the Front"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: E8 (Category B: Hybrid Chart + Table)
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("E8. Participation by Nation")
        st.markdown("""
        Summarize national representation across the peloton—distinguishing **individual rider citizenship** 
        from **commercial team registration**—then drill down to examine each nation's roster.
        """)

        nation_part = olap.get_nation_participation()

        # Secondary Metrics Row
        n1, n2, n3, n4 = st.columns(4)
        with n1:
            st.metric("Represented Nations", len(nation_part), "Global Representation")
        with n2:
            fra_row = nation_part[nation_part["country_code"] == "FRA"].iloc[0]
            st.metric("Host Nation (France)", f"{fra_row['rider_count']} Riders", f"{fra_row['team_count']} French-Licensed Teams")
        with n3:
            bel_row = nation_part[nation_part["country_code"] == "BEL"].iloc[0]
            st.metric("Belgium", f"{bel_row['rider_count']} Riders", f"{bel_row['team_count']} Belgian Teams")
        with n4:
            non_eu_cnt = (nation_part["team_count"] == 0).sum()
            st.metric("Nations without Domestic Teams", f"{non_eu_cnt} Countries", "Riders on International Trade Squads")

        col_n_ctrl1, col_n_ctrl2 = st.columns([2, 1])
        with col_n_ctrl1:
            top_n_nations = st.slider("Display Top Nations in Bar Chart:", min_value=5, max_value=len(nation_part), value=15, step=1)

        # Primary Visualization: Ranked Horizontal Bar Chart showing Riders per Nation
        st.markdown("#### 🌍 Peloton Participation by Nation")
        sub_nat = nation_part.head(top_n_nations).copy()

        bar_nation = alt.Chart(sub_nat).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color="#2563eb").encode(
            y=alt.Y("country_name:N", sort=alt.EncodingSortField(field="rider_count", order="descending"), title="Country"),
            x=alt.X("rider_count:Q", title="Rider Count", axis=alt.Axis(tickMinStep=1)),
            tooltip=[
                alt.Tooltip("country_name:N", title="Country"),
                alt.Tooltip("country_code:N", title="Code"),
                alt.Tooltip("rider_count:Q", title="Riders"),
                alt.Tooltip("team_count:Q", title="Teams Based Here"),
                alt.Tooltip("pct_peloton:Q", title="Share of Peloton (%)")
            ]
        ).properties(height=max(280, top_n_nations * 22))

        label_nation = alt.Chart(sub_nat).mark_text(
            align="left", baseline="middle", dx=6, fontSize=11, color="#334155"
        ).encode(
            y=alt.Y("country_name:N", sort=alt.EncodingSortField(field="rider_count", order="descending")),
            x=alt.X("rider_count:Q"),
            text=alt.Text("rider_count:Q")
        )
        st.altair_chart(bar_nation + label_nation, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 🔍 Drilldown: National Roster & Commercial Squads")
        country_options = {f"{r['country_name']} ({r['country_code']}) — {r['rider_count']} riders": r["country_code"] for _, r in nation_part.iterrows()}
        selected_c_label = st.selectbox("Choose Country to Open:", options=list(country_options.keys()), index=0)
        selected_ccode = country_options[selected_c_label]

        country_riders = olap.get_nation_riders(selected_ccode)

        st.markdown(f"""
        <div class="narrative-box" style="border-left-color: #3b82f6;">
            <h4>Athlete Nationality vs. Team Registration</h4>
            <p>Riders listed below compete under the flag of <strong>{selected_c_label.split(' — ')[0]}</strong>, though they may ride for trade squads registered in different countries.</p>
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(
            country_riders,
            column_config={
                "bib_number": "Bib",
                "rider_name": "Rider",
                "dob": "Date of Birth",
                "role": "Role",
                "is_leader": "Is Leader",
                "team_name": "Commercial Trade Squad",
                "status": "Race Status"
            },
            hide_index=True,
            use_container_width=True
        )

        with st.expander("📋 View Complete Nation Participation Summary Table"):
            st.dataframe(
                nation_part,
                column_config={
                    "country_code": "Code",
                    "country_name": "Country",
                    "team_count": st.column_config.NumberColumn("Teams", format="%d"),
                    "rider_count": st.column_config.NumberColumn("Riders", format="%d"),
                    "pct_peloton": st.column_config.NumberColumn("Share of Peloton", format="%.1f%%")
                },
                hide_index=True,
                use_container_width=True
            )

    # -------------------------------------------------------------------------
    # TAB 2: E9 (Category A: Chart-First)
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("E9. National Outcomes within Available Data")
        st.markdown("""
        Compare national participation against tangible outcomes—**stage wins**, **stage podiums**, 
        and **best final GC rank**—to contrast peloton size with athletic efficiency.
        """)

        outcomes_df = olap.get_national_outcomes()

        # Primary Visualization: Bubble Scatter Plot
        st.markdown("#### 🫧 National Participation vs. Stage Podium Performance")
        st.caption("Top-left bubble position indicates exceptional athletic efficiency (high podium conversion relative to peloton size).")

        bubble_e9 = alt.Chart(outcomes_df).mark_circle().encode(
            x=alt.X("rider_count:Q", title="National Rider Count (Participation)", axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("stage_podiums:Q", title="Stage Podiums (Top 3 Finishes)", axis=alt.Axis(tickMinStep=1)),
            size=alt.Size("stage_wins:Q", title="Stage Wins (1st)", scale=alt.Scale(range=[120, 600])),
            color=alt.Color("best_gc_rank:Q", scale=alt.Scale(scheme="viridis", reverse=True), title="Best Final GC Rank"),
            tooltip=[
                alt.Tooltip("country_name:N", title="Nation"),
                alt.Tooltip("country_code:N", title="Code"),
                alt.Tooltip("rider_count:Q", title="Riders"),
                alt.Tooltip("stage_wins:Q", title="Stage Wins"),
                alt.Tooltip("stage_podiums:Q", title="Stage Podiums"),
                alt.Tooltip("stage_top10s:Q", title="Stage Top 10s"),
                alt.Tooltip("best_gc_rank_str:N", title="Best Final GC")
            ]
        ).properties(height=400)

        # Highlight labels on distinctive nations
        labeled_nations = outcomes_df[outcomes_df["country_code"].isin(["SLO", "BEL", "DEN", "FRA", "NED", "ITA", "AUS", "GBR"])].copy()
        labels_e9 = alt.Chart(labeled_nations).mark_text(
            align="left", baseline="middle", dx=10, fontSize=11, fontWeight="bold", color="#1e293b"
        ).encode(
            x="rider_count:Q",
            y="stage_podiums:Q",
            text="country_name:N"
        )

        st.altair_chart(bubble_e9 + labels_e9, use_container_width=True)

        st.markdown("""
        <div class="narrative-box">
            <h4>💡 National Efficiency Contrasts</h4>
            <p>• <strong>Slovenia:</strong> Only 5 riders in the peloton, yet captured <strong>4 Stage Wins, 11 Podiums</strong>, and the <strong>Yellow Jersey (Pogacar)</strong>—unmatched podium efficiency.<br>
            • <strong>Belgium & Denmark:</strong> Converted compact squads into 4 and 2 stage wins respectively, with Remco Evenepoel, Wout Van Aert, and Jonas Vingegaard.<br>
            • <strong>France:</strong> Largest contingent with 32 riders and 33 top-10 finishes, demonstrating collective depth across stages.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🔗 Pathway to Contributing Stages & Athletes")
        sel_c_out = st.selectbox("Inspect Stage Outcomes for Nation:", options=sorted(outcomes_df["country_name"].unique()), index=sorted(outcomes_df["country_name"].unique()).index("Slovenia") if "Slovenia" in outcomes_df["country_name"].unique() else 0)
        c_code_sel = outcomes_df[outcomes_df["country_name"] == sel_c_out]["country_code"].iloc[0]

        q_pathway = """
        SELECT 
            s.stage_id,
            s.stage_date,
            s.stage_type,
            r.rank,
            rd.bib_number,
            rd.rider_name,
            rd.team_name,
            r.finish_time,
            r.bonus,
            r.penalty,
            r.adj_time
        FROM result_with_adj_time r
        JOIN stage s ON r.stage_id = s.stage_id
        JOIN rider rd ON r.bib_number = rd.bib_number
        WHERE rd.country_code = ? AND r.rank <= 3
        ORDER BY s.stage_id ASC, r.rank ASC;
        """
        pathway_df = execute_query(q_pathway, (c_code_sel,))
        if not pathway_df.empty:
            pathway_df["adj_time_formatted"] = pathway_df["adj_time"].apply(format_seconds)
            st.dataframe(
                pathway_df[["stage_id", "stage_date", "stage_type", "rank", "bib_number", "rider_name", "team_name", "adj_time_formatted"]],
                column_config={
                    "stage_id": st.column_config.NumberColumn("Stage #", format="%d"),
                    "stage_date": "Date",
                    "stage_type": "Terrain",
                    "rank": st.column_config.NumberColumn("Finish Rank", format="P%d"),
                    "bib_number": "Bib",
                    "rider_name": "Rider",
                    "team_name": "Team",
                    "adj_time_formatted": "Adjusted Time"
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info(f"No stage podiums (top 3) recorded for {sel_c_out}.")

        with st.expander("📋 View National Outcomes Summary Table"):
            st.dataframe(
                outcomes_df[[
                    "country_code", "country_name", "rider_count", "best_gc_rank_str", "stage_wins", "stage_podiums", "stage_top10s"
                ]],
                column_config={
                    "country_code": "Code",
                    "country_name": "Nation",
                    "rider_count": st.column_config.NumberColumn("Riders", format="%d"),
                    "best_gc_rank_str": "Best Final GC Rank",
                    "stage_wins": st.column_config.NumberColumn("Stage Wins (1st)", format="%d"),
                    "stage_podiums": st.column_config.NumberColumn("Stage Podiums (Top 3)", format="%d"),
                    "stage_top10s": st.column_config.NumberColumn("Top 10 Finishes", format="%d")
                },
                hide_index=True,
                use_container_width=True
            )

    # -------------------------------------------------------------------------
    # TAB 3: E12 (Category A: Chart-First)
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("E12. Consistency Near the Front")
        st.markdown("""
        From the space of high finishes, identify riders who most frequently appear in the top ten, 
        and inspect their stage-by-stage consistency fingerprint across all 21 stages.
        """)

        col_e12_ctrl1, _ = st.columns([1, 1])
        with col_e12_ctrl1:
            top_n_cons = st.slider("Display Consistent Contenders:", min_value=10, max_value=25, value=15, step=5)

        consistency_df = olap.get_consistency_ranking(top_n_cons)
        matrix_df = olap.get_top10_consistency_matrix(top_n_cons)

        # Primary Visualization: Rider x Stage Heatmap
        st.markdown(f"#### 🏁 Rider × Stage Consistency Heatmap (Top {top_n_cons} Consistent Riders across 21 Stages)")
        st.caption("Numbers indicate top-10 finish ranks; colored tiles highlight wins, podiums, and top-ten presences.")

        rect_e12 = alt.Chart(matrix_df).mark_rect(cornerRadius=2).encode(
            x=alt.X("stage_id:O", title="Stage Number (1–21)"),
            y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="top10_count", op="max", order="descending"), title="Contender"),
            color=alt.Color("finish_category:N", scale=alt.Scale(
                domain=["1st (Win)", "2nd-3rd (Podium)", "4th-10th (Top 10)", "> 10th", "DNS/DNF"],
                range=["#eab308", "#3b82f6", "#10b981", "#f1f5f9", "#94a3b8"]
            ), title="Stage Outcome"),
            tooltip=[
                alt.Tooltip("rider_name:N", title="Rider"),
                alt.Tooltip("team_name:N", title="Team"),
                alt.Tooltip("stage_id:O", title="Stage #"),
                alt.Tooltip("stage_type:N", title="Terrain"),
                alt.Tooltip("stage_rank:Q", title="Stage Rank"),
                alt.Tooltip("finish_category:N", title="Category")
            ]
        ).properties(height=max(320, top_n_cons * 24))

        # Text overlay showing stage rank for top-10 finishes
        sub_top10 = matrix_df[matrix_df["stage_rank"] <= 10].copy()
        sub_top10["stage_rank_int"] = sub_top10["stage_rank"].astype(int)
        
        text_e12 = alt.Chart(sub_top10).mark_text(fontSize=10, fontWeight="bold", color="white").encode(
            x="stage_id:O",
            y=alt.Y("rider_name:N", sort=alt.EncodingSortField(field="top10_count", op="max", order="descending")),
            text=alt.Text("stage_rank_int:Q")
        )

        st.altair_chart(rect_e12 + text_e12, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 📋 Contributing Stages for Consistent Riders")
        cons_dict = {f"Bib {r['bib_number']} - {r['rider_name']} ({r['team_name']}) — {r['top10_finishes_count']} top-10s": r["bib_number"] for _, r in consistency_df.iterrows()}
        sel_cons_rider = st.selectbox("Select Rider to View Contributing Stages:", options=list(cons_dict.keys()), index=0)
        cons_bib = cons_dict[sel_cons_rider]

        contrib_df = olap.get_rider_contributing_stages(cons_bib)
        st.dataframe(
            contrib_df,
            column_config={
                "stage_id": st.column_config.NumberColumn("Stage #", format="%d"),
                "stage_date": "Date",
                "stage_type": "Terrain",
                "distance_km": st.column_config.NumberColumn("Km", format="%.1f"),
                "route": "Route",
                "rank": st.column_config.NumberColumn("Finish Rank", format="P%d"),
                "adj_time_formatted": "Adjusted Time"
            },
            hide_index=True,
            use_container_width=True
        )

        with st.expander("📋 View Full Consistency Ranking Summary Table"):
            st.dataframe(
                consistency_df,
                column_config={
                    "bib_number": "Bib",
                    "rider_name": "Rider",
                    "team_name": "Team",
                    "country_code": "Nat",
                    "top10_finishes_count": st.column_config.NumberColumn("Top-10 Finishes", format="%d"),
                    "avg_rank_in_top10": st.column_config.NumberColumn("Avg Rank in Top 10", format="%.1f"),
                    "best_finish": st.column_config.NumberColumn("Best Finish", format="P%d")
                },
                hide_index=True,
                use_container_width=True
            )


# =============================================================================
# MODULE 6: DATA WAREHOUSE & SQL STUDIO
# =============================================================================
elif menu == "🗄️ SQL Studio & Schema":
    st.header("Relational Database Schema & Interactive SQL Studio")

    st.markdown("""
    This analytics platform is built directly on the **relational schema and BCNF normalized design** 
    developed by Group 39 for the Tour de France database system (`tdf.db` / `data.sql`).
    """)

    sub_t1, sub_t2, sub_t3 = st.tabs([
        "💻 Interactive SQL Console",
        "📐 Relational Schema & BCNF",
        "📁 Live Table Browser"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: SQL Console
    # -------------------------------------------------------------------------
    with sub_t1:
        st.subheader("Interactive SQL Query Console")
        st.markdown("Execute custom SQL queries directly against `tdf.db`. Test multidimensional aggregations, window functions, and OLAP rolls.")

        sample_queries = {
            "Top 10 General Classification (Window Function)": """
SELECT 
    r.bib_number,
    rd.rider_name,
    rd.team_name,
    SUM(r.adj_time) AS total_adj_time,
    RANK() OVER (ORDER BY SUM(r.adj_time) ASC) AS gc_rank
FROM result_with_adj_time r
JOIN rider rd ON r.bib_number = rd.bib_number
GROUP BY r.bib_number
HAVING COUNT(r.stage_id) = 21
ORDER BY gc_rank ASC
LIMIT 10;
            """.strip(),

            "Stage Type Distribution & Total Kilometres": """
SELECT 
    stage_type,
    COUNT(stage_id) AS stage_count,
    ROUND(SUM(distance_km), 1) AS total_km,
    ROUND(AVG(distance_km), 1) AS avg_stage_km
FROM stage
GROUP BY stage_type
ORDER BY total_km DESC;
            """.strip(),

            "Rider Exits by Stage and Reason": """
SELECT 
    e.stage_id,
    s.stage_type,
    e.bib_number,
    rd.rider_name,
    rd.team_name,
    e.reason
FROM exit e
JOIN rider rd ON e.bib_number = rd.bib_number
JOIN stage s ON e.stage_id = s.stage_id
ORDER BY e.stage_id ASC;
            """.strip(),

            "Top 5 Squads by Cumulative Active Finishing Time": """
SELECT 
    t.team_name,
    t.country_code,
    COUNT(DISTINCT rd.bib_number) AS starting_riders,
    SUM(r.adj_time) AS aggregate_time_seconds,
    ROUND(SUM(r.adj_time) / 3600.0, 1) AS aggregate_hours
FROM team t
JOIN rider rd ON t.team_name = rd.team_name
JOIN result_with_adj_time r ON rd.bib_number = r.bib_number
GROUP BY t.team_name
ORDER BY aggregate_time_seconds ASC
LIMIT 5;
            """.strip()
        }

        selected_sample = st.selectbox("Select a Sample Query or write your own below:", options=list(sample_queries.keys()))
        sql_input = st.text_area("SQL Statement:", value=sample_queries[selected_sample], height=160)

        if st.button("🚀 Run Query", type="primary"):
            try:
                t0 = time.time()
                res_df = execute_query(sql_input)
                elapsed = time.time() - t0
                st.success(f"Query returned {len(res_df)} rows in {elapsed*1000:.1f} ms")
                st.dataframe(res_df, use_container_width=True)
                
                # Download CSV
                csv_bytes = res_df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download Query Result as CSV", data=csv_bytes, file_name="query_result.csv", mime="text/csv")
            except Exception as e:
                st.error(f"SQL Execution Error: {str(e)}")

    # -------------------------------------------------------------------------
    # TAB 2: Schema & BCNF
    # -------------------------------------------------------------------------
    with sub_t2:
        st.subheader("Relational Database Schema & BCNF Normalization")
        st.markdown("""
        ### Relational Model Design (Table 1 from Project 2)
        - **`COUNTRY`** (`country_code`, `country_name`): PK is `country_code`.
        - **`TEAM`** (`team_name`, `country_code`): PK is `team_name`; FK `country_code` $\\rightarrow$ `COUNTRY`.
        - **`RIDER`** (`bib_number`, `rider_name`, `dob`, `role`, `is_leader`, `team_name`, `country_code`): PK is `bib_number`; FKs to `TEAM` and `COUNTRY`. Exactly one rider per team has `is_leader = TRUE`.
        - **`LOCATION`** (`location_name`, `country_code`): PK is `location_name`; FK to `COUNTRY`.
        - **`STAGE`** (`stage_id`, `stage_date`, `distance_km`, `stage_type`, `start_location`, `finish_location`): PK is `stage_id`; FKs to `LOCATION`.
        - **`RESULT`** (`bib_number`, `stage_id`, `rank`, `finish_time`, `bonus`, `penalty`): Composite PK (`bib_number`, `stage_id`).
        - **`RESULT_WITH_ADJ_TIME`** (View): Calculates derived attribute `adj_time = finish_time - bonus + penalty` dynamically to maintain 3NF/BCNF.
        - **`EXIT`** (`bib_number`, `stage_id`, `reason`): PK is `bib_number`. A rider exits at most once.
        - **`AWARD`** (`award_id`, `award_name`, `bib_number`, `team_name`): PK is `award_id`; XOR check ensures award belongs to either a rider OR a team.

        ### Normalization Justification
        All relations satisfy **1NF** (atomic values), **2NF** (no partial dependencies on composite keys), and **BCNF** 
        (the determinant of every functional dependency in the minimal cover is a candidate key).
        """)

    # -------------------------------------------------------------------------
    # TAB 3: Table Browser
    # -------------------------------------------------------------------------
    with sub_t3:
        st.subheader("Live Table Browser")
        tables_list = ["country", "team", "rider", "location", "stage", "result", "result_with_adj_time", "exit", "award"]
        chosen_table = st.selectbox("Select Table / View to Browse:", options=tables_list, index=2)
        
        preview_df = execute_query(f"SELECT * FROM {chosen_table} LIMIT 100;")
        count_val = execute_query(f"SELECT COUNT(*) AS cnt FROM {chosen_table};").iloc[0]["cnt"]
        
        st.caption(f"Showing up to 100 rows of **{count_val}** total records in `{chosen_table}`.")
        st.dataframe(preview_df, use_container_width=True)

# -----------------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 0.85rem; padding: 15px 0;">
    Tour de France Multidimensional OLAP System • BT5110 Data Management & Warehousing • Group 39 (Sharon, Keerthivasan, Louise, Sulistyo)
</div>
""", unsafe_allow_html=True)
