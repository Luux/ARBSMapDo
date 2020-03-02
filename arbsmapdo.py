import os
import toml
from argparse import ArgumentParser
from pathlib import Path
from inspect import getfile

from downloader import advanced_downloader


dir_script = Path(getfile(lambda: 0)).parent

default_config_name = "arbsmapdo_default.toml"


def init_config(args):
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

    for key in args_dict.keys():
        if preset_config.get(key) is not None:
            args_dict[key] = preset_config[key]

    return args_dict


def handle_missing_arguments(config_dict):
    # Kinda ugly. But processing user input config stuff will always be.

    if config_dict.get("download_dir") is None:
        print("Download directory not yet specified. Please input the download directory (usually '[BeatSaberPath]\\Beat Saber_Data\\CustomLevels').")
        print("This will be saved to the preset if specified or to the default preset.")
        download_dir = str(dir_script.joinpath(Path(input())).absolute())
        config_dict["download_dir"] = download_dir

        # write the path to the used preset if it's not set at all
        save_config(config_dict, default_config_name)
    
    if config_dict.get("ranked_only") is None:
        print("Would you like to download only levels that have a ranked map? (Default: 1)")
        print("(A Level will be downloaded if there's at least one ranked difficulty)")
        print("0 - All Maps")
        print("1 - Ranked Only")
        response = input()
        ranked_only = "0" if response is "0" else "1"
        config_dict["ranked_only"] = ranked_only
    
    if config_dict.get("scoresaber_sorting") is None:
            print("Which sorting (from scoresaber side) should be used? (Default: 1)")
            print("0 - Trends")
            print("1 - Date Ranked")
            print("2 - Scores Set")
            print("3 - Star Difficulty (only if ranked)")
            response = input()
            config_dict["scoresaber_sorting"] = response if response in ["0", "1", "2", "3"] else "1"

    if config_dict.get("levels_to_download") is None:
        print("How many levels do you want to download?")
        response = int(input())
        config_dict["levels_to_download"] = response
    
    if config_dict.get("stars_min") is None:
        print("Minimum Stars? (Default: 0)")
        response = input()
        response = float(response.replace(",", ".")) if response is not "" else 0
        config_dict["stars_min"] = response

    if config_dict.get("stars_max") is None:
        print("Maximum Stars? (Default: 50)")
        response = input()
        response = float(response.replace(",", ".")) if response is not "" else 50
        config_dict["stars_max"] = response

    if config_dict.get("vote_ratio_min") is None:
        print("What's the minimum percentage of upvotes (of total votes) the map should have? (Value between 0 and 1, Default: 0)")
        response = input()
        response = float(response.replace(",", ".")) if response is not "" else 0
        config_dict["vote_ratio_min"] = response
    
    if config_dict.get("duration_min") is None:
        print("Do you want to set a minimum song duration (in seconds)? (Default: 0)")
        response = input()
        response = float(response.replace(",", ".")) if response is not "" else 0
        config_dict["duration_min"] = response
    
    if config_dict.get("duration_max") is None:
        print("Do you want to set a maximum song duration (in seconds)? (Default: infinite)")
        response = input()
        response = float(response.replace(",", ".")) if response is not "" else float("inf")
        config_dict["duration_max"] = response

    # Non-common options that are only available via command line or presets

    if config_dict.get("vote_ratio_max") is None:
        config_dict["vote_ratio_max"] = 1

    if config_dict.get("tmp_dir") is None:
        config_dict["tmp_dir"] = "./tmp"

    if config_dict.get("max_threads") is None:
        config_dict["max_threads"] = 5
    
    if config_dict["scoresaber_limit"] is None:
        config_dict["scoresaber_limit"] = 20

    save_preset = config_dict.get("save_preset")
    if save_preset is not None:
        save_config(config_dict, save_preset)
        print("Preset saved: {}\n Saved to: {}".format(str(config_dict), str(save_config)))

    return config_dict

def save_config(config: dict, path: str):
    path = dir_script.joinpath(Path(path))
    with open(path, "w+") as config_file:
        toml.dump(config, config_file)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--preset", default=default_config_name, help="Path to the preset to use (default: {}".format(default_config_name))
    parser.add_argument("--levels_to_download", help="Number of levels to download. One level may have multiple difficulties!")
    parser.add_argument("--stars_min", type=int, help="Minimum star difficulty for ranked maps")
    parser.add_argument("--stars_max", type=int, help="Maximum star difficulty for ranked maps")
    parser.add_argument("--ranked", type=bool, help="Only download ranked maps (True or False / 1 or 0)")
    parser.add_argument("--scoresaber_sorting", type=int, choices=[0, 1, 2], help="Scoresaber Sorting Mode. Choices: 0 - Trends, 1 - Date Ranked, 2 - Scores Set, 3 - Star Difficulty")
    parser.add_argument("--tmp_dir", type=Path, help="Temporary download dir (default: './download/')")
    parser.add_argument("--download_dir", type=Path, help="Final download folder where custom levels get extracted (usually '[BeatSaberPath]\\Beat Saber_Data\\CustomLevels')")
    parser.add_argument("--max_threads", type=int, help="Maximim thread count to use for downloading.")
    parser.add_argument("--scoresaber_limit", type=int, help="Maps per 'page' for Scoresaber API. There seems to be an upper limit. You usually don't have to change this.")
    parser.add_argument("--save_preset", type=Path, help="Save specified settings into given file. You can load it next time by using --preset")
    parser.add_argument("--vote_ratio_min", type=float, help="Minimum percentage of positive votes of total votes. (Between 0 and 1)")
    parser.add_argument("--vote_ratio_max", type=float, help="Maximum percentage of positive votes of total votes. (Between 0 and 1)")
    parser.add_argument("--duration_min", type=int, help="Minimum song duration in seconds")
    parser.add_argument("--duration_max", type=int, help="Maximum song duration in seconds")
    args = parser.parse_args()

    print("\n-------------------------------------------------------------")
    print("--- Advanced Ranked Beat Saber Map Downloader (ARBSMapDo) ---")
    print("-------------------------------------------------------------\n")
    print("If you want extended filtering, please use the --help argument to see what's currently implemented!")
    print("Do you want to save your config for further use? Use --save_preset 'name'")
    print("If you want to load a specific config, you can use --preset 'name'")
    print("All options are available directly from the command line as well as via presets.\n")

    config = init_config(args)
    config = handle_missing_arguments(config)
    downloader = advanced_downloader(config)
    downloader.start()





