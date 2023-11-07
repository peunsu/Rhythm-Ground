import streamlit as st
from streamlit_searchbox import st_searchbox
from streamlit_extras.grid import grid

from plotly.graph_objects import Figure
import plotly.express as px
import pandas as pd
import numpy as np

from packaging.version import parse as parse_version
from unidecode import unidecode
from datetime import datetime, timedelta
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
    page_title="Arcaea - Rhythm Ground",
    page_icon="https://play-lh.googleusercontent.com/6vtKnbt-Rd5y5KIDHUy5adgZAmHBKBMmat0MiRh53qPYr6KqIvgSsYcqAQCsP_CeXXM=s48-rw",
    layout="wide",
    menu_items={
        "Get help": "https://github.com/peunsu/Rhythm-Ground",
        "Report a Bug": "https://github.com/peunsu/Rhythm-Ground/issues",
        "About": """
            ### Rhythm Ground
            InDev Version.\n
            Data provided by [Fandom](https://arcaea.fandom.com/).\n
            Github: https://github.com/peunsu/Rhythm-Ground"""
    }
)

class ArcaeaSong:
    id: str
    data: pd.DataFrame
    _difficulty_list: list
    
    def __init__(self, id: str):
        self.id = id
        self.data = get_data_slice(song_data, "ID", st.session_state.song_id["result"])
        self._difficulty_list = self.data["Difficulty"].sort_values().to_list()
    
    def get_difficulty_list(self):
        return self._difficulty_list
    
    def set_difficulty(self):
        self.data = get_data_slice(self.data, "Difficulty", st.session_state.song_diff)
    
    @property
    def title(self) -> str:
        return self.data["Title"].values[0]
    
    @property
    def artist(self) -> str:
        return self.data["Artist"].values[0]

    @property
    def vocals(self) -> str:
        vocals = self.data["Vocals"].values[0]
        return "(None)" if pd.isna(vocals) else vocals

    @property
    def genre(self) -> str:
        return self.data["Genre"].values[0]
    
    @property
    def difficulty(self) -> str:
        return self.data["Difficulty"].values[0]
    
    @property
    def level(self) -> str:
        return convert_level(self.data["Level"].values[0])
    
    @property
    def notes(self) -> str:
        return self.data["Notes_Touch"].values[0] if st.session_state.song_platform == "Mobile" else self.data["Notes_Joycon"].values[0]
    
    @property
    def chart_constant(self) -> str:
        return self.data["Chart Constant"].values[0]

    @property
    def bpm(self) -> str:
        min_bpm = self.data["BPM_Min"].values[0]
        max_bpm = self.data["BPM_Max"].values[0]
        return min_bpm if min_bpm == max_bpm else f"{min_bpm}-{max_bpm}"
    
    @property
    def length(self) -> str:
        return self.data["Length"].dt.strftime('%M:%S').values[0]
    
    @property
    def version(self) -> str:
        return self.data["Version_Mobile"].values[0] if st.session_state.song_platform == "Mobile" else self.data["Version_Switch"].values[0]
    
    @property
    def added(self) -> str:
        return self.data["Added_Mobile"].dt.strftime("%Y-%m-%d").values[0] if st.session_state.song_platform == "Mobile" else self.data["Added_Switch"].dt.strftime("%Y-%m-%d").values[0]
    
    @property
    def chart_design(self) -> str:
        return escape_markdown(self.data["Chart Design"].values[0])
    
    @property
    def artwork_image_url(self) -> str:
        return self.data["Image"].values[0]
    
    @property
    def artwork(self) -> str:
        artwork = self.data["Artwork"].values[0]
        return "(None)" if pd.isna(artwork) else artwork
    
    @property
    def pack(self) -> str:
        return self.data["Pack"].values[0]
    
    @property
    def pack_image_url(self) -> str:
        return get_data_slice(pack_data, "Pack", self.pack)["Image"].values[0]
    
    @property
    def background(self) -> str:
        return self.data["Background"].values[0]
    
    @property
    def background_image_url(self) -> str:
        return get_data_slice(background_data, "Background", self.background)["Image"].values[0]

