import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np

df_res = pd.read_csv("references/individual_results.csv", encoding="utf-8")
df_riders = pd.read_csv("references/riders.csv", encoding="utf-8")
df_exits = pd.read_csv("references/exits.csv", encoding="utf-8")

# Map stages
stages = df_res[["day", "start_location", "finish_location", "length", "type"]].drop_duplicates().sort_values("day").reset_index(drop=True)
stages["stage_id"] = stages.index + 1
df_res = df_res.merge(stages[["day", "stage_id"]], on="day")
df_res["adj_time"] = df_res["time"] - df_res["bonus"] + df_res["penalty"]

print("=== DATA SUMMARY ===")
print(f"Riders: {len(df_riders)}, Results: {len(df_res)}, Stages: {len(stages)}, Exits: {len(df_exits)}")

# GC after stage 21
stage_counts = df_res.groupby("rider")["stage_id"].count()
finishers = stage_counts[stage_counts == 21].index

gc = df_res[df_res["rider"].isin(finishers)].groupby(["rider", "name", "team"]).agg(
    total_time=("time", "sum"),
    total_bonus=("bonus", "sum"),
    total_penalty=("penalty", "sum"),
    total_adj_time=("adj_time", "sum")
).reset_index().sort_values("total_adj_time").reset_index(drop=True)
gc["gc_rank"] = gc.index + 1

def fmt(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    return f"{h:02d}h {m:02d}m {sec:02d}s"

print("\n--- GC TOP 10 ---")
winner_t = gc.loc[0, "total_adj_time"]
for i, r in gc.head(10).iterrows():
    gap = r["total_adj_time"] - winner_t
    gap_str = "-" if gap == 0 else f"+{fmt(gap)}"
    print(f"{r['gc_rank']:2d}. Bib {r['rider']:3d} | {r['name']:<22} | {r['team']:<25} | {fmt(r['total_adj_time'])} ({gap_str}) | -{r['total_bonus']}s / +{r['total_penalty']}s")

print("\n--- E1. Contextual Descent for Contender (e.g. Bib 1, 11, 72) ---")
# Check stage by stage GC rank and time gap
for bib in [1, 11, 72]:
    r_res = df_res[df_res["rider"] == bib].sort_values("stage_id")
    print(f"Rider {bib} ({r_res['name'].iloc[0]}): Stage ranks: {r_res['rank'].tolist()[:10]}...")

print("\n--- E4. Young Rider & Mountain Proxy ---")
df_riders["dob"] = pd.to_datetime(df_riders["dob"])
young_bibs = set(df_riders[df_riders["dob"] >= "2000-01-01"]["bib"])
gc_young = gc[gc["rider"].isin(young_bibs)].reset_index(drop=True)
gc_young["young_rank"] = gc_young.index + 1
print("Top 5 Young Riders:")
for i, r in gc_young.head(5).iterrows():
    print(f"YR {r['young_rank']}: GC Rank {r['gc_rank']} - {r['name']} ({r['team']})")

# Mountain GC proxy
mtn_stages = stages[stages["type"] == "mountain"]["stage_id"].tolist()
gc_mtn = df_res[df_res["stage_id"].isin(mtn_stages) & df_res["rider"].isin(finishers)].groupby(["rider", "name", "team"]).agg(
    mtn_adj_time=("adj_time", "sum")
).reset_index().sort_values("mtn_adj_time").reset_index(drop=True)
gc_mtn["mtn_rank"] = gc_mtn.index + 1
merged_proxies = gc[["rider", "name", "gc_rank"]].merge(gc_mtn[["rider", "mtn_rank"]], on="rider")
merged_proxies["divergence"] = merged_proxies["gc_rank"] - merged_proxies["mtn_rank"]
print("\nTop 5 Mountain Proxy Divergences (where Mountain rank differs from GC rank):")
print(merged_proxies.head(10))

print("\n--- E7. Counterfactual GC (Without Bonus, Without Penalty) ---")
gc_nobonus = df_res[df_res["rider"].isin(finishers)].groupby("rider").agg(
    cf_time=("time", lambda x: (x + df_res.loc[x.index, "penalty"]).sum())
).reset_index().sort_values("cf_time").reset_index(drop=True)
gc_nobonus["cf_nobonus_rank"] = gc_nobonus.index + 1

cf_merged = gc[["rider", "name", "gc_rank", "total_bonus", "total_penalty"]].merge(
    gc_nobonus[["rider", "cf_nobonus_rank"]], on="rider"
)
cf_merged["rank_change_no_bonus"] = cf_merged["gc_rank"] - cf_merged["cf_nobonus_rank"]
shifts = cf_merged[cf_merged["rank_change_no_bonus"] != 0]
print(f"Riders whose rank changes if bonuses removed: {len(shifts)}")
print(shifts.head(10))

print("\n--- E11. ITT stages ---")
itt_stages = stages[stages["type"] == "individual time-trial"]
print(itt_stages)
for sid in itt_stages["stage_id"]:
    w = df_res[(df_res["stage_id"] == sid) & (df_res["rank"] == 1)].iloc[0]
    print(f"Stage {sid}: Winner {w['name']} ({w['team']}), Time: {fmt(w['adj_time'])}")
