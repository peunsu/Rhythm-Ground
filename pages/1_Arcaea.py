import streamlit as st
from streamlit_searchbox import st_searchbox
import pandas as pd
from unidecode import unidecode
import os

st.set_page_config(
    page_title="Arcaea"
)

st.caption("Rhythm Ground")
st.title("Arcaea")

DATA_PATH = "/workspaces/Rhythm-Ground/data/arcaea"
DIFF_DICT = {0: ":blue[**Past**]", 1: ":green[**Present**]", 2: ":violet[**Future**]", 3: ":red[**Beyond**]"}

song_data = pd.read_csv(os.path.join(DATA_PATH, "song_data.csv"), encoding="utf-8-sig")
pack_data = pd.read_csv(os.path.join(DATA_PATH, "pack_data.csv"), encoding="utf-8-sig")

def search_title(searchterm: str):
    searchterm = searchterm.lower().replace(" ", "")
    cond1 = song_data["Title"].str.lower().replace(" ", "").str.contains(searchterm)
    cond2 = song_data["ID"].str.contains(searchterm)
    return song_data[cond1 | cond2].loc[:, "Title"].unique()

selected_title = st_searchbox(
    search_title,
    placeholder="Search song by title",
    label="Title"
)

if selected_title:    
    selected_id = song_data.loc[song_data["Title"] == selected_title, "ID"].values[0]
    selected_data = song_data.loc[song_data["ID"] == selected_id]

    difficulty = st.radio("Difficulty", selected_data["Difficulty"].to_list(), format_func=lambda x: DIFF_DICT[x])
    cur_data = selected_data[selected_data["Difficulty"] == difficulty]
    
    with st.container() as container:
        col1, col2, col3 = st.columns(3)
        
        title = cur_data["Title"].values[0]
        col1.subheader("Title")
        col1.text(title)
        col1.image(cur_data["Image"].values[0])
        
        pack = cur_data["Pack"].values[0]
        artist = cur_data["Artist"].values[0]
        col3.subheader("Pack")
        col3.text(pack)
        col3.image(pack_data.loc[pack_data['Pack'] == pack, 'Image'].values[0])

    st.subheader("Raw Data")
    st.dataframe(cur_data)