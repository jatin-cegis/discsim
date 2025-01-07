import streamlit as st
import os
from PIL import Image
from dotenv import load_dotenv
load_dotenv()


script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
logo_path = os.path.join(root_dir, "logo.jpg")
im = Image.open(logo_path)

logo_page_path = os.path.join(root_dir, "logo_page.png")
im_page = Image.open(logo_page_path)

def set_page_config():
    st.logo(im_page)

    st.set_page_config(
        page_title="DiscSim | CEGIS",
        layout="wide",
        page_icon=im,
        initial_sidebar_state="expanded",
    )
    loadcss(os.path.join(root_dir, "custom.css"))
    userAvatar()

def loadcss(file_path: str):
    try:
        with open(file_path) as f:
            css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
    except Exception as e:
        st.error(f"An error occurred while loading CSS: {e}")

def userAvatar():
     if 'user_name' not in st.session_state:
          st.session_state['user_name'] = "CEGIS"
     @st.dialog("Update Username")
     def userDialog():
          userInput= st.text_input("Enter your name",st.session_state['user_name'])
          if st.button("Save"):
               st.session_state['user_name']=userInput
               st.write(st.session_state['user_name'])
               st.rerun()

     with st.chat_message("human",avatar="https://avatar.iran.liara.run/public"):
          if st.button(st.session_state['user_name'] +  ':material/expand_more:'):
               userDialog()