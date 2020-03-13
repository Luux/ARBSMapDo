import os
import sys
import toml
from argparse import ArgumentParser
from pathlib import Path
from inspect import getfile

from downloader import advanced_downloader


dir_script = Path(getfile(lambda: 0)).parent

default_config_name = "arbsmapdo_default.toml"

skip_assistant=False

class ConfigHandler:
    def __init__(self, args):
        # Non-"None" Arguments passed overwrite the preset
        args_dict = vars(args)
        preset_config = None
        path = dir_script.joinpath(args.preset)

        if os.path.isfile(path):
            try:
                preset_config = toml.load(path)
                print("Using preset: " + args.preset + "\n")
            except:
                print("ERROR while parsing config " + str(path))
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


    def missing_argument_assistant(self):
        # Kinda ugly. But processing user input config stuff will always be.

        # Extended options that are only available via command line or presets
        # No default values for argparse, cause we need to handle presets as well!

        if self.config.get("vote_ratio_max") is None:
            self.config["vote_ratio_max"] = 1

        if self.config.get("tmp_dir") is None:
            self.config["tmp_dir"] = "./tmp"

        if self.config.get("max_threads") is None:
            self.config["max_threads"] = 5
        
        if self.config["scoresaber_maxlimit"] is None:
            self.config["scoresaber_maxlimit"] = 10000

        if self.config.get("nps_min") is None:
            self.config["nps_min"] = 0

        if self.config.get("nps_max") is None:
            self.config["nps_max"] = float("inf")

        if self.config.get("notes_min") is None:
            self.config["notes_min"] = 0

        if self.config.get("notes_max") is None:
            self.config["notes_max"] = sys.maxsize

        # Here comes everything the assistant will deal with
        if self.config.get("download_dir") is None:
            print("Download directory not yet specified. Please input the download directory (usually '[BeatSaberPath]\\Beat Saber_Data\\CustomLevels').")
            print("This will be saved to the preset if specified or to the default preset.")
            self.config["download_dir"] = str(self.get_validated_input(Path, skippable=False).absolute())

            # write the path to the used preset if it's not set at all
            self.save_config(default_config_name)

        if self.config.get("levels_to_download") is None:
            print("How many levels do you want to download?")
            self.config["levels_to_download"] = self.get_validated_input(int, min_value=1, skippable=False)

        if self.config.get("ranked_only") is None:
            print("Would you like to download only levels that have a ranked map? (Default: 1)")
            print("(A Level will be downloaded if there's at least one ranked difficulty)")
            print("0 - All Maps")
            print("1 - Ranked Only")
            self.config["ranked_only"] = self.get_validated_input(int, default=1, choices=[0, 1])
        
        if self.config.get("scoresaber_sorting") is None:
                print("Which sorting (from scoresaber side) should be used? (Default: 1)")
                print("0 - Trends")
                print("1 - Date Ranked")
                print("2 - Scores Set")
                print("3 - Star Difficulty (only if ranked)")
                self.config["scoresaber_sorting"] = self.get_validated_input(dst_type=int, default=1, choices=[0, 1, 2, 3])

        if self.config.get("stars_min") is None:
            print("Minimum Stars? (Default: 0)")
            self.config["stars_min"] = self.get_validated_input(float, default=0, min_value=0, max_value=50)

        if self.config.get("stars_max") is None:
            print("Maximum Stars? (Default: 50)")
            self.config["stars_max"] = self.get_validated_input(float, default=50, min_value=0, max_value=50)

        if self.config.get("vote_ratio_min") is None:
            print("What's the minimum percentage of upvotes (of total votes) the map should have? (Value between 0 and 1, Default: 0)")
            self.config["vote_ratio_min"] = self.get_validated_input(float, default=0, min_value=0, max_value=1)

        if self.config.get("length_min") is None:
            print("Do you want to set a minimum map length (in seconds)? (Default: 0)")
            self.config["length_min"] = self.get_validated_input(float, default=0, min_value=0)
        
        if self.config.get("length_max") is None:
            print("Do you want to set a maximum map length (in seconds)? (Default: infinite)")
            self.config["length_max"] = self.get_validated_input(float, default=float("inf"), min_value=0)


        save_preset = self.config.get("save_preset")
        if save_preset is not None:
            self.save_config(save_preset)
            print("Preset saved: {}\n Saved to: {}".format(str(self.config), str(save_preset)))


    def get_validated_input(self, dst_type, default=None, choices=None, min_value=None, max_value=None, skippable=True):
        if self.config["skip_assistant"] and skippable:
            return default
        while True:
            response = input()
            if response is "" and default is not None:
                return default
            else:
                try:
                    if dst_type is float:
                        response = response.replace(",", ".")

                    elif dst_type is Path:
                        response = dir_script.joinpath(Path(input()))

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
        path = dir_script.joinpath(Path(path))
        with open(path, "w+") as config_file:
            toml.dump(self.config, config_file)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--preset", default=default_config_name, help="Path to the preset to use (default: {}".format(default_config_name))
    parser.add_argument("-levels", "--levels_to_download", type=int, help="Number of levels to download. One level may have multiple difficulties!")
    parser.add_argument("--stars_min", type=int, help="Minimum star difficulty for ranked maps")
    parser.add_argument("--stars_max", type=int, help="Maximum star difficulty for ranked maps")
    parser.add_argument("--ranked", type=bool, help="Only download ranked maps (True or False / 1 or 0)")
    parser.add_argument("--scoresaber_sorting", type=int, choices=[0, 1, 2], help="Scoresaber Sorting Mode. Choices: 0 - Trends, 1 - Date Ranked, 2 - Scores Set, 3 - Star Difficulty")
    parser.add_argument("--tmp_dir", type=Path, help="Temporary download dir (default: './download/')")
    parser.add_argument("--download_dir", type=Path, help="Final download folder where custom levels get extracted (usually '[BeatSaberPath]\\Beat Saber_Data\\CustomLevels')")
    parser.add_argument("--max_threads", type=int, help="Maximim thread count to use for downloading.")
    parser.add_argument("--scoresaber_maxlimit", type=int, help="Maximum maps per 'page' for Scoresaber API. (You usually don't have to change this.)")
    parser.add_argument("--save_preset", type=Path, help="Save specified settings into given file. You can load it next time by using --preset")
    parser.add_argument("--vote_ratio_min", type=float, help="Minimum percentage of positive votes of total votes. (Between 0 and 1)")
    parser.add_argument("--vote_ratio_max", type=float, help="Maximum percentage of positive votes of total votes. (Between 0 and 1)")
    parser.add_argument("--length_min", type=int, help="Minimum map length in seconds")
    parser.add_argument("--length_max", type=int, help="Maximum map length in seconds")
    parser.add_argument("--nps_min", type=float, help="Minimum notes per second")
    parser.add_argument("--nps_max", type=float, help="Maximum notes per second")
    parser.add_argument("--notes_min", type=int, help="Minimum total note count")
    parser.add_argument("--notes_max", type=int, help="Maximum total note count")
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

    config_handler = ConfigHandler(args)
    config_handler.missing_argument_assistant()
    downloader = advanced_downloader(config_handler.config)
    downloader.start()

    # Only for EXE releases
    # print("\n\nDone! Press enter to close ARBSMapDo.")
    # input()




