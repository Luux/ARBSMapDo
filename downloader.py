import requests
import sys
import os
import string
import progressbar
import threading
import zipfile

from inspect import getfile
from pathlib import Path

dir_script = Path(getfile(lambda: 0)).parent

# Cloudflare refuses access if we don't have a UserAgent
headers = {"User-Agent": "ARBSMapDo V1"}


class advanced_downloader():
    def __init__(self, config: dict):
        
        self.download_dir = Path(config["download_dir"])
        self.ranked_only = config["ranked_only"]
        self.scoresaber_sorting = config["scoresaber_sorting"]
        self.levels_to_download = config["levels_to_download"]
        self.scoresaber_limit = config["scoresaber_limit"]
        self.tmp_dir = dir_script.joinpath(config["tmp_dir"])
        self.max_threads = config["max_threads"]
        self.stars_min = config["stars_min"]
        self.stars_max = config["stars_max"]

    def start(self):
        levels_to_download = self.fetch_and_filter()
        self.download_levels(levels_to_download)

    def download_levels(self, levels: list):
        print("Downloading levels...")
        next_level_number = 0
        finished = 0
        current_threads = []

        Path(self.tmp_dir).mkdir(exist_ok=True)

        with progressbar.ProgressBar(max_value=len(levels), redirect_stdout=True) as bar:
            while (finished < len(levels)):
                if(next_level_number < len(levels) and len(current_threads) < self.max_threads):
                    level = levels[next_level_number]
                    download_url = "https://beatsaver.com" + level["beatsaver_info"]["directDownload"]
                    name = self._get_level_dirname(level)
                    print("Downloading " + name)
                    thread = threading.Thread(target=self._download_level, args=[download_url, name])
                    current_threads.append(thread)
                    thread.start()
                    next_level_number += 1
                else:
                    i = 0
                    while i < len(current_threads):
                        if current_threads[i].is_alive() is False:
                            current_threads.pop(i)
                            finished += 1
                        else:
                            i += 1
                bar.update(finished)
            try:
                Path(self.tmp_dir).rmdir()
            except:
                print("WARNING: Error while cleaning up. Cannot delete tmp directory.")

    def _download_level(self, url, name):

        data = requests.get(url, headers=headers)
        tmp_path = self.tmp_dir.joinpath(name + ".zip")
        with open(str(tmp_path), "wb+") as tmp:
            tmp.write(data.content)

        with zipfile.ZipFile(str(tmp_path), "r") as zip_file:
            final_path = self.download_dir.joinpath(name)
            final_path.mkdir()
            zip_file.extractall(str(final_path))
        
        tmp_path.unlink()

    def fetch_and_filter(self):
        # fetching levels that will be downloaded from scoresaber
        # applies extended custom filtering according to given options
        requested_unfiltered = 0
        download_list = []
        ids_to_filter = []

        print("Searching on Scoresaber for levels to download...")
        bar = progressbar.ProgressBar(max_value=self.levels_to_download)
        bar.update(0)
        while len(download_list) < self.levels_to_download:
            limit = self.scoresaber_limit
            remaining = self.levels_to_download - len(download_list)
            if remaining < self.scoresaber_limit:
                limit = remaining
            
            page = int(((requested_unfiltered) / limit) + 1)

            levels = self._call_scoresaber_api(page, limit)["songs"]
            requested_unfiltered += limit

            filtered, ids_to_filter = self._filter_levels_scoresaber_only(levels, ids_to_filter)

            download_list.extend(filtered)
            bar.update(len(download_list))
            sys.stdout.flush()
        
        # Adding information from scoresaber including download URL
        with progressbar.ProgressBar(max_value=len(download_list)) as bar:
            print("\nGetting info from beatsaver...")
            for level in download_list:
                level["beatsaver_info"] = self._get_beatsaver_info(level["id"])
                bar.update(bar.value + 1)
        return download_list

    def _filter_levels_scoresaber_only(self, levellist, ids_to_filter):
        filtered = []
        already_downloaded = []
        if self.download_dir.exists():
            already_downloaded = os.listdir(self.download_dir)

        for level in levellist:
            dirname = self._get_level_dirname(level)

             # filter already downloaded
            if dirname in already_downloaded:
                print(os.listdir(self.download_dir))
                continue

            # Filter by difficulty
            stars = float(level["stars"])
            if stars > self.stars_max or stars < self.stars_min:
                continue

            # Scoresaber seems to have an extra entry for each difficulty.
            # We just need to download a level once, lol.
            if level["id"] in ids_to_filter:
                continue
            
            # If it survived all the filtering -> add to filtered list
            filtered.append(level)
            ids_to_filter.append(level["id"])

        return filtered, ids_to_filter
    
    def _get_beatsaver_info(self, level_id):
        response = requests.get("https://beatsaver.com/api/maps/by-hash/{id}".format(id=level_id), headers=headers)
        json = response.json()
        return json

    def _get_level_dirname(self, level_scoresaber_dict):
        # levelAuthorName and name can contain characters invalid for file or directory names
        # we need to filter them out
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)

        author = "".join(c for c in level_scoresaber_dict["levelAuthorName"] if c in valid_chars).replace(" ", "-")
        levelname = "".join(c for c in level_scoresaber_dict["name"] if c in valid_chars).replace(" ", "-")

        return "{id}_{author}_{levelname}".format(
            id=level_scoresaber_dict["id"],
            author=author,
            levelname=levelname
        )

    def _call_scoresaber_api(self, page, limit):
        scoresaber_sorting = 1 if self.scoresaber_sorting else 0
        ranked_only = 1 if self.ranked_only else 0
        response = requests.get("https://scoresaber.com/api.php?function=get-leaderboards&cat={cat}&page={page}&limit={limit}&ranked={ranked_only}"
                                .format(cat=scoresaber_sorting, page=page, limit=limit, ranked_only=ranked_only),
                                headers=headers)
        if response.ok:
            return response.json()

if __name__ == "__main__":
    print("This is just the internal downloader class. Please run arbsmapdo.py/arbsmapdo.exe instead :)")