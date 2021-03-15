import wget
import requests
import json
import os
import zipfile
import time

from . import utils

from inspect import getfile
from pathlib import Path, PurePath
from json import JSONDecodeError

dir_script = Path(getfile(lambda: 0)).parent

# Cloudflare refuses access if we don't have a UserAgent
headers = {"User-Agent": "ARBSMapDo V1"}

# Used to avoid spamming beatsaver API
beatsaver_scraped_data_url = "https://raw.githubusercontent.com/andruzzzhka/BeatSaberScrappedData/master/beatSaverScrappedData.zip"


class Cache:
    def __init__(self, arbsmapdo_config):
        self._beatsaver_cache = dict()
        self._cache_updated = False
        self.tmp_dir = Path(arbsmapdo_config["tmp_dir"])
        self.tmp_dir.mkdir(exist_ok=True)
        self.download_dir = Path(arbsmapdo_config["download_dir"])
        self.beatsaver_cachefile = Path(arbsmapdo_config["beatsaver_cachefile"])
        self.levelhash_cachefile = Path(arbsmapdo_config["levelhash_cachefile"])
        self.rescan = arbsmapdo_config["rescan"]

        self._beatsaver_cache, self.local_cache_last_downloaded = self.load_beatsaver_cache_from_andruzzzhka_scrapes()
        self.levelhash_cache = self.load_levelhash_cache()
        self.update_levelhash_cache()

    def _update_andruzzzhka_scrapes(self):
        print("Updating Local BeatSaver Cache. This helps avoiding spamming the API hundreds of times.")
        print("Downloading beatSaverScrappedData (helps to avoid spamming beatsaver API)...")

        dl_filename = str(self.tmp_dir.joinpath("andruzzzhka_scrape.zip"))
        wget.download(beatsaver_scraped_data_url, dl_filename)

        # Unzip
        with zipfile.ZipFile(str(dl_filename), "r") as zip_file:
            zip_file.extractall(str(self.tmp_dir))
        
        # Replace old local cache by updated version
        os.replace(self.tmp_dir.joinpath("beatSaverScrappedData.json"), self.beatsaver_cachefile)
        last_updated = time.time()
        print("\nCache ready.")

    def load_beatsaver_cache_from_andruzzzhka_scrapes(self):
        # Check if update is neccessary
        update = False
        if self.beatsaver_cachefile.is_file() is False:
            update = True
        else:
            last_modified = self.beatsaver_cachefile.stat().st_mtime
            elapsed = time.time() - last_modified

            # Elapsed is given in seconds. The scrapes of andruzzzhka get updated once per day.
            if elapsed > 86400:
                update = True 
        
        # Update cache if neccessary
        if update:
            self._update_andruzzzhka_scrapes()
            last_modified = time.time()

        # Load local Cache
        with open(self.beatsaver_cachefile, "r", encoding="UTF-8") as tmpfile:
            scraped_cache_raw = json.load(tmpfile)

        cache_dict = dict()
        for levelinfo in scraped_cache_raw:
            cache_dict[levelinfo["hash"]] = levelinfo

        return cache_dict, last_modified

    # def _update_local_cache_file(self):
    #     print("Saving local cache...")
    #     with open(self.beatsaver_cachefile, "w+") as scrapedcache_fp:
    #         json.dump(self._beatsaver_cache, scrapedcache_fp)

    def _get_beatsaver_info_by_api(self, level_id):
        try:
            if len(level_id) == 40:
                # Is sha1-hash
                response = requests.get("https://beatsaver.com/api/maps/by-hash/{id}".format(id=level_id), headers=headers)
            else:
                # Treat as level key
                response = requests.get("https://beatsaver.com/api/maps/detail/{id}".format(id=level_id), headers=headers)
            json = response.json()
        except JSONDecodeError:
            print("Failed to get level {} from Beat Saver.".format(level_id))
            return None
        return json
    
    def get_beatsaver_info(self, level_id):
        """
        Uses information from the cache (hashes only) or calls the beatsaver API (hashes & keys)
        """

        level_hash = level_id.lower()
        info = self._beatsaver_cache.get(level_hash)

        if info is None:
            info = self._get_beatsaver_info_by_api(level_id)

            # Cache is only for hashes
            if info is not None and len(level_id) == 40:
                self._beatsaver_cache[level_id] = info
                self._cache_updated = True

        return info

    def load_levelhash_cache(self):
        if self.levelhash_cachefile.is_file():
            if self.rescan:
                self.levelhash_cachefile.unlink()
                return dict()

            with open(self.levelhash_cachefile, "r", encoding="UTF-8") as fp:
                hashcache = json.load(fp)
                return hashcache
        else:
            return dict()
    
    def save_levelhash_cache(self):
        # Save updates to the cachefile
        with open(self.levelhash_cachefile, "w+", encoding="UTF-8") as fp:
            json.dump(self.levelhash_cache, fp)

    def update_levelhash_cache(self):
        print("Scanning already existing maps...")
        # Iterate over all directories in the download directory, scanning for already existing levels
        for entry in self.download_dir.iterdir():
            # For each directory (which is an entire mapdir), see if hash was already calculated
            # If this is not the case -> calculate the hash and store to hashcache
            if entry.name not in self.levelhash_cache.keys():
                if entry.is_dir():
                    levelhash = utils.calculate_Level_hash_from_dir(self.download_dir.joinpath(entry.name))
                    self.levelhash_cache[entry.name] = levelhash
                if entry.is_file() and entry.suffix == ".zip":
                    levelhash = utils.calculate_Level_hash_from_zip(self.download_dir.joinpath(entry.name))
                    self.levelhash_cache[entry.name] = levelhash




