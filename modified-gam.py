import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="GAM Media Calculator", page_icon="🧫")

st.title("🧫 GAM Modified + Vitamin K1 Calculator")
#st.caption("Based on Protocol: GAM modified supplemented with vitamin K1 (Geunhui Shin, 2025)")

# 탭 분리: 배지 제조 vs 스톡 용액 제조
tab1, tab2 = st.tabs(["🧪 Stock Solutions", "🥣 Media Preparation"])

# --- TAB 1: 스톡 용액 제조 계산기 ---
with tab1:
    st.header("1. Stock Solution Calculator")
    
    stock_type = st.selectbox("Select Stock Solution", ["Hemin (0.5 g/L)", "Vitamin K1 (10 g/L)", "10% NaHCO3"])
    
    make_vol = st.number_input("Volume to prepare (mL)", value=50, step=10)
    
    st.divider()
    st.write(f"### Recipe for {make_vol} mL of {stock_type}")
    
    if stock_type == "Hemin (0.5 g/L)":
        # PDF Step 1: 0.25g in 50mL total [cite: 29-31]
        # Ratio: 0.5 g per 1000 mL
        hemin_g = (0.5 / 1000) * make_vol
        naoh_vol = (500 / 50) * (make_vol / 1000) * 1000 # Scaling logic adjusted for µL
        # Original: 500uL NaOH for 50mL total. -> 10uL NaOH per 1mL total.
        naoh_needed_ul = 10 * make_vol 
        
        st.markdown(f"""
        1. Weigh **{hemin_g:.4f} g** of Hemin.
        2. Dissolve in **{naoh_needed_ul:.1f} µL** of 1M NaOH.
        3. Make up to **{make_vol} mL** with distilled water.
        4. **Filter sterilize**. Store refrigerated[cite: 31].
        """)
        
    elif stock_type == "Vitamin K1 (10 g/L)":
        # PDF Step 1: 0.5g in 50mL [cite: 32-33]
        # Ratio: 10g per 1000 mL (1%)
        vitk_g = (10 / 1000) * make_vol
        ethanol_vol = make_vol # Solvent is 95% Ethanol
        
        st.markdown(f"""
        1. Weigh **{vitk_g:.3f} g** of Vitamin K1.
        2. Dissolve in **{ethanol_vol} mL** of 95% Ethanol.
        3. **Filter sterilize**. Store in a **brown bottle** (Light sensitive)[cite: 33, 34].
        """)
        
    elif stock_type == "10% NaHCO3":
        # PDF Step 7: 20g in 200mL [cite: 72]
        # Ratio: 10g per 100mL
        nahco3_g = (10 / 100) * make_vol
        water_vol = make_vol
        
        st.markdown(f"""
        1. Weigh **{nahco3_g:.2f} g** of NaHCO3.
        2. Dissolve in **{water_vol} mL** of distilled water.
        3. **Filter sterilize** using PES filter (Avoid Cellulose Nitrate/Acetate)[cite: 78, 79].
        4. Store at 2-8°C[cite: 80].
        """)

# --- TAB 2: 배지 제조 계산기 ---
with tab2:
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
    st.info("💡 Mix reagents and autoclave. Final pH should be 7.1 ± 0.2.")

    # 계산된 양
    water_start = 850 * scale
    gam_g = 35.4 * scale
    agar_g = 15.0 * scale
    water_final_vol = 970 * scale

    st.markdown("#### 📝 Checklist")
    
    # 체크박스에 포맷팅된 문자열 사용
    step1 = st.checkbox(f"1. Measure **{water_start:.1f} mL** of distilled water in a flask/beaker.")
    [cite_start]step2 = st.checkbox(f"2. Add **{gam_g:.2f} g** of **GAM Broth Modified** (MB-G0826)[cite: 38].")
    [cite_start]step3 = st.checkbox(f"3. Add **{agar_g:.2f} g** of **Bacto Agar** (214010)[cite: 39].")
    [cite_start]step4 = st.checkbox(f"4. Stir and heat on a hotplate (~60°C) until completely dissolved[cite: 62].")
    [cite_start]step5 = st.checkbox(f"5. Add distilled water to bring total volume to **{water_final_vol:.1f} mL**[cite: 65].")
    [cite_start]step6 = st.checkbox(f"6. Cover loosely with foil/tape and **Autoclave at 121°C for 20 min**[cite: 69].")

    st.divider()

    # 3. Post-autoclave Checklist
    st.header("Phase 2: Post-autoclave Supplements")
    st.warning("""
    ⚠️ **Critical Temperature Control:**
    * [cite_start]Cool medium to **50°C** before adding supplements[cite: 87].
    * [cite_start]**Hemin** degrades rapidly >75°C (Half-life ~0.73 days at 95°C)[cite: 93, 94].
    * [cite_start]**NaHCO3** decomposes >50°C[cite: 96].
    """)

    # 계산된 양
    hemin_ml = 10.0 * scale
    nahco3_ml = 20.0 * scale
    vitk1_ul = 100 * scale 

    st.markdown("#### 📝 Checklist")
    
    step7 = st.checkbox(f"7. Cool the medium to **50°C** in a water bath or at room temp.")
    [cite_start]step8 = st.checkbox(f"8. (In Biosafety Cabinet) Add **{hemin_ml:.2f} mL** of Hemin stock (0.5 g/L)[cite: 92].")
    [cite_start]step9 = st.checkbox(f"9. (In Biosafety Cabinet) Add **{nahco3_ml:.2f} mL** of filtered 10% NaHCO3[cite: 95].")
    [cite_start]step10 = st.checkbox(f"10. (In Biosafety Cabinet) Add **{vitk1_ul:.1f} µL** of Vitamin K1 stock (10 g/L)[cite: 101].")
    step11 = st.checkbox(f"11. Swirl gently to mix without creating bubbles.")
    [cite_start]step12 = st.checkbox(f"12. Pour into Petri dishes and let dry with lids slightly open for ~1 hour[cite: 105].")
    [cite_start]step13 = st.checkbox(f"13. Store plates at 2-8°C in the dark (wrap in foil)[cite: 109].")

