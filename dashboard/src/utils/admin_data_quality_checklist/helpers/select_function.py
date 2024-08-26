import streamlit as st

def sidebar_functionality_select():
    st.sidebar.header("Select Functionality")
    functionality = st.sidebar.selectbox(
        "Choose a functionality",
        [
            "Unique ID Verifier",
            "Check Specific Columns as Unique ID",
            "Drop/Export Duplicate Entries",
            "Drop/Export Duplicate Rows",
            "Missing Entries Analysis",
            "Zero Entries Analysis",
            "Indicator Fill Rate Analysis",
            "Frequency Table Analysis"
        ]
    )
    return functionality