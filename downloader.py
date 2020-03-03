import requests
import sys
import os
import string
import progressbar
import threading
import zipfile

from inspect import getfile
from pathlib import Path
from json import JSONDecodeError

dir_script = Path(getfile(lambda: 0)).parent

# Cloudflare refuses access if we don't have a UserAgent
headers = {"User-Agent": "ARBSMapDo V1"}


class advanced_downloader():
    def __init__(self, config: dict):
        
        self.download_dir = Path(config["download_dir"])
        self.ranked_only = config["ranked_only"]
        self.scoresaber_sorting = config["scoresaber_sorting"]
        self.levels_to_download = config["levels_to_download"]
        self.scoresaber_maxlimit = config["scoresaber_maxlimit"]
        self.tmp_dir = dir_script.joinpath(config["tmp_dir"])
        self.max_threads = config["max_threads"]
        self.stars_min = config["stars_min"]
        self.stars_max = config["stars_max"]
        self.vote_ratio_min = config["vote_ratio_min"]
        self.vote_ratio_max = config["vote_ratio_max"]
        self.duration_min = config["duration_min"]
        self.duration_max = config["duration_max"]

    def start(self):
        # Create Download Directory if not existant
        self.download_dir.mkdir(exist_ok=True)

        self.already_downloaded = os.listdir(self.download_dir)

        # Crawl Scoresaber and filter
        levels_to_download = self.fetch_and_filter()

        # Finally, download filtered Maps
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

        # yeah, double while. Why? Simply because first filtering based only on ScoreSaber information is done before
        # getting information from BeatSaver to save some time (Scoresaber is way faster than BeatSaver)
        print("Beginning map search. This may take multiple passes depending on how restrictive your filters are.")
        while len(download_list) < self.levels_to_download:
            print("Searching on Scoresaber for levels to download. Need to find {} more songs.".format(self.levels_to_download - len(download_list)))

            with progressbar.ProgressBar(max_value=self.levels_to_download - len(download_list), redirect_stdout=True) as bar:
                bar.update(0)
                scoresaber_filtered_list = []

                while len(scoresaber_filtered_list) < self.levels_to_download - len(download_list):
                    limit = self.scoresaber_maxlimit
                    remaining = self.levels_to_download - len(download_list) - len(scoresaber_filtered_list)

                    page = int(((requested_unfiltered) / limit) + 1)

                    levels = self._call_scoresaber_api(page, limit)["songs"]

                    requested_unfiltered += limit

                    if len(levels) == 0:
                        # Early Abort, no more songs with these filters -> Proceed to download stage
                        print("Could not find more than {} levels under the given criteria.".format(len(download_list)))
                        return download_list

                    # ScoreSaber is faster, so we filter based on only scoresaber information first before accessing BeatSaver
                    filtered = []
                    for level in levels:
                        if len(filtered) < remaining:
                            if self._filter_level_scoresaber_only(level, ids_to_filter):
                                # If it survived all the filtering -> add to filtered list
                                filtered.append(level)
                                ids_to_filter.append(level["id"])

                    scoresaber_filtered_list.extend(filtered)
                    bar.update(len(scoresaber_filtered_list))
                    # print("Total entries processed from ScoreSaber: " + str(requested_unfiltered))
                    sys.stdout.flush()
            
            # Adding information from scoresaber including download URL
            with progressbar.ProgressBar(max_value=len(scoresaber_filtered_list)) as bar:
                print("\nGetting info from beatsaver...")
                for level in scoresaber_filtered_list:
                    level["beatsaver_info"] = self._get_beatsaver_info(level["id"])
                    if self._filter_level_with_beatsaver_info(level) is True:
                        download_list.append(level)
                    bar.update(bar.value + 1)
        return download_list


    def _filter_level_scoresaber_only(self, scoresaber_info, ids_to_filter):
        dirname = self._get_level_dirname(scoresaber_info)

            # filter already downloaded
        if dirname in self.already_downloaded:
            return False

        

        # Filter by difficulty
        stars = float(scoresaber_info["stars"])
        if stars > self.stars_max or stars < self.stars_min:
            return False

        # Scoresaber seems to have an extra entry for each difficulty.
        # We just need to download a level1 once, lol.
        if scoresaber_info["id"] in ids_to_filter:
            return False
        
        return True

    def _filter_level_with_beatsaver_info(self, level):
        bs_info = level["beatsaver_info"]
        if bs_info is None:
            return False
        bs_metadata = bs_info["metadata"]
        bs_stats = bs_info["stats"]
        bs_upvotes = int(bs_stats["upVotes"])
        bs_downvotes = int(bs_stats["downVotes"])
        durations = [float(bs_metadata["duration"])]

        bs_characteristics = bs_metadata.get("characteristics")
        for characteristic in bs_characteristics:
            difficulties = characteristic.get("difficulties")
            for info in difficulties.values():
                if info is not None:
                    durations.append(float(info["duration"]))


        vote_ratio = bs_upvotes / (bs_upvotes + bs_downvotes)
        if vote_ratio < self.vote_ratio_min or vote_ratio > self.vote_ratio_max:
            return False
        
        duration_ok = False
        for duration in durations:
            if duration >= self.duration_min and duration <= self.duration_max:
                duration_ok = True
        if not duration_ok:
            return False

        return True

    def _get_beatsaver_info(self, level_id):
        try:
            response = requests.get("https://beatsaver.com/api/maps/by-hash/{id}".format(id=level_id), headers=headers)
            json = response.json()
        except JSONDecodeError:
            print("Failed to get level {} from Beat Saver.".format(level_id))
            return None
        return json

    def _get_level_dirname(self, level_scoresaber_dict):
        # levelAuthorName and name can contain characters invalid for file or directory names
        # we need to filter them out
        valid_chars = "-_() %s%s" % (string.ascii_letters, string.digits)

        author = "".join(c for c in level_scoresaber_dict["levelAuthorName"] if c in valid_chars).replace(" ", "-")
        levelname = "".join(c for c in level_scoresaber_dict["name"] if c in valid_chars).replace(" ", "-")

        return "{id}_{author}_{levelname}".format(
            id=level_scoresaber_dict["id"],
            author=author,
            levelname=levelname
        )

    def _call_scoresaber_api(self, page, limit):
        ranked_only = 1 if self.ranked_only else 0
        response = requests.get("https://scoresaber.com/api.php?function=get-leaderboards&cat={cat}&page={page}&limit={limit}&ranked={ranked_only}"
                                .format(cat=self.scoresaber_sorting, page=page, limit=limit, ranked_only=ranked_only),
                                headers=headers)
        if response.ok:
            return response.json()

if __name__ == "__main__":
    print("This is just the internal downloader class. Please run arbsmapdo.py instead :)")