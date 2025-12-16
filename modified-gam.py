import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="GAM Media Calculator", page_icon="🧫")

st.title("🧫 GAM Modified + Vit K1 Calculator")
st.caption("Based on Protocol: GAM modified supplemented with vitamin K1 (Geunhui Shin, 2025)")

# 탭 분리: 배지 제조 vs 스톡 용액 제조
tab1, tab2 = st.tabs(["🥣 Media Preparation", "🧪 Stock Solutions"])

# --- TAB 1: 배지 제조 계산기 ---
with tab1:
    st.header("1. Media Preparation")
    
    # 사이드바 입력 (TAB 1용)
    st.subheader("Target Volume Settings")
    
    # 입력 방식 선택 (부피 기준 vs 플레이트 수 기준)
    calc_mode = st.radio("Calculate based on:", ["Total Volume (mL)", "Number of Plates"], horizontal=True)
    
    base_volume_ml = 0
    
    if calc_mode == "Total Volume (mL)":
        target_vol = st.number_input("Target Volume (mL)", min_value=100, value=1000, step=100)
        base_volume_ml = target_vol
        # PDF 기준 1L = 40 plates [cite: 37]
        estimated_plates = base_volume_ml / 25 
        st.info(f"📊 Estimated yield: ~{int(estimated_plates)} plates (assuming 25mL/plate)")
        
    else:
        num_plates = st.number_input("Number of Plates", min_value=1, value=40, step=1)
        vol_per_plate = st.number_input("Volume per Plate (mL)", value=25)
        base_volume_ml = num_plates * vol_per_plate
        st.info(f"📊 Total Volume needed: {base_volume_ml} mL")

    # Safety Margin (Dead Volume)
    margin_pct = st.slider("Safety Margin (%)", 0, 20, 10, help="Extra volume to account for pipetting errors/evaporation")
    final_vol = base_volume_ml * (1 + margin_pct / 100)
    
    st.divider()
    
    # Scaling Factor (Reference: 1000 mL)
    # PDF Reference [cite: 37-39, 65, 92, 95, 101]
    scale = final_vol / 1000.0

    # 데이터프레임 생성
    recipe_data = [
        # Pre-autoclave [cite: 37-39]
        {"Phase": "1. Pre-autoclave", "Reagent": "Distilled Water (Initial)", "Amount": 850 * scale, "Unit": "mL", "Note": "Dissolve powders in this"},
        {"Phase": "1. Pre-autoclave", "Reagent": "GAM Broth Modified", "Amount": 35.4 * scale, "Unit": "g", "Note": "Cat# MB-G0826"},
        {"Phase": "1. Pre-autoclave", "Reagent": "Bacto Agar", "Amount": 15.0 * scale, "Unit": "g", "Note": "Cat# 214010"},
        {"Phase": "1. Pre-autoclave", "Reagent": "Distilled Water (Top-up)", "Amount": 970 * scale, "Unit": "mL", "Note": "Top up to this volume before autoclaving [cite: 65]"},
        
        # Post-autoclave [cite: 92, 95, 101]
        {"Phase": "2. Post-autoclave", "Reagent": "Hemin Solution (0.5 g/L)", "Amount": 10.0 * scale, "Unit": "mL", "Note": "Add at ~50°C. Degrades >75°C "},
        {"Phase": "2. Post-autoclave", "Reagent": "10% NaHCO3 (Filtered)", "Amount": 20.0 * scale, "Unit": "mL", "Note": "Decomposes >50°C [cite: 96]"},
        {"Phase": "2. Post-autoclave", "Reagent": "Vitamin K1 (10 g/L)", "Amount": 100 * scale, "Unit": "µL", "Note": "Light sensitive"},
    ]
    
    df_recipe = pd.DataFrame(recipe_data)
    
    # 결과 출력
    st.write(f"### 📝 Recipe for {final_vol:.1f} mL")
    st.dataframe(
        df_recipe.style.format({"Amount": "{:.2f}"}), 
        use_container_width=True,
        hide_index=True
    )
    
    # 체크리스트 모드
    with st.expander("✅ Open Interactive Checklist"):
        for _, row in df_recipe.iterrows():
            st.checkbox(f"**{row['Reagent']}**: {row['Amount']:.2f} {row['Unit']} ({row['Note']})")

    st.warning("""
    **Critical Steps:**
    * Autoclave at 121°C for 20 min[cite: 69].
    * Cool to **50°C** before adding supplements[cite: 87].
    * Hemin degrades rapidly at high temps (Half-life 0.73 days at 95°C)[cite: 94].
    """)

# --- TAB 2: 스톡 용액 제조 계산기 ---
with tab2:
    st.header("2. Stock Solution Calculator")
    
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
