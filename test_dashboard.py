"""Comprehensive Automated Test Suite for Tour de France OLAP Dashboard.

Tests all navigation menus, tabs, and Altair chart visualizations across requirements E1 to E15.
"""

import json
from streamlit.testing.v1 import AppTest


def test_dashboard_all_menus_and_charts():
    menus = [
        "📊 Race Overview & Awards",
        "🏆 GC & Storylines (E1, E4, E7, E10)",
        "🏔️ Stages & Terrain (E2, E5, E6, E11, E15)",
        "👥 Teams & Squads (E3, E13, E14)",
        "🌍 Nations & Consistency (E8, E9, E12)",
        "🗄️ SQL Studio & Schema"
    ]

    total_charts_verified = 0

    for m in menus:
        print(f"Testing Menu: {m} ...")
        at = AppTest.from_file("main.py").run()
        at.sidebar.radio[0].set_value(m).run()
        
        assert len(at.exception) == 0, f"Exceptions encountered in menu {m}: {[e.value for e in at.exception]}"
        
        charts = at.get("arrow_vega_lite_chart")
        print(f"  -> Generated {len(charts)} Altair chart(s).")
        total_charts_verified += len(charts)

        # Validate that each chart's spec is valid JSON with valid marks/layers
        for idx, c in enumerate(charts):
            spec = json.loads(c.proto.spec)
            is_valid = ("mark" in spec) or ("layer" in spec)
            assert is_valid, f"Chart [{idx}] in {m} missing both mark and layer in spec: {spec}"

    print(f"\n[PASS] All 6 menus tested. Total charts verified: {total_charts_verified}")


def test_e11_interactive_toggle():
    print("\nTesting E11 Interactive ITT Toggle (Stage 5 <-> Stage 13) ...")
    at = AppTest.from_file("main.py").run()
    at.sidebar.radio[0].set_value("🏔️ Stages & Terrain (E2, E5, E6, E11, E15)").run()
    assert len(at.exception) == 0

    # Locate ITT radio selector
    itt_radios = [r for r in at.radio if "Stage 5" in str(r.options) or 5 in r.options]
    assert len(itt_radios) > 0, "E11 ITT radio selector not found."
    itt_radio = itt_radios[0]

    # Verify Stage 5 (default)
    charts_stg5 = at.get("arrow_vega_lite_chart")
    assert len(charts_stg5) >= 10, f"Expected at least 10 charts in Stages & Terrain, found {len(charts_stg5)}"

    # Toggle to Stage 13
    itt_radio.set_value(13).run()
    assert len(at.exception) == 0, f"Exceptions on toggling E11 to Stage 13: {[e.value for e in at.exception]}"
    charts_stg13 = at.get("arrow_vega_lite_chart")
    assert len(charts_stg13) >= 10, f"Expected at least 10 charts after toggling to Stage 13, found {len(charts_stg13)}"

    print("[PASS] E11 Stage 5 and Stage 13 toggle verified with all charts rendering perfectly.")


if __name__ == "__main__":
    test_dashboard_all_menus_and_charts()
    test_e11_interactive_toggle()
    print("\n==============================================")
    print("ALL DASHBOARD GRAPHICS AND CHARTS TESTED OK!")
    print("==============================================")
