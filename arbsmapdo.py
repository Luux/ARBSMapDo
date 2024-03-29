import os
import sys
import toml
import utils
from argparse import ArgumentParser
from pathlib import Path
from inspect import getfile

from downloader import advanced_downloader

dir_script = Path(getfile(lambda: 0)).parent.absolute()

default_config_name = "arbsmapdo_default.toml"

skip_assistant=False

modes = {
        0: None,
        1: "Standard",
        2: "OneSaber",
        3: "NoArrows",
        4: "Degree90",
        5: "Degree360",
        6: "Lightshow",
        7: "Lawless"
    }

class ConfigHandler:
    """
    ARBSMapDo can be used in 3 different ways:
    1) Using the Interactive Assistant
    2) Via Command Line Arguments
    3) Passing a Configuration file
    These three approaches can be mixed altogether, where Config File < CL Args < Interactive
    However, as so many configuration variants can become quite messy to implement, there's a ConfigHandler
    which serves as a single "Point-of-Trust" and manages all of this. This results in a single final configuration dictionary
    that is used by the other components of ARBSMapDo.
    """

    def __init__(self, args):
        """Just some initialization. Also prepares the hierachy explained above."""

        # Non-"None" Arguments passed overwrite the preset
        args_dict = vars(args)
        preset_config = None
        preset_path = dir_script.joinpath(args.preset)

        if os.path.isfile(preset_path):
            try:
                preset_config = toml.load(preset_path)
                print("Using preset: " + args.preset)
            except:
                print("ERROR while parsing config " + str(preset_path))
                raise
        else:
            # When running the first time
            if args.preset is default_config_name:
                preset_config = dict()
            else:
                # When given a non existant Config
                print("Config not found. Aborting")

        for key in preset_config.keys():
            if args_dict.get(key) is None:
                args_dict[key] = preset_config.get(key)

        self.config = args_dict

    def set_default_if_none(self, key, value):
        if self.config.get(key) is None:
            self.config[key] = value

    def handle_non_assistant_default_values(self):
        """
        We cannot simply use argparse defaults as we have to check if the user manually specified an argument or not.
        (If the user has not specified a CL argument, it becomes None -> load config value instead)
        TODO: This can be done a bit less hacky
        """
        
        default_values = {
            "beatmap_rating_max": 1,
            "tmp_dir": "./tmp",
            "max_threads": 5,
            "scoresaber_maxlimit": 10000,
            "nps_min": 0,
            "nps_max": float("inf"),
            "notes_min": 0,
            "notes_max": sys.maxsize,
            "gamemode": "Standard",
            "beatsaver_cachefile": "./arbsmapdo_cache.json",
            "levelhash_cachefile": Path(self.config.get("download_dir")).joinpath("./levelhash_cache.json"),
            "rescan": False,
            "noextract": False,
            "playlist_image": utils.get_resource_path("playlist_image.png"),
        }
        
        for key in default_values.keys():
            if self.config.get(key) is None:
                self.config[key] = default_values[key]

    def missing_argument_assistant(self):
        """
        The interactive assistant covers options that are not passed via config file/CL.
        This is also the "just-run-it" variant, as you don't have to mess around with CL arguments.
        Of course, we need to validate user inputs as well.
        """
        # Kinda ugly. But processing user input config stuff will always be.

        # Extended options that are only available via command line or presets
        # No default values for argparse, cause we need to handle presets as well!

        if self.config.get("download_dir") is None:
            message = ("Download directory not yet specified. Please input the download directory\n"
                       "(usually '[BeatSaberPath]\\Beat Saber_Data\\CustomLevels').\n\n")
            download_dir = self.get_validated_input(message, Path, skippable=False).absolute()
            self.config["download_dir"] = str(download_dir)

            # write the path to the used preset if it's not set at all
            self.save_config(default_config_name)
            print("\n----------------------------------------------------------------------------\n")

        if self.config.get("playlist_dir") is None:
            playlist_path = Path(self.config["download_dir"]).joinpath("../../Playlists/").resolve()
            message = "\nPlaylists will be saved at {}\nIf this is correct, confirm with [ENTER], else specify a custom path below.\n\n".format(playlist_path.absolute())
            playlist_path = self.get_validated_input(message, Path, skippable=True, default=playlist_path).resolve().absolute()
            self.config["playlist_dir"] = str(playlist_path)
            # write the path to the used preset if it's not set at all
            self.save_config(default_config_name)
            print("----------------------------------------------------------------------------\n")

        # Handle other default config va
        self.handle_non_assistant_default_values()

        # Here comes everything else the interactive assistant will deal with
        # We only need the rest if no URI is specified -> else we don't need filtering and therefore we don't need filtering options
        mapfiltering = False
        
        if config_handler.config["URIs"] == [] :
            if self.config.get("skip_assistant") is True:
                mapfiltering = True
            elif self.config.get("levels_to_download") is None:
                print("\n- Just press [ENTER] if you want to download many levels using the filtering functionality of ARBSMapDo.")
                print("\n- If you want to manually download levels/playlists instead, insert the URIs here.")
                print("(Multiple are supported, press 2x[ENTER] when ready.)\n")

                user_input = input()
                if user_input == "":
                    mapfiltering = True
                
                else:
                    # Download maps/playlists manually
                    URIs = []
                    while user_input != "":
                        URIs.append(user_input)
                        user_input = input()
                    config_handler.config["URIs"] = URIs
            else:
                # ´--levels_to_download is given
                mapfiltering = True

        if mapfiltering:
            # Ask all the stuff for batch downloading
            # Or at least the mandatory stuff such as levels_to_download if --skip_assistant
            self.missing_argument_assistant_for_mapfiltering()


    def missing_argument_assistant_for_mapfiltering(self):
        if self.config.get("levels_to_download") is None:
            message = "How many levels do you want to download?\n"
            self.config["levels_to_download"] = self.get_validated_input(message, int, min_value=1, skippable=False)

        if self.config.get("ranked_only") is None:
            message = ("\nWould you like to download only levels that have a ranked map? (Default: 1)\n"
            "(A Level will be downloaded if there's at least one ranked difficulty)\n\n"
            "0 - All Maps\n"
            "1 - Ranked Only\n")
            self.config["ranked_only"] = self.get_validated_input(message, int, default=1, choices=[0, 1])
        
        if self.config.get("scoresaber_sorting") is None:
                message = ("\nWhich sorting (from scoresaber side) should be used? (Default: 1)\n\n"
                "0 - Trends\n"
                "1 - Date Ranked\n"
                "2 - Scores Set\n"
                "3 - Star Difficulty (only if ranked)\n")
                self.config["scoresaber_sorting"] = self.get_validated_input(message, int, default=1, choices=[0, 1, 2, 3])

        # Note that this probably isn't very useful when looking for ranked maps,
        # so ARBSMapDo will only ask for mode if not ranked_only.
        # However, if you really want to do it, you can do this via command line or preset
        
        # if self.config.get("gamemode") is None and not self.config["ranked_only"]:
        #     print("Filter by GameMode? (default: None/No filtering)")
        #     for key in modes:
        #         print("{} - {}".format(key, modes[key]))
        #     mode_num = self.get_validated_input(int, 0, choices=range(len(modes.values())))
        #     mode = modes[mode_num]
        #     self.config["gamemode"] = mode

        if self.config.get("stars_min") is None:
            message = "Minimum Stars? (Default: 0)\n"
            self.config["stars_min"] = self.get_validated_input(message, float, default=0, min_value=0, max_value=50)

        if self.config.get("stars_max") is None:
            message = "Maximum Stars? (Default: 50)\n"
            self.config["stars_max"] = self.get_validated_input(message, float, default=50, min_value=0, max_value=50)

        if self.config.get("beatmap_rating_min") is None:
            message = "What's the minimum beatmap rating (based on votes) the map should have? (Value between 0 and 1, Default: 0)\n"
            self.config["beatmap_rating_min"] = self.get_validated_input(message, float, default=0, min_value=0, max_value=1)

        if self.config.get("length_min") is None:
            message = "Do you want to set a minimum map length (in seconds)? (Default: 0)\n"
            self.config["length_min"] = self.get_validated_input(message, float, default=0, min_value=0)
        
        if self.config.get("length_max") is None:
            message = "Do you want to set a maximum map length (in seconds)? (Default: infinite)\n"
            self.config["length_max"] = self.get_validated_input(message, float, default=float("inf"), min_value=0)


        save_preset = self.config.get("save_preset")
        if save_preset is not None:
            self.save_config(save_preset)
            print("\nPreset saved: {}\n Saved to: {}\n".format(str(self.config), str(save_preset)))


    def get_validated_input(self, message, dst_type, default=None, choices=None, min_value=None, max_value=None, skippable=True):
        """
        Used to validate User Inputs and perform some normalization.
        """
        if self.config["skip_assistant"] and skippable:
            return default
        
        if message is not None:
            print(message)

        while True:
            response = input()
            print("")
            if response == "" and default is not None:
                return default
            else:
                try:
                    if dst_type is float:
                        response = response.replace(",", ".")

                    elif dst_type is Path:
                        response = dir_script.joinpath(Path(response))

                    response = dst_type(response)

                    if dst_type is int or dst_type is float:
                        if min_value is not None and response < min_value:
                            print("Value has to be >= " + str(min_value))
                            continue
                        if max_value is not None and response > max_value:
                            print("Value has to be <= " + str(max_value))
                            continue

                    if choices is None:
                        return response
                    elif response in choices:
                        return response
                    else:
                        print("Please choose one of the given options: " + str(choices))
                except:
                    print("Please input a valid value.")
                    continue

    def save_config(self, path: str):
        """Can be used to save a configuration file"""

        # Things such as the URI should not be saved. Filter them.
        exclude = ["URIs", "preset"]
        filtered_config = dict()
        for key in self.config.keys():
            if key not in exclude:
                filtered_config[key] = self.config[key]

        path = dir_script.joinpath(Path(path))
        with open(path, "w+") as config_file:
            toml.dump(filtered_config, config_file)



