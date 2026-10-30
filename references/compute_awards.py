import sys
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd

df = pd.read_csv("references/individual_results.csv", encoding="utf-8")
df["adj_time"] = df["time"] - df["bonus"] + df["penalty"]

# Stage winners
stage_winners = df[df["rank"] == 1].sort_values("day").reset_index(drop=True)
print("=== 21 STAGE WINNERS ===")
for i, r in stage_winners.iterrows():
    print(f"Stage {i+1:2d} ({r['day']} | {r['type']:<21}): Bib {r['rider']:3d} | {r['name']:<22} | {r['team']}")

print("\n=== MOST STAGE WINS ===")
print(stage_winners["name"].value_counts())

# Team classifications
days = sorted(df["day"].unique())
team_times_top3 = []
for team in df["team"].unique():
    t_tot = 0
    for day in days:
        d_team = df[(df["day"] == day) & (df["team"] == team)]
        top3 = d_team.sort_values("adj_time").head(3)
        t_tot += top3["adj_time"].sum()
    team_times_top3.append((team, t_tot))

team_top3_df = pd.DataFrame(team_times_top3, columns=["team", "team_time_top3"]).sort_values("team_time_top3").reset_index(drop=True)
print("\n=== TOP 5 TEAMS (Top-3 Daily Sum) ===")
print(team_top3_df.head(5))

# Simple team total
simple_team = df.groupby("team")["adj_time"].sum().reset_index().sort_values("adj_time").reset_index(drop=True)
print("\n=== TOP 5 TEAMS (All Riders Cumulative Sum) ===")
print(simple_team.head(5))

# Points classification (1st: 50, 2nd: 30, 3rd: 20, 4th: 18, 5th: 16, 6th: 14, 7th: 12, 8th: 10, 9th: 8, 10th: 7, etc.)
# Or simple top finishes on flat stages
pts = df[df["type"] == "flat"].groupby(["rider", "name"])["rank"].apply(lambda s: (s <= 10).sum()).reset_index()
pts = pts.sort_values("rank", ascending=False).reset_index(drop=True)
print("\n=== TOP FLAT STAGE FINISHERS (Green Jersey contenders) ===")
print(pts.head(5))

# Mountain stages top finishers (Polka Dot Jersey)
mtn_pts = df[df["type"] == "mountain"].groupby(["rider", "name"])["rank"].apply(lambda s: (s <= 5).sum()).reset_index()
mtn_pts = mtn_pts.sort_values("rank", ascending=False).reset_index(drop=True)
print("\n=== TOP MOUNTAIN FINISHERS (Polka Dot Jersey contenders) ===")
print(mtn_pts.head(5))
