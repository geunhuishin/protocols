import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import numpy as np
from io import BytesIO

# 페이지 설정
st.set_page_config(page_title="OD600 Plotter", page_icon="📈", layout="wide")

def parse_time(t_str):
    """HH:MM:SS 형식을 시간(float)으로 변환"""
    try:
        t_str = str(t_str).strip()
        parts = t_str.split(':')
        if len(parts) == 3:
            h, m, s = map(float, parts)
            return h + m/60 + s/3600
        elif len(parts) == 2:
            m, s = map(float, parts)
            return m/60 + s/3600
    except:
        return None
    return None

def main():
    st.title("📈 OD600 Growth Curve Automator")
    st.markdown("""
    **SpectraMax Raw Data** 호환 버전입니다. 
    Seaborn 설치 없이 바로 실행 가능합니다.
    """)

    # --- 1. 파일 업로드 ---
    col1, col2 = st.columns(2)
    layout_file = col1.file_uploader("1. Plate Layout (CSV)", type="csv")
    data_file = col2.file_uploader("2. OD600 Raw Data (CSV)", type="csv")

    if layout_file and data_file:
        try:
            # --- 2. Layout 파일 처리 ---
            df_layout = pd.read_csv(layout_file)
            
            # 첫 번째 컬럼 이름 변경 (Rows: A, B, C...)
            if "Unnamed: 0" in df_layout.columns:
                df_layout.rename(columns={"Unnamed: 0": "Row"}, inplace=True)
            
            # Tidy Format으로 변환
            df_layout_melt = df_layout.melt(id_vars="Row", var_name="Col", value_name="SampleName")
            df_layout_melt.dropna(subset=["SampleName"], inplace=True) 
            
            # Well ID 생성 (예: A1, B12)
            df_layout_melt["Well"] = df_layout_melt["Row"] + df_layout_melt["Col"].astype(str)
            
            # 그룹 파싱: {Name}-{Condition}-{Replicate} -> Group: {Name}-{Condition}
            def get_group(name):
                parts = str(name).split('-')
                if len(parts) > 1:
                    return "-".join(parts[:-1]) 
                return name
            
            df_layout_melt["Group"] = df_layout_melt["SampleName"].apply(get_group)
            
            # --- 3. Data 파일 처리 (SpectraMax 호환) ---
            # 파일을 텍스트로 읽어서 "Time"으로 시작하는 줄(헤더) 찾기
            data_file.seek(0)
            content = data_file.read().decode('latin1', errors='ignore') # 특수문자 깨짐 방지
            
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
                
            # 찾은 위치부터 CSV 읽기
            data_file.seek(0)
            df_raw = pd.read_csv(data_file, skiprows=header_row_idx, encoding='latin1')
            
            # 불필요한 공백 제거
            df_raw.columns = df_raw.columns.str.strip()
            
            # Layout에 있는 Well만 남기기
            valid_wells = set(df_layout_melt["Well"].unique())
            cols_to_keep = ["Time"] + [c for c in df_raw.columns if c in valid_wells]
            
            df_data = df_raw[cols_to_keep].copy()
            
            # 시간 변환
            df_data["Hours"] = df_data["Time"].apply(parse_time)
            df_data.dropna(subset=["Hours"], inplace=True)
            
            # Long Format 변환
            df_data_long = df_data.melt(id_vars=["Time", "Hours"], var_name="Well", value_name="OD600")
            
            # --- 4. 데이터 병합 ---
            df_merged = pd.merge(df_data_long, df_layout_melt, on="Well", how="inner")
            
            stats = df_merged.groupby(["Group", "Hours"])["OD600"].agg(
                ['mean', 'std', 'median', 'count']
            ).reset_index()
            stats['sem'] = stats['std'] / np.sqrt(stats['count'])
            
            st.success(f"✅ 처리 완료! {len(stats['Group'].unique())}개 그룹을 찾았습니다.")

            # --- 5. 그래프 설정 ---
            with st.sidebar:
                st.header("🎨 Graph Settings")
                all_groups = sorted(stats["Group"].unique())
                selected_groups = st.multiselect("Select Samples", all_groups, default=all_groups)
                
                st.divider()
                st.subheader("Colors")
                
                # Matplotlib 컬러맵 사용
                colors = {}
                cmap = cm.get_cmap('tab10') # 기본 10색상
                
                for i, group in enumerate(selected_groups):
                    # Hex 코드로 변환
                    default_color = mcolors.to_hex(cmap(i % 10))
                    colors[group] = st.color_picker(f"{group}", default_color)
                
                st.divider()
                plot_mode = st.radio("Central Tendency", ["Mean", "Median"])
                error_type = st.selectbox("Error Bar", ["Standard Deviation (SD)", "Standard Error (SEM)", "None"])

            # --- 6. Plotting ---
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
                ax.set_ylabel("OD600", fontsize=12)
                ax.set_title(f"Growth Curve ({plot_mode})", fontsize=14)
                ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
                ax.grid(True, linestyle='--', alpha=0.5)
                
                plt.tight_layout()
                st.pyplot(fig)
                
                # 다운로드 버튼
                csv_buffer = stats.to_csv(index=False).encode('utf-8')
                st.download_button("📥 데이터 다운로드 (CSV)", csv_buffer, "growth_curve_data.csv", "text/csv")
            else:
                st.warning("샘플을 선택해주세요.")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
            st.write("Layout 파일과 Data 파일 형식을 다시 확인해주세요.")

if __name__ == "__main__":
    main()
