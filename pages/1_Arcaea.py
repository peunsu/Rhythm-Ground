import streamlit as st
from streamlit_searchbox import st_searchbox
from streamlit_extras.grid import grid
import plotly.express as px
import plotly.figure_factory as ff

import pandas as pd
from unidecode import unidecode
import os
import re

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'arcaea')
DIFF_DICT = {
    0: ":blue[**Past**]",
    1: ":green[**Present**]",
    2: ":violet[**Future**]",
    3: ":red[**Beyond**]",
    4: ":red[**Beyond** *Moment*]",
    5: ":red[**Beyond** *Eternity*]"
    }

st.set_page_config(
    page_title="Arcaea",
    layout="wide"
)

@st.cache_resource
def get_song_data():
    return pd.read_csv(os.path.join(DATA_PATH, "song_data.csv"), encoding="utf-8-sig").sort_values(by="Title", key=lambda x: x.str.len())

@st.cache_resource
def get_pack_data():
    return pd.read_csv(os.path.join(DATA_PATH, "pack_data.csv"), encoding="utf-8-sig")

@st.cache_resource
def get_background_data():
    return pd.read_csv(os.path.join(DATA_PATH, "background_data.csv"), encoding="utf-8-sig")

def escape_markdown(_str: str) -> str:
    if pd.isnull(_str):
        return ""
    return _str.translate(str.maketrans({"*": r"\*", "-": r"\-", "_": r"\_", "~": r"\~", "(": r"\(", ")": r"\)", "#": r"\#", "[": r"\[", "]": r"\]"}))

def str_to_id(raw_id: str) -> str:
    return re.sub(r'[\W]+', '', unidecode(raw_id).lower())

song_data = get_song_data()
pack_data = get_pack_data()
background_data = get_background_data()

@st.cache_data
def search_title(searchterm: str):
    cond = song_data["ID"].str.contains(str_to_id(searchterm))
    return list(song_data[cond].loc[:, ["Title", "ID"]].drop_duplicates(subset="Title").itertuples(index=None, name=None))

with st.sidebar:
    st.header("Search")
    
    searchbox = st_searchbox(
        search_title,
        placeholder="Search song by title",
        label="Title",
        key="song_id"
    )

    sel_id = st.session_state.song_id["result"]
    cur_data = song_data.loc[song_data["ID"] == sel_id]
    
    radio_grid = grid(2)
    radio_grid.radio("Difficulty", cur_data["Difficulty"].sort_values().to_list(), format_func=lambda x: DIFF_DICT[x], key="song_diff")
    radio_grid.radio("Platform", ["Mobile", "Switch"], key="song_platform")

if st.session_state.song_id["result"] is None:
    st.info('To view Arcaea song data, search song by title on the sidebar.', icon="ℹ️")
else:
    sel_diff = st.session_state.song_diff
    cur_data = cur_data[cur_data["Difficulty"] == sel_diff]
    
    cur_title = cur_data["Title"].values[0]
    cur_artist = cur_data["Artist"].values[0]
    cur_vocals = cur_data["Vocals"].values[0]
    cur_vocals = "(None)" if pd.isna(cur_vocals) else cur_vocals
    cur_genre = cur_data["Genre"].values[0]
    
    cur_level = cur_data["Level"].values[0]
    cur_notes = cur_data["Notes_Touch"].values[0] if st.session_state.song_platform == "Mobile" else cur_data["Notes_Joycon"].values[0]
    cur_chart_constant = cur_data["Chart Constant"].values[0]
    min_bpm = cur_data["BPM_Min"].values[0]
    max_bpm = cur_data["BPM_Max"].values[0]
    cur_bpm = min_bpm if min_bpm == max_bpm else f"{min_bpm}-{max_bpm}"
    cur_length = cur_data["Length"].values[0]
    cur_version = cur_data["Version_Mobile"].values[0] if st.session_state.song_platform == "Mobile" else cur_data["Version_Switch"].values[0]
    cur_added = cur_data["Added_Mobile"].values[0] if st.session_state.song_platform == "Mobile" else cur_data["Added_Switch"].values[0]
    cur_chart_design = escape_markdown(cur_data["Chart Design"].values[0])
    
    cur_cover_art = cur_data["Image"].values[0]
    cur_artwork = cur_data["Artwork"].values[0]
    cur_artwork = "(None)" if pd.isna(cur_artwork) else cur_artwork
    cur_pack = cur_data["Pack"].values[0]
    cur_pack_url = pack_data.loc[pack_data['Pack'] == cur_pack, 'Image'].values[0]
    cur_background = cur_data["Background"].values[0]
    cur_background_url = background_data.loc[background_data['Background'] == cur_background, 'Image'].values[0].split("/revision")[0]

    col1, dummy, col2 = st.columns([0.8, 0.05, 0.15])
    
    dummy.empty()
    
    with col1.container():
        st.markdown(f"""
            ## {escape_markdown(cur_title)}
            * **Pack /** {cur_pack}
            * **Artist /** {escape_markdown(cur_artist)}\n
            * **Vocals /** {escape_markdown(cur_vocals)}\n
            * **Genre /** {escape_markdown(cur_genre)}\n
            """)
    
    col1.divider()
    
    if pd.isna(cur_notes):
        col1.error("This chart is not available in Switch version.", icon="🚨")
    else:
        with col1.container():
            st.subheader("Chart Info")
            
            cur_grid = grid(3, 2, 2)
            
            cur_grid.metric(label="Level", value=cur_level)
            cur_grid.metric(label="Notes", value=int(cur_notes))
            cur_grid.metric(label="Chart Constant", value=cur_chart_constant)
            
            cur_grid.metric(label="BPM", value=cur_bpm)
            cur_grid.metric(label="Length", value=cur_length)
            
            cur_grid.metric(label="Added Version", value=cur_version)
            cur_grid.metric(label="Added Date", value=cur_added)
            
            st.caption(f"Chart designed by **{cur_chart_design}**")
            
    #col1.divider()
            
    with col2.container():
        st.image(cur_cover_art, caption=f"Cover Art by {cur_artwork}")
        st.image(cur_pack_url, caption=cur_pack)
        st.image(cur_background_url, caption=f"Background: {cur_background}")
        
st.divider()
        
st.subheader("Raw Data")
st.dataframe(cur_data, column_config={"Image": st.column_config.ImageColumn(width="small")})
