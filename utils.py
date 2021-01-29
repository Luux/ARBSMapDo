from pathlib import Path
from enum import Enum
from urllib.parse import urlparse

import urllib3
import os
import json
import hashlib

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


def calculate_Level_hash(levelPath):
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
    

def get_level_key_from_url(map_url, resource_type):
    parsed = urlparse(map_url)

    if resource_type is URI_type.map_beatsaver or resource_type is URI_type.map_bsaber:
        split = parsed.path.split("/")
        # URL may be https://beatsaver.com/beatmap/whatever or https://beatsaver.com/beatmap/whatever/
        key = split[-1] if split[-1] != "" else split[-2]
        return key
    
    if resource_type is URI_type.map_scoresaber:
        # TODO
        return NotImplementedError


    


#print(get_map_or_playlist_resource_type("https://beatsaver.com/beatmap/26d2"))

url = "https://bsaber.com/songs/133ee/"
print(get_level_key_from_url(url, get_map_or_playlist_resource_type(url)))

