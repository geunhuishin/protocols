import streamlit as st
import pandas as pd

def calculate_mix(components, num_samples, excess_pct):
    """
    Master Mix 계산 함수
    """
    df = pd.DataFrame(components)
    factor = num_samples * (1 + excess_pct / 100)
    df['Total Volume (µL)'] = df['Volume per rxn (µL)'] * factor
    return df

def display_section(title, mix_data, protocol_steps, num_samples, excess_pct):
    """
    각 섹션별 UI 렌더링 (마스터믹스 + 체크리스트)
    """
    st.header(title)
    
    # 1. Master Mix Calculator
    if mix_data:
        st.subheader(f"🧪 Master Mix (n={num_samples}, +{excess_pct}%)")
        df = calculate_mix(mix_data, num_samples, excess_pct)
        st.dataframe(
            df.style.format({"Volume per rxn (µL)": "{:.2f}", "Total Volume (µL)": "{:.1f}"}),
            use_container_width=True,
            hide_index=True
        )
        total_vol = df['Total Volume (µL)'].sum()
        one_rxn_vol = df['Volume per rxn (µL)'].sum()
        st.info(f"Dispense **{one_rxn_vol:.1f} µL** per well from this mix.")

    # 2. Protocol Steps
    st.subheader("📋 Procedure")
    for i, step in enumerate(protocol_steps, 1):
        st.checkbox(step, key=f"{title}_{i}")
    st.divider()

