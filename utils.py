from pathlib import Path
from enum import Enum
from urllib.parse import urlparse
from bs4 import BeautifulSoup

import urllib3
import os
import json
import hashlib
import requests
import re
import zipfile
import base64

class URI_type(Enum):
    unknown = 0
    map_file = 1
    map_scoresaber = 2
    map_beatsaver = 3
    map_beatsaver_oneclick = 4
    map_beatsaver_key = 5
    map_bsaber = 6
    playlist_file = 7
    playlist_bsaber = 8

def encode_image_to_base64_str(img_path):
    img_path = Path(img_path)
    with open(img_path, mode="rb") as fp:
        img = fp.read()
    
    img_encoded = base64.b64encode(img)
    return img_encoded.decode()

def calculate_Level_hash_from_dir(levelPath):
    levelPath = Path(levelPath)
    infoPath = levelPath.joinpath("./info.dat")

    if not infoPath.is_file():
        print("info.dat at {} does not exist. Skipping. Note that this is not normal, please check the integrity of this level and consider re-downloading it.".format(levelPath))
        return None

    with open(infoPath, "rb") as tmpfile:
        info_binary = tmpfile.read()
        info_data = json.loads(info_binary, encoding="utf-8")

    # We need to calculate sha1 hashes of the concatenation of info.dat and each difficulty listed there
    hasher = hashlib.sha1()
    hasher.update(info_binary)

    # List difficulties
    difficulty_sets = info_data.get("_difficultyBeatmapSets")
    
    # Read each difficulty file
    for diffset in difficulty_sets:
        for beatmap in diffset.get("_difficultyBeatmaps"):
            beatmap_filename = beatmap.get("_beatmapFilename")
            beatmap_filepath = levelPath.joinpath(beatmap_filename)

            # Read difficulty file and concatenate to the binary info data
            with open(beatmap_filepath, "rb") as tmpfile:
                diff_binary = tmpfile.read()
                hasher.update(diff_binary)
    
    # Calculate the final hash
    sha1 = hasher.hexdigest().upper()

    return sha1

def calculate_Level_hash_from_zip(levelPath):
    levelPath = Path(levelPath)

    # Similar to calculate_Level_hash_from_dir(), but inside the zip

    with zipfile.ZipFile(str(levelPath), "r") as zip_file:
        with zip_file.open("Info.dat") as tmpfile:
            info_binary = tmpfile.read()
            info_data = json.loads(info_binary, encoding="utf-8")

        hasher = hashlib.sha1()
        hasher.update(info_binary)
        difficulty_sets = info_data.get("_difficultyBeatmapSets")

        for diffset in difficulty_sets:
            for beatmap in diffset.get("_difficultyBeatmaps"):
                beatmap_filename = beatmap.get("_beatmapFilename")

                # Read difficulty file and concatenate to the binary info data
                with zip_file.open(beatmap_filename, "r") as tmpfile:
                    diff_binary = tmpfile.read()
                    hasher.update(diff_binary)
    
    # Calculate the final hash
    sha1 = hasher.hexdigest().upper()

    return sha1



def get_map_or_playlist_resource_type(input_string):
    if os.path.exists(input_string):
        uri_path = Path(input_string)
        if not uri_path.is_file:
            return URI_type.unknown
        if uri_path.suffix == ".zip":
            return URI_type.map_file
        if uri_path.suffix == ".bplist":
            return URI_type.playlist_file
    
    parsed = urlparse(input_string)
    if parsed.hostname == "beatsaver.com":
        if parsed.scheme == "beatsaver":
            return URI_type.map_beatsaver_oneclick
        return URI_type.map_beatsaver

    
    if parsed.hostname == "bsaber.com":
        if parsed.path.split("/")[1] == "songs":
            return URI_type.map_bsaber
        else:
            # WARNING really unverified here
            return URI_type.playlist_bsaber
    
    if parsed.hostname == "scoresaber.com":
        if parsed.path.split("/")[1] == "leaderboard":
            return URI_type.map_scoresaber
    
    return URI_type.unknown
    

def get_level_hash_from_url(map_url, resource_type):
    parsed = urlparse(map_url)

    if resource_type is URI_type.map_beatsaver or resource_type is URI_type.map_bsaber:
        split = parsed.path.split("/")
        # URL may be https://beatsaver.com/beatmap/whatever or https://beatsaver.com/beatmap/whatever/
        key = split[-1] if split[-1] != "" else split[-2]
        return key
    
    if resource_type is URI_type.map_scoresaber:
        request = requests.get(map_url)
        soup = BeautifulSoup(request.text, "html.parser")

        ID_selector = soup.find(text="ID: ").next_element.next
        return str(ID_selector)

def get_level_hashes_from_playlist(bplist_path):
    with open(bplist_path, encoding="utf-8") as fp:
        playlist = json.load(fp)
    
    hashes = []
    for level in playlist["songs"]:
        hashes.append(level["hash"])
    
    return hashes

def extract_bsaber_bplist_url(baseurl):
    request = requests.get(baseurl)
    soup = BeautifulSoup(request.text, "html.parser")

    dl_button = soup.find("a", href=re.compile(r"/PlaylistAPI/"))
    dl_url = dl_button.attrs.get("href")
    
    absolute_url = "https://bsaber.com" + dl_url
    return absolute_url
