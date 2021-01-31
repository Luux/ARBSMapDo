import json
from pathlib import Path
from pathvalidate import sanitize_filename


class Playlist():
    def __init__(self, config):
        self.playlist_dir = Path(config["playlist_dir"])
        self.name = config.get("playlist")

        # Auto-guess as *.bplist if extension is not given
        if not "." in self.name:
            self.name += ".bplist"

        self.filename = self.playlist_dir.joinpath(self.name)

        self.playlist_data = self.load_or_create()

    def load_or_create(self):
        # Create new if neccessary
        if not self.filename.is_file():
            print("Playlist {} does not exist. Creating new playlist.".format(self.name))
            raw_playlist = {
                "playlistTitle": self.name,
                "playlistAuthor": "[ARBSMapDo]",
                "image": None,
                "songs": []
            }
            return raw_playlist
        
        # Else load existing
        with open(self.filename, encoding="utf-8") as fp:
            playlist = json.load(fp)
        print("Loaded playlist {} from {}".format(self.name.split(".")[0], self.filename))
        return playlist
    
    def exists_in_playlist(self, levelhash):
        for song in self.playlist_data["songs"]:
            if song["hash"] == levelhash:
                return True
        return False

    def add_to_playlist(self, level):
        # Avoid duplicates
        levelhash = level["beatsaver_info"]["hash"]

        if not self.exists_in_playlist(levelhash):
            mini_info = {
                "key": level["beatsaver_info"]["key"],
                "hash": levelhash,
                "songName": "{} - {}".format(level["beatsaver_info"]["metadata"]["songAuthorName"],
                                            level["beatsaver_info"]["metadata"]["songName"]),
                "uploader": level["beatsaver_info"]["uploader"]["username"]
            }
            self.playlist_data["songs"].append(mini_info)

    def save_playlist(self):
        with open(self.filename, "w+", encoding="utf-8") as fp:
            json.dump(self.playlist_data, fp)
        print("Saved playlist {} to {}".format(self.name.split(".")[0], self.filename))