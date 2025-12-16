import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="FAA Recipe", page_icon="🧫")

st.title("🧫 FAA Recipe")
#st.caption("Based on Protocol: GAM modified supplemented with vitamin K1 (Geunhui Shin, 2025)")

# 탭 분리: 스톡 용액 제조 vs 배지 제조
tab1 = st.tabs(["🥣 Media Preparation"])

# --- TAB 1: 배지 제조 계산기 ---
with tab1:
    # 1. 설정 (Settings)
    with st.expander("⚙️ Calculation Settings", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            calc_mode = st.radio("Mode:", ["Total Volume (mL)", "Plate Count"], horizontal=True)
        
        with col2:
            margin_pct = st.slider("Safety Margin (%)", 0, 20, 10)

        if calc_mode == "Total Volume (mL)":
            target_vol = st.number_input("Target Volume (mL)", value=1000, step=100)
            base_volume = target_vol
        else:
            num_plates = st.number_input("Number of Plates", value=40)
            vol_per_plate = st.number_input("Vol/Plate (mL)", value=25)
            base_volume = num_plates * vol_per_plate

        # 최종 부피 및 스케일 계산
        final_vol = base_volume * (1 + margin_pct / 100)
        scale = final_vol / 1000.0  # 기준 1L (1000mL)

        st.metric(label="Final Volume to Prepare", value=f"{final_vol:.1f} mL")

    st.divider()

    # 2. Pre-autoclave Checklist
    st.header("Phase 1: Pre-autoclave Preparation")
    st.info("💡 Mix reagents and autoclave. Final pH should be 7.2 ± 0.2 at 25°C.")

    # 계산된 양
    water_start = 900 * scale
    gam_g = 33.6 * scale
    agar_g = 15.0 * scale
    water_final_vol = 950 * scale

    st.markdown("#### 📝 Step-by-Step Checklist")
    
    # 체크박스 생성
    step1 = st.checkbox(f"1. Measure **{water_start:.1f} mL** of distilled water in a flask/beaker.")
    step2 = st.checkbox(f"2. Add **{gam_g:.2f} g** of **Fastidious Anaerobe Broth** (MB-F2169, KisanBio).")
    step3 = st.checkbox(f"3. Add **{agar_g:.2f} g** of **Bacto Agar** (214010, BD/Difco).")
    step4 = st.checkbox(f"4. Stir and heat on a hotplate (~60°C) until completely dissolved.")
    step5 = st.checkbox(f"5. Add distilled water to bring total volume to **{water_final_vol:.1f} mL**.")
    step6 = st.checkbox(f"6. Cover loosely with foil/tape and **Autoclave at 121°C for 15 min**.")

    st.divider()

    # 3. Post-autoclave Checklist
    st.header("Phase 2: Post-autoclave Supplements")
    st.warning("""
    ⚠️ **Critical Temperature Control:**
    * Cool medium to **50°C** before adding supplement.
    * **Sheep blood defibrinated** must be slowly warmed up to room temperature (20-25°C) and gently shaken or rolled to re-suspend the erythrocytes prior to being added.
    """)

    # 계산된 양
    sheep_blood_defibrinated_ml = 50.0 * scale

    st.markdown("#### 📝 Step-by-Step Checklist")
    
    step7 = st.checkbox(f"7. Cool the medium to **45°C to 50°C** at room temp.")
    step9 = st.checkbox(f"8. (In Biosafety Cabinet) Add **{sheep_blood_defibrinated_ml:.2f} mL** of Sheep blood defibrinated (MB-S1876, KisanBio).")
    step11 = st.checkbox(f"11. Swirl gently to mix without creating bubbles.")
    step12 = st.checkbox(f"12. Pour into Petri dishes and let dry with lids slightly open for ~1 hour.")
    step13 = st.checkbox(f"13. Store plates at 2-8°C in the dark (wrap in foil).")
