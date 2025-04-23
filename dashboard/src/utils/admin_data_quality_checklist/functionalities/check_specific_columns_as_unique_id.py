import os
import streamlit as st
import pandas as pd
import numpy as np
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")

UNIQUE_ID_CHECK_ENDPOINT = f"{API_BASE_URL}/unique_id_check"

#Updates the session before relaoding the page -> helps to redirect page
def handle_click(newSelection):
    st.session_state.option_selection = newSelection

def check_specific_columns_as_unique_id(df):
    customcss = """
        <style>
        div[data-testid="stExpander"] summary{
            padding:0.4rem 1rem;
        }
        .stHorizontalBlock{
            //margin-top:-30px;
        }
        .st-key-functioncall button{
        margin-top:28px;
        }
        .st-key-functioncall button,.st-key-dropentryBtn button,.st-key-verifyIDBtn button{
            background-color:#3b8e51;
            color:#fff;
            border:none;
        }
        .st-key-functioncall button:hover,.st-key-functioncall button:active,.st-key-functioncall button:focus,st-key-functioncall button:focus:not(:active),
        .st-key-dropentryBtn button:hover,.st-key-dropentryBtn button:active,.st-key-dropentryBtn button:focus,st-key-dropentryBtn button:focus:not(:active),
        .st-key-verifyIDBtn button:hover,.st-key-verifyIDBtn button:active,.st-key-verifyIDBtn button:focus,st-key-verifyIDBtn button:focus:not(:active){
            color:#fff!important;
            border:none;
        }
        .st-key-uidCol label p::after{ 
            content: " *";
            color: red;
        }
        </style>
    """
    st.markdown(customcss, unsafe_allow_html=True)

    st.session_state.drop_export_rows_complete = False
    st.session_state.drop_export_entries_complete = False
    title_info_markdown = """
        Use this feature to check whether the column(s) you think form the unique ID is indeed the unique ID.
        - Verifies if selected column(s) can serve as a unique identifier for the dataset.
        - You can select up to 4 columns to check.
        - The function will return whether the selected column(s) can work as a unique ID.
        - Valid input format: CSV file
        - A minimum of ONE column must be selected.
    """
    st.markdown("<h2 style='text-align: center;font-weight:800;color:#136a9a;margin-top:-15px'>Verify Unique ID(s)</h2>", unsafe_allow_html=True, help=title_info_markdown)
    st.markdown("<p style='color:#3b8e51;margin-bottom:20px'>This function helps you verify if the column(s) that you selected serve(s) as a unique ID for your dataset. If you expect some column(s) to be a unique ID in your dataset, this function helps you verify the same.</p>", unsafe_allow_html=True)
    

    selectField, updateBtn = st.columns([2,1])
    columns = selectField.multiselect("Select column(s) to verify [multiple selections are allowed - up to 4]", options=df.columns.tolist(),key="uidCol")
    
    if columns and updateBtn.button("Check Unique ID",key="functioncall"):
        with st.spinner("Checking unique ID..."):
            df_clean = df.replace([np.inf, -np.inf], np.nan).dropna()
            data = df_clean.where(pd.notnull(df_clean), None).to_dict('records')
            payload = {"data": data, "columns": columns}
            response = requests.post(UNIQUE_ID_CHECK_ENDPOINT, json=payload)
            
            if response.status_code == 200:
                result = response.json()['result']
                if result[1]:
                    st.success("Yes, the selected column(s) can work as a Unique ID")
                    st.write(result[0])
                else:
                    st.error("No, the select column(s) cannot work as a Unique ID")

                    paraField, colBtn = st.columns([2,1])
                    paraField.write("In case you want to drop/export the duplicate entries from the column(s), you can use the Inspect Duplicate Entries function")
                    dropentry = "Inspect Duplicate Entries"
                    colBtn.button(dropentry, on_click=handle_click, args=[dropentry],key="dropentryBtn")

                    paraField.write("In case you want to identify the Unique ID(s) in your file, you can use the Identify Unique ID(s) function")
                    verifyID = "Identify Unique ID(s)"
                    colBtn.button(verifyID, on_click=handle_click, args=[verifyID],key="verifyIDBtn")
            else:
                error_detail = response.json().get("detail", "Unknown error")
                st.error(f"Error: {response.status_code} - {error_detail}")