if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("URIs", nargs="*", default=[], help="URI (Path or URL) to map or playlist (*.bplist). ARBSMapDo will download and install the specified map/list.")
    parser.add_argument("--preset", default=default_config_name, help="Path to the preset to use (default: {}".format(default_config_name))
    parser.add_argument("-levels", "--levels_to_download", type=int, help="Number of levels to download. One level may have multiple difficulties!")
    parser.add_argument("--noextract", action="store_true", help="Do not extract *.zip files. Helpful for Quest users as you can upload them directly to BMBF!")
    parser.add_argument("--stars_min", type=float, help="Minimum star difficulty for ranked maps")
    parser.add_argument("--stars_max", type=float, help="Maximum star difficulty for ranked maps")
    parser.add_argument("--ranked_only", type=bool, help="Only download ranked maps (True or False / 1 or 0)")
    parser.add_argument("--scoresaber_sorting", type=int, choices=[0, 1, 2], help="Scoresaber Sorting Mode. Choices: 0 - Trends, 1 - Date Ranked, 2 - Scores Set, 3 - Star Difficulty")
    parser.add_argument("--tmp_dir", type=Path, help="Temporary download dir (default: './download/')")
    parser.add_argument("--download_dir", type=Path, help="Final download folder where custom levels get extracted (usually '[BeatSaberPath]\\Beat Saber_Data\\CustomLevels')")
    parser.add_argument("--playlist_dir", type=Path, help="Directory where playlist files will be saved at (usually '[BeatSaberPath]\\Playlists')")
    parser.add_argument("--max_threads", type=int, help="Maximim thread count to use for downloading.")
    parser.add_argument("--scoresaber_maxlimit", type=int, help="Maximum maps per 'page' for Scoresaber API. (You usually don't have to change this.)")
    parser.add_argument("--save_preset", type=Path, help="Save specified settings into given file. You can load it next time by using --preset")
    parser.add_argument("--beatmap_rating_min", type=float, help="Minimum beatmap rating. (Between 0 and 1)")
    parser.add_argument("--beatmap_rating_max", type=float, help="Maximum beatmap rating. (Between 0 and 1)")
    parser.add_argument("--length_min", type=int, help="Minimum map length in seconds")
    parser.add_argument("--length_max", type=int, help="Maximum map length in seconds")
    parser.add_argument("--nps_min", type=float, help="Minimum notes per second")
    parser.add_argument("--nps_max", type=float, help="Maximum notes per second", )
    parser.add_argument("--notes_min", type=int, help="Minimum total note count")
    parser.add_argument("--notes_max", type=int, help="Maximum total note count")
    # parser.add_argument("--gamemode", type=str, choices=list(modes.values()), help="Filter by game mode. EXPERIMENTAL! NOT FINISHED!")
    parser.add_argument("--rescan", action="store_true", help="Force rescan of already downloaded songs. This resets the cache and results in manually deleted songs being in the pool again.")
    parser.add_argument("--beatsaver_cachefile", type=Path, help="Cache file used for BeatSaver cache. (You usually don't have to change this.)")
    parser.add_argument("--levelhash_cachefile", type=Path, help="Cache file used for caching already calculated level hashes. (You usually don't have to change this.)")
    parser.add_argument("--playlist", help="Playlist (file name) where levels from this session should be added. If the specified playlist does not exist yet, it will be created.")
    parser.add_argument("--playlist_image", type=Path, help="When creating a new playlist, use this image. If not given, the default image will be used.")
    parser.add_argument("-s", "--skip_assistant", action="store_true",
                        help="Skip assistant except for neccessary things. You'll need to specify every argument via command line or preset")
    args = parser.parse_args()

    print("\n-------------------------------------------------------------")
    print("--- Advanced Ranked Beat Saber Map Downloader (ARBSMapDo) ---")
    print("-------------------------------------------------------------\n")
    print("If you want extended filtering, please use the --help argument to see what's currently implemented!")
    print("Do you want to save your config for further use? Use --save_preset 'name'")
    print("If you want to load a specific config, you can use --preset 'name'")
    print("All options are available directly from the command line as well as via presets.\n")
    print("----------------------------------------------------------------------------")
    print("----------------------------------------------------------------------------\n")

    config_handler = ConfigHandler(args)
    config_handler.missing_argument_assistant()
    downloader = advanced_downloader(config_handler.config)
    downloader.start()

    # Only for EXE releases
    # print("\n\nDone! Press enter to close ARBSMapDo.")
    # input()




