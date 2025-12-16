import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from io import BytesIO

# 페이지 설정
st.set_page_config(page_title="OD600 Plotter", page_icon="📈", layout="wide")

def parse_time(t_str):
    """HH:MM:SS 형식을 시간(float)으로 변환"""
    try:
        parts = str(t_str).split(':')
        if len(parts) == 3:
            h, m, s = map(int, parts)
            return h + m/60 + s/3600
        elif len(parts) == 2:
            m, s = map(int, parts)
            return m/60 + s/3600
    except:
        return None
    return None

def main():
    st.title("📈 OD600 Growth Curve Automator")
    st.markdown("""
    **96-well Plate Layout**과 **Plate Reader Data** 파일을 업로드하면 
    자동으로 `{Name}-{Condition}` 그룹을 묶어 그래프를 그려줍니다.
    """)

    # --- 1. 파일 업로드 ---
    col1, col2 = st.columns(2)
    layout_file = col1.file_uploader("1. Plate Layout (CSV)", type="csv", help="Sample names in wells")
    data_file = col2.file_uploader("2. OD600 Raw Data (CSV)", type="csv", help="From Plate Reader")

    if layout_file and data_file:
        try:
            # --- 2. Layout 파일 처리 ---
            df_layout = pd.read_csv(layout_file)
            
            # 첫 번째 컬럼 이름 변경 (Rows: A, B, C...)
            if "Unnamed: 0" in df_layout.columns:
                df_layout.rename(columns={"Unnamed: 0": "Row"}, inplace=True)
            
            # Tidy Format으로 변환 (Row, Col, SampleName)
            df_layout_melt = df_layout.melt(id_vars="Row", var_name="Col", value_name="SampleName")
            df_layout_melt.dropna(subset=["SampleName"], inplace=True) # 빈 웰 제거
            
            # Well ID 생성 (예: A1, B12)
            df_layout_melt["Well"] = df_layout_melt["Row"] + df_layout_melt["Col"].astype(str)
            
            # 그룹 파싱 로직: {Name}-{Condition}-{Replicate} -> Group: {Name}-{Condition}
            # 마지막 하이픈(-) 뒤의 숫자를 제거하고 그룹명으로 사용
            def get_group(name):
                parts = str(name).split('-')
                if len(parts) > 1:
                    return "-".join(parts[:-1]) # 마지막 부분(replicate) 제외
                return name
            
            df_layout_melt["Group"] = df_layout_melt["SampleName"].apply(get_group)
            
            # --- 3. Data 파일 처리 ---
            # 데이터 파일의 헤더 위치 찾기 ("Time"으로 시작하는 줄)
            data_file.seek(0)
            header_row = 0
            lines = data_file.readlines()
            for i, line in enumerate(lines):
                # 인코딩 문제 방지
                decoded_line = line.decode("utf-8", errors="ignore")
                if decoded_line.startswith("Time"):
                    header_row = i
                    break
            
            data_file.seek(0)
            df_raw = pd.read_csv(data_file, skiprows=header_row)
            
            # 필요한 컬럼만 선택 (Time + Layout에 있는 Wells)
            valid_wells = set(df_layout_melt["Well"].unique())
            # 데이터 파일 컬럼 중 Layout에 있는 Well만 남김
            cols_to_keep = ["Time"] + [c for c in df_raw.columns if c in valid_wells]
            
            if len(cols_to_keep) <= 1:
                st.error("❌ Layout의 Well 이름과 데이터 파일의 Well 이름이 일치하지 않습니다 (예: A1 vs A01). 확인해주세요.")
                st.stop()
                
            df_data = df_raw[cols_to_keep].copy()
            
            # 시간 변환
            df_data["Hours"] = df_data["Time"].apply(parse_time)
            df_data.dropna(subset=["Hours"], inplace=True) # 시간 변환 실패 행 제거
            
            # Long Format 변환
            df_data_long = df_data.melt(id_vars=["Time", "Hours"], var_name="Well", value_name="OD600")
            
            # --- 4. 데이터 병합 (Merge) ---
            df_merged = pd.merge(df_data_long, df_layout_melt, on="Well", how="inner")
            
            # 통계 계산 (Mean, Std, Median, SEM)
            stats = df_merged.groupby(["Group", "Hours"])["OD600"].agg(
                ['mean', 'std', 'median', 'count']
            ).reset_index()
            stats['sem'] = stats['std'] / np.sqrt(stats['count'])
            
            st.success(f"✅ Data Processed! Found {len(stats['Group'].unique())} groups.")

            # --- 5. 그래프 설정 및 그리기 ---
            with st.sidebar:
                st.header("🎨 Graph Settings")
                
                # 그룹 선택
                all_groups = sorted(stats["Group"].unique())
                selected_groups = st.multiselect("Select Samples", all_groups, default=all_groups)
                
                st.divider()
                st.subheader("Colors")
                
                # 색상 선택기 자동 생성
                colors = {}
                default_palette = sns.color_palette("husl", len(all_groups)).as_hex()
                for i, group in enumerate(selected_groups):
                    # 기본 색상을 지정해주고 사용자가 변경 가능하게 함
                    colors[group] = st.color_picker(f"{group}", default_palette[i % len(default_palette)])
                
                st.divider()
                # 에러바 설정
                plot_mode = st.radio("Central Tendency", ["Mean", "Median"])
                error_type = st.selectbox("Error Bar", ["Standard Deviation (SD)", "Standard Error (SEM)", "None"])

            # 메인 그래프 영역
            if selected_groups:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                filtered_stats = stats[stats["Group"].isin(selected_groups)]
                
                for group in selected_groups:
                    subset = filtered_stats[filtered_stats["Group"] == group]
                    
                    # X, Y 데이터
                    x = subset["Hours"]
                    if plot_mode == "Mean":
                        y = subset["mean"]
                    else:
                        y = subset["median"]
                    
                    # 에러 데이터
                    if error_type == "Standard Deviation (SD)":
                        yerr = subset["std"]
                    elif error_type == "Standard Error (SEM)":
                        yerr = subset["sem"]
                    else:
                        yerr = None
                    
                    # 플롯 그리기
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
                ax.set_title(f"Growth Curve ({plot_mode} ± {error_type})", fontsize=14)
                ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)
                ax.grid(True, linestyle='--', alpha=0.5)
                
                plt.tight_layout()
                st.pyplot(fig)
                
                # --- 6. 다운로드 버튼 ---
                col_d1, col_d2 = st.columns(2)
                
                # CSV 다운로드
                csv = stats.to_csv(index=False).encode('utf-8')
                col_d1.download_button("📥 Download Processed Data (CSV)", csv, "growth_data.csv", "text/csv")
                
                # 이미지 다운로드
                img_buf = BytesIO()
                fig.savefig(img_buf, format='png', dpi=300, bbox_inches='tight')
                col_d2.download_button("🖼️ Download Plot (PNG)", img_buf.getvalue(), "growth_curve.png", "image/png")
            else:
                st.warning("Please select at least one group to plot.")

        except Exception as e:
            st.error(f"Error: {e}")
            st.info("💡 Tip: Check if your Layout CSV uses 'A1' format and Data CSV has 'Time' column.")

if __name__ == "__main__":
    main()
