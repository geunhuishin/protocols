import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import numpy as np
from io import BytesIO

# 페이지 설정
st.set_page_config(page_title="OD600 Plotter Ultimate", page_icon="📈", layout="wide")

def parse_time(t_str):
    """
    [수정됨] 24시간 이상 실험 포맷 지원 (d.hh:mm:ss)
    예: 1.01:00:00 -> 1일 1시간 = 25시간으로 변환
    """
    try:
        t_str = str(t_str).strip()
        parts = t_str.split(':')
        
        # hh:mm:ss 또는 d.hh:mm:ss 형식
        if len(parts) == 3:
            # 첫 번째 파트(시)에 마침표(.)가 있는지 확인 (예: 1.01)
            time_part = parts[0]
            if '.' in time_part:
                day_str, hour_str = time_part.split('.')
                days = float(day_str)
                hours = float(hour_str)
                # 날짜를 시간으로 변환하여 합산
                total_hours = (days * 24) + hours
            else:
                total_hours = float(time_part)
            
            minutes = float(parts[1])
            seconds = float(parts[2])
            
            return total_hours + minutes/60 + seconds/3600
            
        # mm:ss 또는 hh:mm (드문 경우)
        elif len(parts) == 2:
            p1, p2 = map(float, parts)
            # 보통 2개면 분:초 일 확률이 높지만, 상황에 따라 다름.
            # 여기서는 안전하게 분:초로 가정
            return p1/60 + p2/3600
            
    except Exception as e:
        # st.write(f"Error parsing {t_str}: {e}") # 디버깅용
        return None
    return None