@st.cache_data
def get_song_data():
    df = pd.read_csv(os.path.join(DATA_PATH, "song_data.csv"), encoding="utf-8-sig").sort_values(by="Title", key=lambda x: x.str.len())
    df["Length"] = pd.to_datetime(df['Length'], format='%M:%S', errors='coerce')
    df["Version_Mobile"] = df["Version_Mobile"].astype(str)
    df["Version_Switch"] = df["Version_Switch"].astype(str)
    df["Added_Mobile"] = pd.to_datetime(df["Added_Mobile"], format='%Y-%m-%d')
    df["Added_Switch"] = pd.to_datetime(df["Added_Mobile"], format='%Y-%m-%d')
    df["Notes_Touch"] = pd.to_numeric(df['Notes_Touch'], errors='coerce').astype('Int64')
    df["Notes_Joycon"] = pd.to_numeric(df['Notes_Joycon'], errors='coerce').astype('Int64')
    df["Level"] = pd.to_numeric(df["Level"], errors="coerce").astype('Int64')
    return df

@st.cache_data
def get_pack_data():
    return pd.read_csv(os.path.join(DATA_PATH, "pack_data.csv"), encoding="utf-8-sig")

@st.cache_data
def get_background_data():
    return pd.read_csv(os.path.join(DATA_PATH, "background_data.csv"), encoding="utf-8-sig")

@st.cache_data
def get_data_slice(data: pd.DataFrame, cols: str, value) -> pd.DataFrame:
    return data.loc[data[cols] == value]

@st.cache_data
def plotly_fig(cur_data: pd.DataFrame, var1: str, var2: str) -> Figure:
    col = var2
    if var2 == "Notes":
        col = "Notes_Touch" if st.session_state.song_platform == "Mobile" else "Notes_Joycon"
    if var2 == "Maximum BPM":
        col = "BPM_Max"
    if var2 == "Minimum BPM":
        col = "BPM_Min"
    
    chart_data = get_data_slice(song_data, var1, cur_data[var1].values[0]).sort_values(by=col, ascending=False).reset_index()
    cur_index = get_data_slice(chart_data, 'index', cur_data.index[0]).index[0]
    cur_value = cur_data[col].values[0]
    top_percentile = cur_index * 100 / chart_data[col].notna().sum()
    
    fig = px.line(
        chart_data,
        x=chart_data.index,
        y=col,
        title=f"Compare <i>{var2}</i> within the same <i>{var1}</i>",
        orientation="v"
        )
    
    if col == "Length":
        cur_value = datetime64_to_datetime(cur_value)
        fig.update_yaxes(tickformat="%M:%S")
        
    fig.update_xaxes(title=f"{chart_data[col].notna().sum()} entries", minallowed=0)
    fig.update_yaxes(title=var2)
    fig.update_layout(bargap=0)
    fig.update_traces(
        customdata=chart_data["Title"],
        hovertemplate ='<b>Title</b>: %{customdata}<br><b>Value</b>: %{y}<br><b>Ranking</b>: %{x}'
    )
    fig.add_annotation(
        x=cur_index,
        y=cur_value,
        align="center",
        text=f"<b>Top {top_percentile:.1f}%</b>",
        arrowcolor="#b0b3b8",
        font=dict(
            size=16
        )
    )
    fig.add_hline(
        y=cur_value,
        line_dash="dot",
        line_width=1,
        line_color="#b0b3b8"
    )
    return fig

@st.cache_data
def parse_get_versions(df: pd.DataFrame, column: str):
    return df[column].apply(lambda x: parse_version(x) if x != "nan" else parse_version("0"))

def escape_markdown(_str: str) -> str:
    if pd.isnull(_str):
        return ""
    return _str.translate(str.maketrans({"*": r"\*", "-": r"\-", "_": r"\_", "~": r"\~", "(": r"\(", ")": r"\)", "#": r"\#", "[": r"\[", "]": r"\]"}))

def str_to_id(raw_id: str) -> str:
    return re.sub(r'[\W]+', '', unidecode(raw_id).lower())

