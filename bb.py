import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="BB Agar Recipe", page_icon="🧫")

st.title("🧫 BB Agar Recipe")

# 탭 분리: st.tabs는 리스트를 반환하므로, [tab1]으로 받아서 리스트 껍질을 벗겨줘야 함
[tab1] = st.tabs(["🥣 Media Preparation"])

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
    st.info("💡 Mix reagents and autoclave. Final pH should be 7.0 ± 0.2 at 25°C.")

    # 계산된 양
    water_mL = 950 * scale
    bb_g = 28.1 * scale 
    agar_g = 15.0 * scale

    st.markdown("#### 📝 Step-by-Step Checklist")
    
    # 체크박스 생성
    step1 = st.checkbox(f"1. Suspend **{bb_g:.2f} g** of **Brucella Broth** (MB-B2134, KisanBio) **{water_mL:.1f} mL** of distilled water in Duran bottle.")
    step3 = st.checkbox(f"2. Add **{agar_g:.2f} g** of **Bacto Agar** (214010, BD/Difco).")
    step6 = st.checkbox(f"3. Cover loosely with foil/tape and **Sterilize by autoclave at 121°C for 15 min**.")

    st.divider()

    # 3. Post-autoclave Checklist
    st.header("Phase 2: Post-autoclave Supplements")
    st.warning("""
    ⚠️ **Critical Temperature Control:**
    * Cool medium to **45°C - 50°C** before adding supplement.
    * **Sheep blood defibrinated** must be slowly warmed up to room temperature (20-25°C) and gently shaken or rolled to re-suspend the erythrocytes prior to being added.
    """)

    # 계산된 양
    sheep_blood_defibrinated_ml = 50.0 * scale

    st.markdown("#### 📝 Step-by-Step Checklist")
    
    step7 = st.checkbox(f"4. Cool the medium to **45°C to 50°C** at room temp.")
    step9 = st.checkbox(f"5. (In Biosafety Cabinet) Add **{sheep_blood_defibrinated_ml:.2f} mL** of Sheep blood defibrinated (MB-S1876, KisanBio).")
    step11 = st.checkbox(f"6. Swirl gently to mix without creating bubbles.")
    step12 = st.checkbox(f"7. Pour into Petri dishes and let dry with lids slightly open for ~1 hour.")
    step13 = st.checkbox(f"8. Store plates at 2-8°C in the dark (wrap in foil).")