def main():
    st.title("📈 OD600 Growth Curve (Long-term Support)")
    st.markdown("""
    **업데이트:** 24시간 이상 데이터(`1.01:00:00`) 포맷을 지원합니다.
    """)

    # --- 1. 파일 업로드 ---
    col1, col2 = st.columns(2)
    layout_file = col1.file_uploader("1. Plate Layout (CSV)", type="csv")
    data_file = col2.file_uploader("2. OD600 Raw Data (CSV)", type="csv")

    if layout_file and data_file:
        try:
            # --- 2. Layout 파일 처리 ---
            df_layout = pd.read_csv(layout_file)
            if "Unnamed: 0" in df_layout.columns:
                df_layout.rename(columns={"Unnamed: 0": "Row"}, inplace=True)
            
            df_layout_melt = df_layout.melt(id_vars="Row", var_name="Col", value_name="SampleName")
            df_layout_melt.dropna(subset=["SampleName"], inplace=True) 
            df_layout_melt["Well"] = df_layout_melt["Row"] + df_layout_melt["Col"].astype(str)
            
            def get_group(name):
                parts = str(name).split('-')
                if len(parts) > 1:
                    return "-".join(parts[:-1]) 
                return name
            
            df_layout_melt["Group"] = df_layout_melt["SampleName"].apply(get_group)
            
            # --- 3. Data 파일 처리 ---
            data_file.seek(0)
            content = data_file.read().decode('latin1', errors='ignore')
            
            header_row_idx = 0
            lines = content.splitlines()
            found_header = False
            for i, line in enumerate(lines):
                if line.strip().startswith("Time") and "," in line:
                    header_row_idx = i
                    found_header = True
                    break
            
            if not found_header:
                st.error("❌ 데이터 파일에서 'Time' 컬럼을 찾을 수 없습니다.")
                st.stop()
                
            data_file.seek(0)
            df_raw = pd.read_csv(data_file, skiprows=header_row_idx, encoding='latin1')
            df_raw.columns = df_raw.columns.str.strip()
            
            valid_wells = set(df_layout_melt["Well"].unique())
            cols_to_keep = ["Time"] + [c for c in df_raw.columns if c in valid_wells]
            df_data = df_raw[cols_to_keep].copy()
            
            # [수정된 파싱 함수 적용]
            df_data["Hours"] = df_data["Time"].apply(parse_time)
            df_data.dropna(subset=["Hours"], inplace=True)
            
            # 시간 순서 정렬
            df_data.sort_values("Hours", inplace=True)
            
            # Long Format 변환
            df_data_long = df_data.melt(id_vars=["Time", "Hours"], var_name="Well", value_name="OD600")
            
            # --- 4. 데이터 병합 ---
            df_merged = pd.merge(df_data_long, df_layout_melt, on="Well", how="inner")

            # --- 5. Blank Subtraction ---
            st.sidebar.header("⚙️ Data Processing")
            use_blank_correction = st.sidebar.checkbox("Apply Blank Correction", value=True)
            clip_negative = st.sidebar.checkbox("Clip Negative Values to 0", value=True)
            
            if use_blank_correction:
                min_time = df_merged["Hours"].min()
                df_blanks = df_merged[
                    (df_merged["Group"].str.lower().str.startswith("blank")) & 
                    (df_merged["Hours"] == min_time)
                ].copy()
                
                if not df_blanks.empty:
                    def get_condition(group_name):
                        parts = group_name.split('-', 1)
                        return parts[1] if len(parts) > 1 else "default"

                    df_blanks["Condition"] = df_blanks["Group"].apply(get_condition)
                    blank_map = df_blanks.groupby("Condition")["OD600"].mean().to_dict()
                    
                    def subtract_blank(row):
                        group = row["Group"]
                        parts = group.split('-', 1)
                        condition = parts[1] if len(parts) > 1 else "default"
                        
                        val = row["OD600"]
                        if condition in blank_map:
                            val = val - blank_map[condition]
                        return val

                    df_merged["OD600"] = df_merged.apply(subtract_blank, axis=1)
                    
                    if clip_negative:
                        df_merged["OD600"] = df_merged["OD600"].clip(lower=0)
                    
                    st.sidebar.success(f"✅ Corrected using T={min_time:.1f}h blanks.")
                else:
                    st.sidebar.warning("⚠️ No 'blank' samples found at start time.")

            # 통계 계산 및 정렬
            stats = df_merged.groupby(["Group", "Hours"])["OD600"].agg(
                ['mean', 'std', 'median', 'count']
            ).reset_index()
            stats['sem'] = stats['std'] / np.sqrt(stats['count'])
            stats.sort_values("Hours", inplace=True)

            # --- 6. 그래프 설정 ---
            st.sidebar.divider()
            st.sidebar.header("🎨 Graph Settings")
            
            all_groups = sorted(stats["Group"].unique())
            non_blank_groups = [g for g in all_groups if not g.lower().startswith("blank")]
            default_selection = non_blank_groups if use_blank_correction else all_groups
            
            selected_groups = st.sidebar.multiselect("Select Samples", all_groups, default=default_selection)
            
            st.sidebar.subheader("Colors")
            colors = {}
            cmap = cm.get_cmap('tab10')
            for i, group in enumerate(selected_groups):
                default_color = mcolors.to_hex(cmap(i % 10))
                colors[group] = st.sidebar.color_picker(f"{group}", default_color)
            
            st.sidebar.divider()
            plot_mode = st.sidebar.radio("Central Tendency", ["Mean", "Median"])
            error_type = st.sidebar.selectbox("Error Bar", ["Standard Deviation (SD)", "Standard Error (SEM)", "None"])
            
            # --- 7. Plotting ---
            if selected_groups:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                filtered_stats = stats[stats["Group"].isin(selected_groups)]
                
                for group in selected_groups:
                    subset = filtered_stats[filtered_stats["Group"] == group]
                    
                    x = subset["Hours"]
                    y = subset["mean"] if plot_mode == "Mean" else subset["median"]
                    
                    yerr = None
                    if error_type == "Standard Deviation (SD)":
                        yerr = subset["std"]
                    elif error_type == "Standard Error (SEM)":
                        yerr = subset["sem"]
                    
                    ax.errorbar(
                        x, y, yerr=yerr,
                        label=group,
                        color=colors[group],
                        capsize=3,
                        fmt='-o',
                        markersize=4,
                        linewidth=1.5,
                        alpha=0.8
                    )
                
                ax.set_xlabel("Time (Hours)", fontsize=12)
                ylabel = "OD600 (Corrected)" if use_blank_correction else "OD600 (Raw)"
                ax.set_ylabel(ylabel, fontsize=12)
                ax.set_title(f"Growth Curve ({plot_mode})", fontsize=14)
                ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
                ax.grid(True, linestyle='--', alpha=0.5)
                
                if use_blank_correction:
                    ax.axhline(0, color='black', linewidth=0.8, linestyle='-')

                plt.tight_layout()
                st.pyplot(fig)
                
                # 데이터 확인용 (디버깅)
                with st.expander("🔍 Debug: Time Check"):
                    st.write("24시간 이상 데이터 변환 확인:")
                    debug_df = df_data[["Time", "Hours"]].drop_duplicates().sort_values("Hours")
                    # 23시간 이후 데이터만 필터링해서 보여주기
                    st.dataframe(debug_df[debug_df["Hours"] > 23].head(10))

                col_d1, col_d2 = st.columns(2)
                csv_buffer = stats.to_csv(index=False).encode('utf-8')
                col_d1.download_button("📥 Data (CSV)", csv_buffer, "growth_data.csv", "text/csv")
                
                img_buf = BytesIO()
                fig.savefig(img_buf, format='png', dpi=300, bbox_inches='tight')
                col_d2.download_button("🖼️ Plot (PNG)", img_buf.getvalue(), "growth_plot.png", "image/png")
            else:
                st.warning("샘플을 선택해주세요.")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
            st.write("Layout과 Raw Data 파일의 형식이 올바른지 확인해주세요.")

if __name__ == "__main__":
    main()
