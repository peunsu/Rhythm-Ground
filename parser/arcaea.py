# Fix AttributeError
import collections
import collections.abc
collections.Callable = collections.abc.Callable

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
import requests
import re
import os
from unidecode import unidecode

class ArcaeaDataParser():    
    def __init__(self):
        """Arcaea Data Parser.
        """
        self.song_list = list()
        self.song_data = pd.DataFrame()
        self.pack_data = pd.DataFrame()
        self.background_data = pd.DataFrame()
    
    def html_request(self, page: str, wiki: str = "arcaea") -> str:
        """Sends a GET request and return HTML response in string.
        
        Args:
            page (str): A name of page of the given wiki.
            wiki (str, optional): An ID of Fandom wiki. Defaults to "arcaea".

        Returns:
            str: HTML response in string.
        """
        
        BASE_URL = "https://{wiki}.fandom.com/wiki/{page}"
        
        url = BASE_URL.format(
            wiki = wiki,
            page = page.replace(" ","_").replace("?","%3F")
        )
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    
    def str_to_id(self, raw_id: str) -> str:
        """Transform input string to ID.

        Args:
            raw_id (str): A String to transform.

        Returns:
            str: Transformed ID in string.
        """
        return re.sub(r'[\W]+', '', unidecode(raw_id).lower())
    
    def get_songlist(self) -> list:
        """Get a list of Arcaea song titles.

        Returns:
            list: A list of Arcaea song titles.
        """
        
        response = self.html_request("Songs by Date")
        soup = BeautifulSoup(response, "html.parser")
        table = soup.find("table", class_="songbydate-table")
        
        self.song_list = list(set([title["title"] for title in table.select("tr td:nth-child(2) a")]))
        
        return self.song_list
    
    def get_song_data(self) -> pd.DataFrame:
        """Get Arcaea song data in pandas DataFrame.

        Returns:
            pd.DataFrame: Arcaea song data.
        """

        def parse_tables(soup: BeautifulSoup, title: str) -> pd.DataFrame:
            """Parse HTML tables to pandas DataFrame.

            Args:
                soup (BeautifulSoup): A BeautifulSoup object of HTML tables to parse.
                title (str): Title of data being parsed.

            Returns:
                pd.DataFrame: The result of parsing given tables.
            """
            head_list = ["ID", "Title", "Pack", "Artist", "Image"]
            data_list = [
                [self.str_to_id(title)],
                [soup.find("span", class_="song-template-title").text],
                [soup.find("span", class_="song-template-pack").text],
                [soup.find("span", class_="song-template-artist").text],
                [soup.find("figure").find("a")["href"]]
                ]

            tables = soup.find_all("table", class_="pi-horizontal-group")

            for table in tables:
                th_list = [el.text for el in table.find_all('th')]
                tds = table.find_all('td')
                td_list = []
                for td in tds:
                    for ref in td.find_all("sup", class_="reference"):
                        ref.decompose()
                    spans = td.find_all('span')
                    temp = [span.text for span in spans if not span.find('b')]
                    td_list.append(temp if temp else [td.text])
                head_list.extend(th_list)
                data_list.extend(td_list)

            max_len = max(len(data) for data in data_list)
            for data in data_list:
                if len(data) == 1:
                    data *= max_len
            
            head_list.append("Difficulty")
            if max_len == 1:
                data_list.append([3])
            else:
                data_list.append([0, 1, 2])

            return pd.DataFrame(zip(*data_list), columns=head_list)
        
        def process_data(df: pd.DataFrame) -> pd.DataFrame:
            """Process given pandas DataFrame.

            Args:
                df (pd.DataFrame): A pandas DataFrame to process.

            Returns:
                pd.DataFrame: Processed DataFrame.
            """
            
            df = df.map(lambda x: x.replace(u"\xa0", u"") if isinstance(x, str) else x)
            df = df.join(pd.DataFrame(df['Notes'].map(lambda x: re.findall(r"\d+", x)).values.tolist(), columns=["Notes_Touch", "Notes_Joycon"]))
            df = df.join(pd.DataFrame(df['Added'].map(lambda x: re.findall(r"\d+\.\d+\.\d+[a-z]?", x)[-2:]).values.tolist(), columns=["Version_Mobile", "Version_Switch"]))
            df = df.join(pd.DataFrame(df['Added'].map(lambda x: re.findall(r"\d+-\d+-\d+", x)[-2:]).values.tolist(), columns=["Added_Mobile", "Added_Switch"]))
            df = df.join(pd.DataFrame(df['BPM'].map(lambda x: re.findall(r"\d+", x)[-2:]).values.tolist(), columns=["BPM_Min", "BPM_Max"]))
            df["Notes_Joycon"] = df["Notes_Joycon"].mask(df["Version_Switch"].notna(), df["Notes_Joycon"].fillna(df["Notes_Touch"]))
            df["BPM_Max"].fillna(df["BPM_Min"], inplace=True)
            df.drop(["Notes", "Added", "BPM"], axis=1, inplace=True)
            
            return df
        
        pbar = tqdm(self.get_songlist(), leave=True)
        for title in pbar:
            pbar.set_description(f"Current Page: {title}")
            response = self.html_request(title)
            soup = BeautifulSoup(response, "html.parser")

            divs = soup.find_all("div", class_="wds-tab__content", attrs={"data-item-name": True})
            if divs:
                for div in divs:
                    self.song_data = pd.concat([self.song_data, parse_tables(div, title)], ignore_index=True)
            else:
                self.song_data = pd.concat([self.song_data, parse_tables(soup, title)], ignore_index=True)
        
        self.song_data = process_data(self.song_data)
        
        # Process Exception (Last)
        self.song_data.loc[(self.song_data["ID"] == "last") & (self.song_data["Difficulty"] == 3), "Difficulty"] = [4, 5]
        
        return self.song_data
    
    def get_pack_data(self) -> pd.DataFrame:
        """Get Arcaea song pack image data as pandas DataFrame.

        Returns:
            pd.DataFrame: Arcaea song pack data.
        """
        
        if self.song_data.empty:
            self.get_song_data()
            
        pack_list = self.song_data["Pack"].unique()
        image_list = []
        id_list = [self.str_to_id(pack) for pack in pack_list]
        
        pbar = tqdm(pack_list, leave=True)
        for pack in pbar:
            pbar.set_description(f"Current Page: {pack}")
            if pack.startswith("Memory Archive:"):
                pack = "Memory Archive"
            response = self.html_request(pack)
            soup = BeautifulSoup(response, "html.parser")
            image_list.append(soup.find("a", class_="image")['href'])
        
        self.pack_data = pd.DataFrame(zip(id_list, pack_list, image_list), columns=["ID", "Pack", "Image"])
            
        return self.pack_data
    
    def get_background_data(self) -> pd.DataFrame:
        """Get Arcaea background image data as pandas DataFrame.

        Returns:
            pd.DataFrame: Arcaea background image data.
        """
        
        response = self.html_request("Song Backgrounds")
        soup = BeautifulSoup(response, "html.parser")
        tables = soup.find_all("table", class_="article-table")

        image_list = []
        bg_list = []

        for table in tables[:3]:
            tds = table.select("tr td:nth-child(1)")
            for td in tds:
                name = td.find("span", attrs={"style": (lambda x: x.startswith("color:") if isinstance(x, str) else False)}).text
                image_list.append(td.find('a')['href'])
                bg_list.append(name)

        self.background_data = pd.DataFrame(zip(bg_list, image_list), columns=["Background", "Image"])
        
        return self.background_data

if __name__ == "__main__":
    arcaea = ArcaeaDataParser()
    DATA_PATH = "/workspaces/Rhythm-Ground/data/arcaea"
    arcaea.get_song_data().to_csv(os.path.join(DATA_PATH, "song_data.csv"), index=False)
    #arcaea.get_pack_data().to_csv(os.path.join(DATA_PATH, "pack_data.csv"), index=False)
    #arcaea.get_background_data().to_csv(os.path.join(DATA_PATH, "background_data.csv"), index=False)