def convert_level(level: int) -> str:
    if level % 2 == 0:
        return str(level // 2)
    else:
        return str(level // 2) + "+"

def datetime64_to_datetime(datetime64):
    return datetime.utcfromtimestamp((datetime64 - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 's'))

def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Add filters")

    if not modify:
        return df

    df = df.copy()

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            if column in ["Side", "Difficulty"]:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif column in ["Level"]:
                _min = df[column].min()
                _max = df[column].max()
                user_num_input = right.select_slider(
                    f"Values for {column}",
                    sorted(df[column].unique()),
                    value=(_min, _max),
                    format_func=convert_level
                )
                df = df[df[column].between(*user_num_input)]
            elif column in ["Notes_Touch", "Notes_Joycon"]:
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif column in ["Chart Constant", "BPM_Min", "BPM_Max"]:
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif column in ["Version_Mobile", "Version_Switch"]:
                versions = parse_get_versions(df, column)
                valid_versions = versions[versions > parse_version("0")]
                _min = valid_versions.min()
                _max = valid_versions.max()
                user_num_input = right.select_slider(
                    f"Values for {column}",
                    sorted(valid_versions.unique()),
                    value=(_min, _max)
                )
                df = df[versions.between(*user_num_input)]
            elif column in ["Length"]:
               _min = datetime64_to_datetime(df[column].min())
               _max = datetime64_to_datetime(df[column].max())
               step = timedelta(seconds=1)
               user_num_input = right.slider(
                   f"Values for {column}",
                   min_value=_min,
                   max_value=_max,
                   value=(_min, _max),
                   step=step,
                   format="mm:ss"
               )
               df = df[df[column].between(*user_num_input)]
            elif column in ["Added_Mobile", "Added_Switch"]:
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]

    return df

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

    song = ArcaeaSong(st.session_state.song_id["result"])
    
    radio_grid = grid(2)
    radio_grid.radio("Difficulty", song.get_difficulty_list(), format_func=lambda x: DIFF_DICT[x], key="song_diff")
    radio_grid.radio("Platform", ["Mobile", "Switch"], key="song_platform", disabled=(st.session_state.song_id["result"] is None))

if st.session_state.song_id["result"] is None:
    st.info('To view Arcaea song data, search song by title on the sidebar.', icon="ℹ️")
    st.divider()
    st.dataframe(filter_dataframe(song_data), hide_index=True)
else:
    song.set_difficulty()

    col1, dummy, col2 = st.columns([0.8, 0.05, 0.15])
    
    dummy.empty()
    
    with col1.container():
        st.markdown(f"""
            ## {escape_markdown(song.title)}
            * **Pack /** {song.pack}
            * **Artist /** {escape_markdown(song.artist)}\n
            * **Vocals /** {escape_markdown(song.vocals)}\n
            * **Genre /** {escape_markdown(song.genre)}\n
            """)
        
    col1.divider()
    
    
    if pd.isna(song.notes):
        with col1.container():
            st.error("This chart is not available in Switch version.", icon="🚨")
    else:
        with col1.container():
            st.subheader("Chart Info")
            
            cur_grid = grid(3, 2, 2)
            
            cur_grid.metric(label="Level", value=song.level)
            cur_grid.metric(label="Notes", value=int(song.notes))
            cur_grid.metric(label="Chart Constant", value=song.chart_constant)
            
            cur_grid.metric(label="BPM", value=song.bpm)
            cur_grid.metric(label="Length", value=song.length)
            
            cur_grid.metric(label="Added Version", value=song.version)
            cur_grid.metric(label="Added Date", value=song.added)
            
            st.caption(f"Chart designed by **{song.chart_design}**")
        
        col1.divider()
        
        with col1.container():
            st.subheader("Compare")
            
            cur_grid = grid(2)
            cur_grid.selectbox(label="Group", options=["Difficulty", "Level", "Pack"], key="plot_var1")
            cur_grid.selectbox(label="Value", options=["Chart Constant", "Notes", "Minimum BPM", "Maximum BPM", "Length"], key="plot_var2")
            
            st.plotly_chart(plotly_fig(song.data, st.session_state.plot_var1, st.session_state.plot_var2), use_container_width=True)
        
    with col2.container():
        st.image(song.artwork_image_url, caption=f"Cover Art by {song.artwork}")
        st.image(song.pack_image_url, caption=f"Pack: {song.pack}")
        st.image(song.background_image_url, caption=f"Background: {song.background}")
        
    st.divider()
            
    st.subheader("Raw Data")
    st.dataframe(song.data, column_config={"Image": st.column_config.ImageColumn(width="small")})