def main():
    st.set_page_config(page_title="RNA-seq Library Prep", page_icon="🧬", layout="wide")
    
    st.title("🧬 RNA-seq Library Prep Protocol")
    st.markdown("**Based on: RNA-Snap extraction & Custom Library Prep**")

    # --- Sidebar: Global Settings ---
    with st.sidebar:
        st.header("⚙️ Settings")
        num_samples = st.number_input("Number of Samples", min_value=1, value=12, step=1)
        excess_pct = st.slider("Dead Volume / Excess (%)", 0, 50, 10, help="Reagent waste margin")
        
        st.markdown("---")
        st.markdown("### 📚 Quick Links")
        st.markdown("[1. RNA Extraction](#1-rna-extraction-rna-snap)")
        st.markdown("[2. QC & Norm](#2-rna-qc-and-normalization)")
        st.markdown("[3. Frag & DNase](#3-fragmentation-and-dnase-digestion)")
        st.markdown("[4. 3' Adapter Ligation](#4-3-dna-adapter-ligation)")
        st.markdown("[5. rRNA Depletion](#5-rnase-h-based-rrna-depletion)")
        st.markdown("[6. Reverse Transcription](#6-reverse-transcription)")
        st.markdown("[7. Adapter Ligation #2](#7-adapter-ligation-2)")
        st.markdown("[8. PCR Amplification](#8-pcr-amplification)")

    # --- Define Data ---
    
    # 1. RNA Extraction
    mix_rna_snap = [
        {"Reagent": "0.5M EDTA", "Volume per rxn (µL)": 18.0},
        {"Reagent": "10% SDS", "Volume per rxn (µL)": 1.25},
        {"Reagent": "B-mercaptoethanol", "Volume per rxn (µL)": 5.0},
        {"Reagent": "Formamide", "Volume per rxn (µL)": 475.0},
    ]
    steps_extraction = [
        "Take 1mL of cell culture, spin 4,300g, 5min, 4°C.",
        "Remove supernatant. Store pellets on dry ice or -80°C if needed.",
        "Add ~200µl 0.1mm zirconia beads to frozen pellets.",
        "**Prepare RNA-snap master mix** (Calculated above).",
        "Resuspend cells in 500µl RNA-snap mix. Seal plate.",
        "Place at -20°C for 10 min.",
        "Bead beating: 2.5 min -> Cool 5 min -> Beat 2.5 min -> Cool 5 min -> Beat 2.5 min -> Cool 5 min.",
        "Spin 4,300g, 5min, 4°C. Recover **200µL** supernatant to new plate.",
        "**Zymo RNA Clean & Concentrate**:\n  - Add 600µl Ethanol (100%), mix.\n  - Bind to column, discard flow-through.\n  - Add 400µl RNA Prep Buffer, spin.\n  - Add 400µl RNA Prep Buffer (2nd time? check protocol), then 700µl Wash Buffer.\n  - Add 400µl Wash Buffer, spin 2 min dry.\n  - Elute in **30µl** nuclease-free water."
    ]

    # 2. QC
    steps_qc = [
        "Quantify using Qubit RNA Broad Range (BR) Assay kit (1-2µl input).",
        "Target **15-20ug per pool** (or 400ng in 15µl if single sample).",
        "Add 1µl SUPERase-IN if storing at -80°C (Optional)."
    ]

    # 3. Frag & DNase
    mix_fastap = [
        {"Reagent": "Recombinant RNase Inhibitor; Takara, Cat.# 2313A", "Volume per rxn (µL)": 1.0},
        {"Reagent": "Turbo DNase; Ambion/Applied Biosystems, Cat.# AM2239", "Volume per rxn (µL)": 4.0},
        {"Reagent": "FastAP Thermosensitive Alkaline Phosphatase; Thermo Scientific, Cat.# EF0651", "Volume per rxn (µL)": 10.0},
        {"Reagent": "Nuclease free water", "Volume per rxn (µL)": 5.0},
    ]
    steps_frag = [
        "Add 4µl FastAP buffer (10X) to each well (containing RNA). Mix.",
        "Incubate: **94°C for 3 min** (or 92°C 2.5min for low integrity).",
        "**Prepare FastAP Master Mix** (Calculated above).",
        "Add **20µl** Master Mix to each well.",
        "Incubate: **37°C for 30 min**. Place on ice immediately.",
        "**2X SPRI Cleanup** (80µl beads). Elute in **7µl** water.",
        "Move **5µl** to new tube for Ligation 1.",
        "(Optional) Check remaining on Agilent Pico chip."
    ]

    # 4. 3' Adapter Ligation
    mix_lig1 = [
        {"Reagent": "10X T4 RNA Ligase buffer", "Volume per rxn (µL)": 2.0},
        {"Reagent": "DMSO (100%)", "Volume per rxn (µL)": 1.8},
        {"Reagent": "ATP (100mM)", "Volume per rxn (µL)": 0.2},
        {"Reagent": "PEG 8000 (50%)", "Volume per rxn (µL)": 8.0},
        {"Reagent": "Recombinant RNase Inhibitor; Takara, Cat.# 2313A", "Volume per rxn (µL)": 0.3},
        {"Reagent": "T4 RNA Ligase 1; Enzynomics, Cat.# M042S", "Volume per rxn (µL)": 1.8},
    ]
    steps_lig1 = [
        "Add 1µl of **Unique Adapter** (100uM) to 5µl RNA.",
        "Heat **70°C for 2 min**, then cold block.",
        "**Prepare Ligation Master Mix** (At RT, PEG is viscous!). *Protocol suggests 25% excess.*",
        "Add **14.1 µl** Mix to RNA/Adapter.",
        "Mix 10 times. Incubate **22°C for 1hr 30min**.",
        "Add 60µl RLT buffer. Total 80µl.",
        "**Pool samples** and clean up (Zymo C&C-5, 200nt cutoff):\n - Mix pooled sample 1:1 with (Binding Buffer+EtOH).\n - Bind, Wash steps.\n - Elute 2 times with 16µl (Final **32µl**).\n - Quantify with Qubit HS RNA."
    ]

    # 5. rRNA Depletion
    mix_hybridization = [
         {"Reagent": "5M NaCl", "Volume per rxn (µL)": 0.6},
         {"Reagent": "1M Tris-HCl (pH 7.5)", "Volume per rxn (µL)": 1.5},
         {"Reagent": "Nuclease-free water (Adjust as needed)", "Volume per rxn (µL)": 12.9}, 
         # Note: Protocol implies 15uL total reaction including 500ng RNA + Probe. 
         # Assuming RNA+Probe volume is variable, this MM helps prep the buffer part.
         # Simplified for scaling: creating a buffer mix to add to RNA+Probe.
    ]
    
    mix_rnase_h = [
        {"Reagent": "RNase H; Enzynomics, Cat.# M036S", "Volume per rxn (µL)": 3.0},
        {"Reagent": "1M Tris-HCl (pH 7.5)", "Volume per rxn (µL)": 0.5},
        {"Reagent": "5M NaCl", "Volume per rxn (µL)": 0.2},
        {"Reagent": "1M MgCl2", "Volume per rxn (µL)": 0.4},
        {"Reagent": "Nuclease-free water", "Volume per rxn (µL)": 0.9},
    ]

    steps_rrna = [
        "**Hybridization**: Mix 500ng RNA, Probes, and Buffer components (Total 15µl).",
        "Cycler: 95°C -> 45°C (-0.1°C/sec). Hold 45°C for 5 min.",
        "**Prepare RNase H Master Mix** (Calculated above). Preheat to 45°C.",
        "Add **5µl** RNase H Mix to reaction (Total 20µl).",
        "Incubate **45°C for 30 min** (Lid 60°C).",
        "Spin down, place on ice.",
        "**2X SPRI Cleanup** (Part 1): Elute 26µl, take 25µl.",
        "**2X SPRI Cleanup** (Part 2): Elute 15µl, take 14µl.",
        "Store at -80°C or proceed."
    ]

    # 6. Reverse Transcription
    mix_rt = [
        {"Reagent": "5X RT Buffer", "Volume per rxn (µL)": 4.0},
        {"Reagent": "dNTP mix (10mM)", "Volume per rxn (µL)": 1.0},
        {"Reagent": "100mM DTT", "Volume per rxn (µL)": 1.0},
        {"Reagent": "Recombinant RNase Inhibitor; Takara, Cat.# 2313A", "Volume per rxn (µL)": 1.0},
        {"Reagent": "Maxima H Minus Reverse Transcriptase (200 U/μL); Thermo Scientific, Cat.# EP0752", "Volume per rxn (µL)": 1.0},
    ]
    steps_rt = [
        "Take 10µl rRNA depleted RNA.",
        "Add 2µl RT Primer (20uM). Heat **70°C for 2 min**, ice.",
        "**Prepare RT Master Mix** (Calculated above).",
        "Add **8µl** Master Mix (Total 20µl).",
        "Incubate **55°C for 15 min**.",
        "Add 1µl RNase H. Incubate **37°C for 20 min**.",
        "**2X SPRI Cleanup**. Elute in **5µl** water. **KEEP BEADS**."
    ]

    # 7. Adapter Ligation 2
    mix_lig2 = [
        {"Reagent": "10X T4 Ligase Buffer", "Volume per rxn (µL)": 2.0},
        {"Reagent": "DMSO (100%)", "Volume per rxn (µL)": 0.8},
        {"Reagent": "ATP (100mM)", "Volume per rxn (µL)": 0.2},
        {"Reagent": "PEG 8000 (50%)", "Volume per rxn (µL)": 8.5},
        {"Reagent": "T4 RNA Ligase 1; Enzynomics, Cat.# M042S", "Volume per rxn (µL)": 1.5},
    ]
    steps_lig2 = [
        "Add 2µl RS_2adap (40uM) to cDNA/bead mix.",
        "Heat **75°C for 3 min**, ice.",
        "**Prepare Ligation 2 Master Mix** (Calculated above).",
        "Add **13µl** Mix to tube.",
        "Incubate **22°C Overnight**.",
        "**2X SPRI Cleanup**, elute 25µl.",
        "**1.5X SPRI Cleanup**, elute 15µl."
    ]

    # 8. PCR
    mix_pcr = [
        {"Reagent": "KOD ONE PCR MM; TOYOBO, Cat.# KMM-101", "Volume per rxn (µL)": 25.0},
        {"Reagent": "Nuclease free water", "Volume per rxn (µL)": 10.0},
        {"Reagent": "SYBR™ Gold Nucleic Acid Gel Stain (10,000X Concentrate in DMSO); Invitrogen, Cat.# S11494", "Volume per rxn (µL)": 1.0},
    ]
    steps_pcr = [
        "**Prepare PCR Master Mix** (KOD+Water+SYBR).",
        "Combine: 10µl cDNA + 2.5µl Fwd Primer + 2.5µl Rev Primer + 36µl Master Mix.",
        "**qPCR Cycling**:\n 1. 98°C 3m\n 2. 98°C 10s\n 3. 67°C 15s\n 4. 72°C 1m\n (Repeat 2-4)\n 5. 72°C 5min",
        "Stop during exponential phase.",
        "**2X SPRI Cleanup**, elute 22µl.",
        "Run Egel (2%), Gel purify (Monarch).",
        "Quantify (Qubit HS DNA). Load NextSeq."
    ]

    # --- Render Sections ---
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "1. Extraction", "2. QC", "3. Frag/DNase", "4. Lig #1", 
        "5. Depletion", "6. RT", "7. Lig #2", "8. PCR"
    ])

    with tab1:
        display_section("1. RNA Extraction (RNA-Snap)", mix_rna_snap, steps_extraction, num_samples, excess_pct)
    
    with tab2:
        display_section("2. RNA QC and Normalization", None, steps_qc, num_samples, excess_pct)

    with tab3:
        display_section("3. Fragmentation and DNase Digestion", mix_fastap, steps_frag, num_samples, excess_pct)
        
    with tab4:
        display_section("4. 3' DNA Adapter Ligation", mix_lig1, steps_lig1, num_samples, excess_pct)
        st.caption("*Note: Protocol recommends preparing reagent mix at RT and adding PEG slowly.*")

    with tab5:
        display_section("5. RNase H based rRNA Depletion", mix_rnase_h, steps_rrna, num_samples, excess_pct)
        st.caption("*Note: Hybridization mix is calculated for the RNase H Step mainly. Check protocol for Probe mix specifics.*")

    with tab6:
        display_section("6. Reverse Transcription", mix_rt, steps_rt, num_samples, excess_pct)

    with tab7:
        display_section("7. Adapter Ligation #2", mix_lig2, steps_lig2, num_samples, excess_pct)

    with tab8:
        display_section("8. PCR Amplification", mix_pcr, steps_pcr, num_samples, excess_pct)

    # --- Sidebar Appendix ---
    with st.sidebar:
        st.markdown("---")
        with st.expander("ℹ️ General SPRI Cleanup"):
            st.markdown("""
            1. Incubate 10min with beads.
            2. Magnet -> Clear -> Discard sup.
            3. Add 200µl 80% EtOH (Fresh). Discard.
            4. Repeat EtOH wash.
            5. Dry 10 min.
            6. Elute in water.
            """)

if __name__ == "__main__":
    main()
