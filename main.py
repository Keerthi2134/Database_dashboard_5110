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
    # TAB 1: E1
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("E1. General Classification Leaderboard with Contextual Descent")
        st.markdown("""
        Begin from the overall General Classification, ordered by lowest cumulative $\sum \\text{adjusted\_time}$. 
        Select any contender to follow their trajectory down to the stage grain, surfacing the **single pivotal day** that most altered their race.
        """)

        gc_df = olap.get_gc_leaderboard(21)
        
        # Leaderboard Top Table
        col_ctrl1, col_ctrl2 = st.columns([2, 1])
        with col_ctrl1:
            team_filter = st.multiselect("Filter by Team:", options=sorted(gc_df["team_name"].unique()), default=[])
        with col_ctrl2:
            top_n = st.slider("Display Top N Riders:", min_value=5, max_value=160, value=15, step=5)

        filtered_gc = gc_df.copy()
        if team_filter:
            filtered_gc = filtered_gc[filtered_gc["team_name"].isin(team_filter)]

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

        # Stage Descent Data
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

        # Stage Progression Chart
        rank_chart = alt.Chart(descent_df).mark_line(point=True, color="#2563eb", strokeWidth=3).encode(
            x=alt.X("stage_id:O", title="Stage Number"),
            y=alt.Y("gc_rank_stage:Q", title="Progressive GC Rank (Inverted)", scale=alt.Scale(reverse=True, zero=False)),
            tooltip=[
                alt.Tooltip("stage_id:O", title="Stage"),
                alt.Tooltip("stage_type:N", title="Terrain"),
                alt.Tooltip("stage_rank:Q", title="Daily Finish"),
                alt.Tooltip("gc_rank_stage:Q", title="GC Rank"),
                alt.Tooltip("gap_formatted:N", title="Gap to Leader")
            ]
        ).properties(
            title=f"GC Rank Evolution across 21 Stages - {selected_label}",
            height=280
        )
        st.altair_chart(rank_chart, use_container_width=True)

        # Detailed Daily Descent Table
        st.markdown("#### Full Daily Stage Breakdown")
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
    # TAB 2: E4
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("E4. Parallel Classifications & Mountain-Stage Proxy")
        st.markdown("""
        Place side-by-side a rider's **overall GC rank** and their **Young Rider GC rank** (filtered at race start for riders born $\ge$ 2000-01-01).
        Introduce a **Mountain-Stage GC Proxy** (accumulating adjusted time only on Mountain stages) and surface key divergences.
        """)

        parallel_df = olap.get_parallel_classifications()

        # Summary KPIs
        pk1, pk2, pk3 = st.columns(3)
        with pk1:
            st.metric("Total 21-Stage Finishers", len(parallel_df))
        with pk2:
            st.metric("Young Rider Contenders", len(parallel_df.dropna(subset=["young_rank"])))
        with pk3:
            st.metric("Mountain Stages Included", "6 High Mountain Stages")

        st.markdown("#### Parallel Standings Table")
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

        st.markdown("---")
        st.markdown("#### ⛰️ Mountain Proxy Divergence Analysis")
        st.markdown("""
        **Positive Divergence (+):** Rider excels in mountains (e.g. pure climber whose mountain rank is higher than overall GC due to losses on flat/ITT stages).  
        **Negative Divergence (−):** Rider excels on flat/ITT terrains but loses time in the high mountains.
        """)

        # Scatter Chart of GC Rank vs Mountain Proxy Rank
        scatter_chart = alt.Chart(parallel_df).mark_circle(size=80).encode(
            x=alt.X("gc_rank:Q", title="Overall GC Rank"),
            y=alt.Y("mtn_proxy_rank:Q", title="Mountain Proxy Rank"),
            color=alt.Color("mtn_gc_divergence:Q", scale=alt.Scale(scheme="redblue", domainMid=0), title="Divergence"),
            tooltip=["rider_name", "team_name", "gc_rank", "mtn_proxy_rank", "mtn_gc_divergence"]
        ).properties(
            title="Overall GC Rank vs. Mountain-Stage Proxy Rank (Diagonal = Perfect Parity)",
            height=380
        )

        # Diagonal line
        line_parity = alt.Chart(pd.DataFrame({'x': [1, 160], 'y': [1, 160]})).mark_line(color="gray", strokeDash=[4, 4]).encode(
            x='x:Q',
            y='y:Q'
        )

        st.altair_chart(scatter_chart + line_parity, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 3: E7
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("E7. Bonuses, Penalties, and Counterfactual GC Replay")
        st.markdown("""
        Lay out cumulative bonuses and penalties per rider. Replay the GC leaderboard under **counterfactual toggles** 
        (removing bonuses, removing penalties, or reverting to raw elapsed time) to illuminate movements into and out of the top ten.
        """)

        cf_stage = st.slider("Select Stage Grain for Counterfactual Analysis:", min_value=1, max_value=21, value=21, step=1)
        cf_df = olap.get_counterfactual_gc(cf_stage)

        col_cf1, col_cf2 = st.columns([1, 1])
        with col_cf1:
            st.metric("Riders Awarded Time Bonuses (10s/6s/4s)", int((cf_df["total_bonus"] > 0).sum()))
        with col_cf2:
            st.metric("Riders Assessed Time Penalties", int((cf_df["total_penalty"] > 0).sum()))

        st.markdown("#### Counterfactual Leaderboard & Rank Displacements")
        
        # Display comparison table
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

        st.markdown("""
        <div class="narrative-box">
            <h4>💡 Counterfactual Takeaways</h4>
            <p>• <strong>Bonus Insulation:</strong> Tadej Pogacar accumulated <strong>52 seconds</strong> in sprint/stage win bonuses, shielding his GC buffer ahead of Jonas Vingegaard (34 bonus seconds).<br>
            • <strong>Penalty Impact:</strong> Penalties (e.g. 10s assessed to Jordan Jegat and Jonathan Milan, 20s to Paul Penhoet) demonstrate the strict enforcement of feed-zone and drafting regulations.<br>
            • Toggle between stage sliders above to observe how bonuses shifted the podium in tight stages!</p>
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # TAB 4: E10
    # -------------------------------------------------------------------------
    with tab4:
        st.subheader("E10. Temporal GC Storyline & Inflection Points")
        st.markdown("""
        Trace cumulative adjusted time gap to the leader after each stage for principal GC actors as an interactive line narrative.
        Inflection points denote pivotal moments where high mountains or individual time-trials reshuffled the leaderboard.
        """)

        # Default contenders: Top 6 GC contenders
        top_bibs = [1, 11, 72, 191, 151, 221, 31, 71]
        all_riders_df = execute_query("SELECT bib_number, rider_name, team_name FROM rider ORDER BY bib_number ASC;")
        rider_dict = {f"Bib {r['bib_number']} - {r['rider_name']} ({r['team_name']})": r["bib_number"] for _, r in all_riders_df.iterrows()}

        selected_labels = st.multiselect(
            "Select Contenders to Chart:",
            options=list(rider_dict.keys()),
            default=[k for k, v in rider_dict.items() if v in top_bibs]
        )
        selected_bibs = [rider_dict[k] for k in selected_labels]

        if selected_bibs:
            storyline_df = olap.get_temporal_gc_storyline(selected_bibs)
            
            # Interactive Multi-Line Gap Chart
            story_chart = alt.Chart(storyline_df).mark_line(point=True, strokeWidth=2.5).encode(
                x=alt.X("stage_id:O", title="Stage Number"),
                y=alt.Y("gap_to_leader:Q", title="Gap to GC Leader (Seconds)"),
                color=alt.Color("rider_name:N", title="Contender"),
                tooltip=[
                    alt.Tooltip("stage_id:O", title="Stage"),
                    alt.Tooltip("stage_type:N", title="Terrain"),
                    alt.Tooltip("rider_name:N", title="Rider"),
                    alt.Tooltip("gap_to_leader:Q", title="Gap (s)"),
                    alt.Tooltip("gc_rank:Q", title="GC Rank")
                ]
            ).properties(
                title="Time Gap to GC Leader across 21 Stages",
                height=420
            )
            st.altair_chart(story_chart, use_container_width=True)

            # Inflection Points Highlight
            st.markdown("""
            #### 📌 Key Race Inflection Points
            - **Stage 5 (Caen ITT, 33.0 km):** First major GC separator where Remco Evenepoel won and gaps opened by over a minute between time-trialists and pure climbers.
            - **Stage 10 (Le Mont-Dore Puy De Sancy, Mountain):** Hard summit finish in the Massif Central creating the first top-10 reshuffle.
            - **Stage 12 & 14 (Hautacam & Luchon-Superbagnères, Pyrenees):** Decisive mountain battles establishing Pogacar and Vingegaard's commanding lead.
            - **Stage 18 & 19 (Courchevel Col De La Loze & La Plagne, Alps):** Queen mountain stages solidifying the final podium positions.
            """)


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
    # TAB 1: E2
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("E2. A Stage in Focus: Vignette & Team Perspective")
        st.markdown("Treat one stage as an intensive vignette: examine leading finishers, terrain profile, and which squads populated the top ten.")

        selected_stage = st.selectbox("Select Stage (1 to 21):", options=list(range(1, 22)), index=11)
        vignette = olap.get_stage_vignette(selected_stage)

        # Vignette Header Card
        st.markdown(f"""
        <div class="narrative-box" style="border-left-color: #10b981;">
            <h4>🏁 Stage {vignette['stage_id']}: {vignette['start_location']} → {vignette['finish_location']}</h4>
            <p><strong>Date:</strong> {vignette['stage_date']} | <strong>Distance:</strong> {vignette['distance_km']} km | 
            <strong>Terrain:</strong> <span class="stage-pill stage-{vignette['stage_type'].replace(' ', '-')}">{vignette['stage_type'].upper()}</span></p>
        </div>
        """, unsafe_allow_html=True)

        col_st1, col_st2 = st.columns([3, 2])
        with col_st1:
            st.markdown("#### Leading Stage Finishers")
            finishers_df = olap.get_stage_finishers(selected_stage, top_n=12)
            st.dataframe(
                finishers_df[[
                    "rank", "bib_number", "rider_name", "team_name", "country_code", 
                    "time_formatted", "gap_formatted", "bonus", "penalty"
                ]],
                column_config={
                    "rank": st.column_config.NumberColumn("Pos", format="%d"),
                    "bib_number": "Bib",
                    "rider_name": "Rider",
                    "team_name": "Team",
                    "country_code": "Nat",
                    "time_formatted": "Adjusted Time",
                    "gap_formatted": "Gap",
                    "bonus": st.column_config.NumberColumn("Bonus", format="-%ds"),
                    "penalty": st.column_config.NumberColumn("Pen", format="+%ds")
                },
                hide_index=True,
                use_container_width=True
            )

        with col_st2:
            st.markdown("#### Team Representation in Top 10")
            team_persp = olap.get_stage_team_perspective(selected_stage, top_n=10)
            
            bar_team = alt.Chart(team_persp).mark_bar(color="#0284c7").encode(
                x=alt.X("top_finishers_count:Q", title="Count of Riders in Top 10"),
                y=alt.Y("team_name:N", sort="-x", title="Team"),
                tooltip=["team_name", "top_finishers_count", "riders_in_top_n"]
            ).properties(height=260)
            st.altair_chart(bar_team, use_container_width=True)

            st.dataframe(
                team_persp[["team_name", "top_finishers_count", "riders_in_top_n"]],
                column_config={
                    "team_name": "Team",
                    "top_finishers_count": st.column_config.NumberColumn("Top 10 Count", format="%d"),
                    "riders_in_top_n": "Riders & Finishes"
                },
                hide_index=True,
                use_container_width=True
            )

    # -------------------------------------------------------------------------
    # TAB 2: E5
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("E5. Mountain Contours: Podiums & Time Gaps to Winner")
        st.markdown("""
        Surface two distinct mountain-specific signals: **podium frequency on Mountain stages** and **mean time gap to the stage winner** on mountain terrain.
        Drill down to inspect the daily traces that produced these summaries.
        """)

        mtn_contours = olap.get_mountain_contours()

        st.dataframe(
            mtn_contours.head(15)[[
                "bib_number", "rider_name", "team_name", "mountain_stages_completed",
                "mountain_podium_count", "mean_gap_formatted", "best_mountain_rank"
            ]],
            column_config={
                "bib_number": "Bib",
                "rider_name": "Rider",
                "team_name": "Team",
                "mountain_stages_completed": st.column_config.NumberColumn("Stages Done", format="%d"),
                "mountain_podium_count": st.column_config.NumberColumn("Mountain Podiums (Top 3)", format="%d"),
                "mean_gap_formatted": "Mean Gap to Winner",
                "best_mountain_rank": st.column_config.NumberColumn("Best Finish", format="P%d")
            },
            hide_index=True,
            use_container_width=True
        )

        st.markdown("---")
        st.markdown("#### 🔍 Return to Daily Mountain Traces")
        rider_mtn_dict = {f"Bib {r['bib_number']} - {r['rider_name']} ({r['team_name']})": r["bib_number"] for _, r in mtn_contours.head(20).iterrows()}
        selected_mtn_rider = st.selectbox("Select rider for mountain trace review:", options=list(rider_mtn_dict.keys()))
        sel_mtn_bib = rider_mtn_dict[selected_mtn_rider]

        traces_df = olap.get_rider_mountain_traces(sel_mtn_bib)
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
                "rank": st.column_config.NumberColumn("Finish Rank", format="%d"),
                "adj_time_formatted": "Adjusted Time",
                "gap_formatted": "Gap to Stage Winner"
            },
            hide_index=True,
            use_container_width=True
        )

    # -------------------------------------------------------------------------
    # TAB 3: E6
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("E6. Speed Profiles as Simple Ratio (Distance / Time)")
        st.markdown("""
        Chart stage-type speed profiles using the proxy $\\text{km/h} = \\text{length\_km} / (\\text{time} / 3600)$ across **Flat, Hilly, Mountain, and ITT**.
        Emphasize riders and squads who gain significant relative advantage when terrain shifts away from Flat/Hilly toward Mountain.
        """)

        team_speeds = olap.get_team_speed_profile()

        # Team speed overview table
        pivot_speed = team_speeds.pivot(index="team_name", columns="stage_type", values="avg_speed_kmh").reset_index()
        pivot_speed["flat_to_mtn_ratio"] = (pivot_speed["mountain"] / pivot_speed["flat"] * 100.0).round(1)

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
    # TAB 4: E11
    # -------------------------------------------------------------------------
    with tab4:
        st.subheader("E11. Against the Clock: Individual Time Trial Catalogue")
        st.markdown("Surface the inventory of ITT stages and present their essentials—date, distance, winner, speed, and compact catalogue.")

        itt_df = olap.get_itt_catalogue()

        for _, row in itt_df.iterrows():
            st.markdown(f"""
            <div class="metric-card" style="border-left: 6px solid #4f46e5;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span class="stage-pill stage-itt">ITT STAGE {row['stage_id']}</span>
                        <h3 style="margin: 6px 0 2px 0;">{row['start_location']} → {row['finish_location']}</h3>
                        <div style="color: #64748b; font-size: 0.9rem;">{row['stage_date']} | <strong>{row['distance_km']} km</strong> against the clock</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.85rem; color: #64748b; font-weight: 600;">STAGE WINNER</div>
                        <div style="font-size: 1.3rem; font-weight: 800; color: #1e1b4b;">{row['winner_name']}</div>
                        <div style="font-size: 0.85rem; color: #475569;">{row['winner_team']}</div>
                        <div style="font-size: 1.05rem; font-weight: 700; color: #4338ca; margin-top: 4px;">{row['winning_time_formatted']} ({row['winner_speed_kmh']} km/h)</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("#### Full ITT Leaderboards")
        itt_stage_sel = st.radio("Inspect ITT Stage Leaderboard:", options=itt_df["stage_id"].tolist(), format_func=lambda x: f"Stage {x}")
        itt_finishers = olap.get_stage_finishers(itt_stage_sel, top_n=10)
        st.dataframe(
            itt_finishers[["rank", "bib_number", "rider_name", "team_name", "country_code", "time_formatted", "gap_formatted"]],
            hide_index=True,
            use_container_width=True
        )

    # -------------------------------------------------------------------------
    # TAB 5: E15
    # -------------------------------------------------------------------------
    with tab5:
        st.subheader("E15. The Long Day: Spotlight on Longest Routes")
        st.markdown("Sort all stages by distance to spotlight the longest route, its geographic profile, and leading finishers.")

        dist_stages = olap.get_stages_by_distance()
        longest = dist_stages.iloc[0]

        # Spotlight Card
        st.markdown(f"""
        <div class="narrative-box" style="border-left-color: #8b5cf6;">
            <h4>👑 The Long Day: Stage {longest['stage_id']} ({longest['distance_km']} km)</h4>
            <p><strong>Route:</strong> {longest['start_location']} → {longest['finish_location']} on {longest['stage_date']}<br>
            <strong>Terrain:</strong> {longest['stage_type'].title()}<br>
            <strong>Challenge:</strong> At {longest['distance_km']} km, this was the ultimate test of endurance in the opening week across northern France, requiring relentless bunch positioning over 4.5 hours of racing.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### Leading Finishers on the Longest Day")
        long_finishers = olap.get_stage_finishers(int(longest["stage_id"]), top_n=10)
        st.dataframe(
            long_finishers[["rank", "bib_number", "rider_name", "team_name", "country_code", "time_formatted", "gap_formatted"]],
            hide_index=True,
            use_container_width=True
        )

        st.markdown("#### All Stages Ranked by Distance")
        st.dataframe(
            dist_stages,
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
    # TAB 1: E3
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("E3. Team Burden and Contribution")
        st.markdown("""
        Roll up each team's aggregate adjusted time over the event, then open the aggregation to reveal 
        which riders carried the time load and how their per-stage profiles shaped the team's outcome.
        """)

        team_sum = olap.get_team_summary()
        
        st.markdown("#### Team Aggregate Standings (All 23 Squads)")
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
                "gap_to_lead_team": "Gap to Leader",
                "total_stage_results": "Total Results Count"
            },
            hide_index=True,
            use_container_width=True
        )

        st.markdown("---")
        st.markdown("### 🔍 Open Aggregation: Rider Burden Breakdown")
        
        sel_team_e3 = st.selectbox("Select a Team to inspect rider load:", options=team_sum["team_name"].tolist())
        burden_df = olap.get_team_rider_contributions(sel_team_e3)

        st.dataframe(
            burden_df[[
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

        # Burden Share Chart
        burden_chart = alt.Chart(burden_df).mark_bar().encode(
            x=alt.X("pct_team_burden:Q", title="Share of Team Total Adjusted Time (%)"),
            y=alt.Y("rider_name:N", sort="-x", title="Rider"),
            color=alt.Color("is_leader:N", scale=alt.Scale(domain=[1, 0], range=["#eab308", "#3b82f6"]), title="Is Leader"),
            tooltip=["rider_name", "role", "pct_team_burden", "time_formatted", "status"]
        ).properties(height=240, title=f"Time Burden Distribution - {sel_team_e3}")
        st.altair_chart(burden_chart, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 2: E13
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("E13. Depth of Squads & Attrition")
        st.markdown("""
        At the rider grain, portray team depth via distinct rider counts, highlighting squads with the broadest rosters
        and providing a doorway to their full rider lists and countries.
        """)

        squad_df = olap.get_squad_depth()

        st.dataframe(
            squad_df,
            column_config={
                "team_name": "Team",
                "country_code": "Country",
                "starting_riders": st.column_config.NumberColumn("Starting Roster", format="%d"),
                "active_finishers": st.column_config.NumberColumn("21-Stage Finishers", format="%d"),
                "exit_count": st.column_config.NumberColumn("Exits (DNS/Withdrawal)", format="%d"),
                "survival_rate_pct": st.column_config.NumberColumn("Survival Rate", format="%.1f%%")
            },
            hide_index=True,
            use_container_width=True
        )

        st.markdown("---")
        st.markdown("#### 🚪 Doorway to Full Squad Rosters")
        door_team = st.selectbox("Select Team to Inspect Full Roster:", options=squad_df["team_name"].tolist())
        roster_df = olap.get_team_roster(door_team)

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

    # -------------------------------------------------------------------------
    # TAB 3: E14
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("E14. Top-Ten Intensity by Team across Terrains")
        st.markdown("""
        Aggregate top-ten presences at the team level broken down by stage type (Flat, Hilly, Mountain, ITT);
        pair the totals with links back to the specific stages and riders involved.
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
        melted_int["stage_type"] = melted_int["stage_type"].str.replace("_top10", "").str.upper()

        stacked_chart = alt.Chart(melted_int).mark_bar().encode(
            x=alt.X("top10_count:Q", title="Top 10 Presences"),
            y=alt.Y("team_name:N", sort="-x", title="Team"),
            color=alt.Color("stage_type:N", title="Terrain", scale=alt.Scale(
                domain=["FLAT", "HILLY", "MOUNTAIN", "ITT"],
                range=["#22c55e", "#eab308", "#ef4444", "#6366f1"]
            )),
            tooltip=["team_name", "stage_type", "top10_count"]
        ).properties(title="Top-10 Stage Presences by Team and Terrain", height=440)

        st.altair_chart(stacked_chart, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 🔗 Drilldown to Specific Top-10 Finishes")
        drill_team = st.selectbox("Select Team for finish links:", options=intensity_df["team_name"].tolist())
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
    # TAB 1: E8
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("E8. Participation by Nation")
        st.markdown("""
        Summarize nations by their presence—count of teams and count of riders—then open the roll-up 
        to list the riders and their associated teams for a chosen country.
        """)

        nation_part = olap.get_nation_participation()

        col_n1, col_n2 = st.columns([3, 2])
        with col_n1:
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

        with col_n2:
            nation_bar = alt.Chart(nation_part.head(10)).mark_bar(color="#3b82f6").encode(
                x=alt.X("rider_count:Q", title="Riders Count"),
                y=alt.Y("country_name:N", sort="-x", title="Country"),
                tooltip=["country_name", "rider_count", "team_count", "pct_peloton"]
            ).properties(title="Top 10 Nations by Rider Count", height=320)
            st.altair_chart(nation_bar, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 🔍 Open the Roll-up: Country Squad Inspection")
        country_options = {f"{r['country_name']} ({r['country_code']})": r["country_code"] for _, r in nation_part.iterrows()}
        selected_c_label = st.selectbox("Choose Country to Open:", options=list(country_options.keys()))
        selected_ccode = country_options[selected_c_label]

        country_riders = olap.get_nation_riders(selected_ccode)
        st.dataframe(
            country_riders,
            column_config={
                "bib_number": "Bib",
                "rider_name": "Rider",
                "dob": "DOB",
                "role": "Role",
                "is_leader": "Is Leader",
                "team_name": "Team",
                "status": "Race Status"
            },
            hide_index=True,
            use_container_width=True
        )

    # -------------------------------------------------------------------------
    # TAB 2: E9
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("E9. National Outcomes within Available Data")
        st.markdown("""
        For each nation, note the **best GC rank** achieved by its riders and tally **stage wins and podiums**;
        keep the pathway back to the underlying stages and athletes clear.
        """)

        outcomes_df = olap.get_national_outcomes()

        st.dataframe(
            outcomes_df[[
                "country_code", "country_name", "best_gc_rank_str", "stage_wins", "stage_podiums", "stage_top10s"
            ]],
            column_config={
                "country_code": "Code",
                "country_name": "Nation",
                "best_gc_rank_str": "Best Final GC Rank",
                "stage_wins": st.column_config.NumberColumn("Stage Wins (1st)", format="%d"),
                "stage_podiums": st.column_config.NumberColumn("Stage Podiums (Top 3)", format="%d"),
                "stage_top10s": st.column_config.NumberColumn("Top 10 Finishes", format="%d")
            },
            hide_index=True,
            use_container_width=True
        )

        st.markdown("---")
        st.markdown("#### 🔗 Pathway to Contributing Stages & Athletes")
        sel_c_out = st.selectbox("Inspect Stage Outcomes for Nation:", options=sorted(outcomes_df["country_name"].unique()))
        c_code_sel = outcomes_df[outcomes_df["country_name"] == sel_c_out]["country_code"].iloc[0]

        q_pathway = """
        SELECT 
            s.stage_id,
            s.stage_date,
            s.stage_type,
            r.rank,
            rd.bib_number,
            rd.rider_name,
            rd.team_name
        FROM result_with_adj_time r
        JOIN stage s ON r.stage_id = s.stage_id
        JOIN rider rd ON r.bib_number = rd.bib_number
        WHERE rd.country_code = ? AND r.rank <= 3
        ORDER BY s.stage_id ASC, r.rank ASC;
        """
        pathway_df = execute_query(q_pathway, (c_code_sel,))
        if not pathway_df.empty:
            st.dataframe(pathway_df, hide_index=True, use_container_width=True)
        else:
            st.info(f"No stage podiums (top 3) recorded for {sel_c_out}.")

    # -------------------------------------------------------------------------
    # TAB 3: E12
    # -------------------------------------------------------------------------
    with tab3:
        st.subheader("E12. Consistency Near the Front")
        st.markdown("""
        From the space of high finishes, identify the riders who most often appear in the top ten;
        accompany the summary with the list of contributing stages, their ranks, and stage types.
        """)

        consistency_df = olap.get_consistency_ranking(15)

        st.dataframe(
            consistency_df,
            column_config={
                "bib_number": "Bib",
                "rider_name": "Rider",
                "team_name": "Team",
                "country_code": "Nat",
                "top10_finishes_count": st.column_config.NumberColumn("Top-10 Finishes Count", format="%d"),
                "avg_rank_in_top10": st.column_config.NumberColumn("Avg Rank in Top 10", format="%.1f"),
                "best_finish": st.column_config.NumberColumn("Best Finish", format="P%d")
            },
            hide_index=True,
            use_container_width=True
        )

        st.markdown("---")
        st.markdown("#### 📋 Contributing Stages for Consistent Riders")
        cons_dict = {f"Bib {r['bib_number']} - {r['rider_name']} ({r['team_name']})": r["bib_number"] for _, r in consistency_df.iterrows()}
        sel_cons_rider = st.selectbox("Select Rider to View Contributing Stages:", options=list(cons_dict.keys()))
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
