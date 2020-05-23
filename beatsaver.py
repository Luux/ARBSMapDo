import wget
import requests
import json
import os

from inspect import getfile
from pathlib import Path, PurePath
from json import JSONDecodeError

dir_script = Path(getfile(lambda: 0)).parent
dir_scrapedcache = dir_script.joinpath("./cache")

scrapedcache_filename = dir_scrapedcache.joinpath("beatsaver_data.json")

# Cloudflare refuses access if we don't have a UserAgent
headers = {"User-Agent": "ARBSMapDo V1"}

# Used to avoid spamming beatsaver API
beatsaver_scraped_data_url = "https://raw.githubusercontent.com/andruzzzhka/BeatSaberScrappedData/master/beatSaverScrappedData.json"


def load_cache_from_andruzzzhka_scrapes():
    print("Initialization of Local BeatSaver Cache. This helps avoiding spamming the API hundreds of times.")
    print("Downloading beatSaverScrappedData (helps to avoid spamming beatsaver API)...")
    tmpfn = dir_scrapedcache.joinpath("/.tmp")
    wget.download(beatsaver_scraped_data_url, str(tmpfn))
    
    with open(tmpfn, "r", encoding="UTF-8") as tmpfile:
        scraped_cache_raw = json.load(tmpfile)

    cache_dict = dict()
    for levelinfo in scraped_cache_raw:
        cache_dict[levelinfo["hash"]] = levelinfo

    tmpfn.unlink()

    return cache_dict


class BeatSaver:
    def __init__(self):
        self._beatsaver_cache = dict()
        self._cache_updated = False

        Path(dir_scrapedcache).mkdir(exist_ok=True)

        try:
            with open(scrapedcache_filename, "r") as scrapedcache_fp:
                self._beatsaver_cache = json.load(scrapedcache_fp)
        except (JSONDecodeError, FileNotFoundError):
            self._beatsaver_cache = load_cache_from_andruzzzhka_scrapes()
            self._update_local_cache_file()

    def _update_local_cache_file(self):
        print("Saving local cache...")
        with open(scrapedcache_filename, "w+") as scrapedcache_fp:
            json.dump(self._beatsaver_cache, scrapedcache_fp)

    def _get_beatsaver_info_by_api(self, level_id):
        try:
            response = requests.get("https://beatsaver.com/api/maps/by-hash/{id}".format(id=level_id), headers=headers)
            json = response.json()
        except JSONDecodeError:
            print("Failed to get level {} from Beat Saver.".format(level_id))
            return None
        return json
    
    def get_beatsaver_info(self, level_hash):
        level_hash = level_hash.lower()
        info = self._beatsaver_cache.get(level_hash)

        if info is None:
            info = self._get_beatsaver_info_by_api(level_hash)

            if info is not None:
                self._beatsaver_cache[level_hash] = info
                self._cache_updated = True

        return info

    





