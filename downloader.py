import requests
import sys
import os
import string
import progressbar
import threading
import zipfile
import cache
import utils

from inspect import getfile
from pathlib import Path
from json import JSONDecodeError


dir_script = Path(getfile(lambda: 0)).parent

headers = {"User-Agent": "ARBSMapDo V1"}



class advanced_downloader():
    def __init__(self, config: dict):
        
        self.download_dir = Path(config["download_dir"])
        self.tmp_dir = dir_script.joinpath(config["tmp_dir"])
        self.max_threads = config["max_threads"]
        self.URI = config["URI"]


        # Only when filtering
        if self.URI is None:
            self.ranked_only = config["ranked_only"]
            self.scoresaber_sorting = config["scoresaber_sorting"]
            self.levels_to_download = config["levels_to_download"]
            self.scoresaber_maxlimit = config["scoresaber_maxlimit"]
            self.stars_min = config["stars_min"]
            self.stars_max = config["stars_max"]
            self.vote_ratio_min = config["vote_ratio_min"]
            self.vote_ratio_max = config["vote_ratio_max"]
            self.length_min = config["length_min"]
            self.length_max = config["length_max"]
            self.notes_min = config["notes_min"]
            self.notes_max = config["notes_max"]
            self.nps_min = config["nps_min"]
            self.nps_max = config["nps_max"]
            self.gamemode = config["gamemode"]
        else:
            self.URI_type = utils.get_map_or_playlist_resource_type(self.URI)

        # Initialize
        self.cache = cache.Cache(config)

    def install_from_URI(self, URI):
        if self.URI_type in [utils.URI_type.map_beatsaver, utils.URI_type.map_bsaber]:
            level_key = utils.get_level_key_from_url(self.URI, self.URI_type)
            level_dict = dict()

            # Keys do not rely on the actual cache functionality
            # but the API calls are almost identical, that's why cache.get_beatsaver_info handles hashes AND keys
            level_dict["beatsaver_info"] = self.cache.get_beatsaver_info(level_key)

            # We got everything we need, so let's go
            self.download_levels([level_dict])


    def clean_temp_dir(self):
        """Clean temp dir only if safe (directory is empty)"""
        try:
            Path(self.tmp_dir).rmdir()
        except:
            print("WARNING: Error while cleaning up. Cannot delete tmp directory.")

    def start(self):
        """Starting the main functionality of ARBSMapDo"""

        # Create Download Directory if not existant
        self.download_dir.mkdir(exist_ok=True)

        # Search & Filter...
        if self.URI is None:
            # Crawl Scoresaber and filter
            levels_to_download = self.fetch_and_filter()

            # Finally, download filtered Maps
            if len(levels_to_download) > 0:
                self.download_levels(levels_to_download)
        else:
            # ...or install directly
            self.install_from_URI(self.URI)
        
        # Save calculated hashes
        self.cache.save_levelhash_cache()

    def download_levels(self, levels: list):
        """Download a specific list of levels using multiple threads"""

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
                    levelhash = level["beatsaver_info"]["_id"]
                    name = self._get_level_dirname(level)
                    self.cache.levelhash_cache[name] = levelhash

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
        self.clean_temp_dir()

    def _download_level(self, url, name):
        """Threading helper function to download a single level"""

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
        """
        1) Scan scoresaber
        2) Grab candidates
        3) Scan BeatSaver data (and filter by it) for all candidates since only few information is available via ScoreSaber
        4) Create final download list
        """
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

            #with progressbar.ProgressBar(max_value=self.levels_to_download - len(download_list), redirect_stdout=False) as bar_levelsearch:
                #bar_levelsearch.update(0)
            scoresaber_filtered_list = []

            while len(scoresaber_filtered_list) < self.levels_to_download - len(download_list):
                limit = self.scoresaber_maxlimit
                remaining = self.levels_to_download - len(download_list) - len(scoresaber_filtered_list)

                page = int(((requested_unfiltered) / limit) + 1)

                levels = self._call_scoresaber_api(page, limit)["songs"]

                requested_unfiltered += limit

                if len(levels) == 0:
                    # Early Abort, no more songs with these filters -> Proceed to download stage
                    if len(download_list) == 0:
                        print("Could not find any new levels under the given criteria.")
                    else:
                        print("Could not find more than {} levels under the given criteria.".format(len(download_list)))
                    return download_list

                # ScoreSaber is faster, so we filter based on only scoresaber information first before accessing BeatSaver
                filtered = []
                for level in levels:
                    if self._filter_level_scoresaber_only(level, ids_to_filter):
                        # If it survived all the filtering -> add to filtered list
                        filtered.append(level)
                        ids_to_filter.append(level["id"])

                scoresaber_filtered_list.extend(filtered)
                print("Filtered " + str(len(scoresaber_filtered_list)) + " potential candidates from Scoresaber data only")
                # print("Total entries processed from ScoreSaber: " + str(requested_unfiltered))
                #sys.stdout.flush()
        
                # Adding information from scoresaber including download URL
                filtered_beatsaver = 0
                print("Filtering candidates by info from beatsaver...")
                with progressbar.ProgressBar(max_len=len(scoresaber_filtered_list), redirect_stdout=True) as bar:
                    for level in scoresaber_filtered_list:
                        level["beatsaver_info"] = self.cache.get_beatsaver_info(level["id"])
                        if self._filter_level_with_beatsaver_info(level) is True:
                            download_list.append(level)
                            print("Found Levels: {}/{}".format(len(download_list), self.levels_to_download))
                        filtered_beatsaver += 1
                        bar.update(filtered_beatsaver)
                        if len(download_list) == self.levels_to_download:
                            return download_list
        return download_list


    def _filter_level_scoresaber_only(self, scoresaber_info, ids_to_filter):
        # filter already downloaded
        if scoresaber_info["id"].upper() in self.cache.levelhash_cache.values():
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
        def _filter_difficulty(difficulty_info, level):
            if difficulty_info is None:
                return False
            length = float(difficulty_info["length"])
            note_count = int(difficulty_info["notes"])

            if length == 0:
                # for some reason, sometimes the duration as well as other values are 0... -> broken info
                return False

            notes_per_second = float(note_count) / length

            if length < self.length_min or length > self.length_max:
                return False

            if note_count < self.notes_min or note_count > self.notes_max:
                return False

            if notes_per_second < self.nps_min or notes_per_second > self.nps_max:
                return False

            return True
        
        def _filter_characteristic(characteristic):
            name = characteristic.get("name")
            if name != self.gamemode and self.gamemode is not None:
                return False

            difficulties = characteristic.get("difficulties")
            for info in difficulties.values():
                if _filter_difficulty(info, level):
                    return True


        bs_info = level.get("beatsaver_info")
        if bs_info is None:
            print("Skipping level due to missing beatsaver_info:\n{}".format(level))
            return False
        bs_metadata = bs_info.get("metadata")
        if bs_metadata is None:
            print("Skipping Level due to missing metadata:\n{}".format(level))
            return False
        bs_stats = bs_info["stats"]
        bs_upvotes = int(bs_stats["upVotes"])
        bs_downvotes = int(bs_stats["downVotes"])

        # Filter each difficulty
        bs_characteristics = bs_metadata.get("characteristics")

        characteristics_ok = False
        for characteristic in bs_characteristics:
            if _filter_characteristic(characteristic):
                characteristics_ok = True
        
        vote_ratio = 0.5 # division / 0 if map has no votes yet
        if bs_upvotes + bs_downvotes > 0:
            vote_ratio = bs_upvotes / (bs_upvotes + bs_downvotes)
        if vote_ratio < self.vote_ratio_min or vote_ratio > self.vote_ratio_max:
            return False

        if not characteristics_ok:
            return False

        return True

    def _get_level_dirname(self, level_scoresaber_dict):
        """
        Choose a directory name for a level
        """
        # levelAuthorName and name can contain characters invalid for file or directory names
        # we need to filter them out
        valid_chars = "-_() %s%s" % (string.ascii_letters, string.digits)

        author = "".join(c for c in level_scoresaber_dict["beatsaver_info"]["metadata"]["levelAuthorName"] if c in valid_chars).replace(" ", "-")
        levelname = "".join(c for c in level_scoresaber_dict["beatsaver_info"]["name"] if c in valid_chars).replace(" ", "-")

        return "{id}_{author}_{levelname}".format(
            id=level_scoresaber_dict["beatsaver_info"]["_id"],
            author=author,
            levelname=levelname
        )

    def _call_scoresaber_api(self, page, limit):
        """Call the ScoreSaber-API I guess?"""

        ranked_only = 1 if self.ranked_only else 0
        response = requests.get("https://scoresaber.com/api.php?function=get-leaderboards&cat={cat}&page={page}&limit={limit}&ranked={ranked_only}"
                                .format(cat=self.scoresaber_sorting, page=page, limit=limit, ranked_only=ranked_only),
                                headers=headers)
        if response.ok:
            return response.json()

if __name__ == "__main__":
    print("This is just the internal downloader class. Please run arbsmapdo.py instead :)")
