import streamlit as st
from streamlit_searchbox import st_searchbox
import pandas as pd
from unidecode import unidecode
import os
import re

DATA_PATH = "/workspaces/Rhythm-Ground/data/arcaea"
DIFF_DICT = {
    0: ":blue[**Past**]",
    1: ":green[**Present**]",
    2: ":violet[**Future**]",
    3: ":red[**Beyond**]",
    4: ":red[**Beyond (Moment)**]",
    5: ":red[**Beyond (Eternity)**]"
    }

st.set_page_config(
    page_title="Arcaea"
)

@st.cache_resource
def get_song_data():
    return pd.read_csv(os.path.join(DATA_PATH, "song_data.csv"), encoding="utf-8-sig").sort_values(by="Title", key=lambda x: x.str.len())

@st.cache_resource
def get_pack_data():
    return pd.read_csv(os.path.join(DATA_PATH, "pack_data.csv"), encoding="utf-8-sig")

@st.cache_data
def search_title(searchterm: str):
    cond = song_data["ID"].str.contains(re.sub(r'[\W]+', '', unidecode(searchterm).lower()))
    return list(song_data[cond].loc[:, ["Title", "ID"]].drop_duplicates(subset="Title").itertuples(index=None, name=None))

st.caption("Rhythm Ground")
st.title("Arcaea")

song_data = get_song_data()
pack_data = get_pack_data()

sel_id = st_searchbox(
    search_title,
    placeholder="Search song by title",
    label="Title"
)

if sel_id:
    sel_data = song_data.loc[song_data["ID"] == sel_id]

    sel_diff = st.radio("Difficulty", sel_data["Difficulty"].to_list(), format_func=lambda x: DIFF_DICT[x])
    cur_data = sel_data[sel_data["Difficulty"] == sel_diff]
    
    with st.container() as container:
        col1, col2, col3 = st.columns(3)
        
        cur_title = cur_data["Title"].values[0]
        col1.subheader("Title")
        col1.text(cur_title)
        col1.image(cur_data["Image"].values[0])
        
        cur_pack = cur_data["Pack"].values[0]
        cur_artist = cur_data["Artist"].values[0]
        col3.subheader("Pack")
        col3.text(cur_pack)
        col3.image(pack_data.loc[pack_data['Pack'] == cur_pack, 'Image'].values[0])

    st.subheader("Raw Data")
    st.dataframe(cur_data)