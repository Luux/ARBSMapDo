# ARBSMapDo - Advanced Ranked Beat Saber Map Downloader

*Yet another map downloader tool? Who needs this?!?*

While there are plenty of tools and mods that help downloading playlists, trending maps from score saber and more, their filtering options are kinda limited. I wanted a tool with options like "Download 100 new ranked maps that range from 3.5 to 6 star difficulty, have a minimum of 70% positive Votes and a length between 2:00 and 3:30". ARBSMapDo allows exactly that.

## Features

* Easy and fast downloading of (mostly ranked) maps crawled from Scoresaber
* Filtering options not relying solely on the (undocumented) Scoresaber API - new options can (and will!) be easily added
* Presets - if you want to apply the same filters and download new maps again in a few weeks, you can simply save your settings
* Open Source, of course.


## Dependencies

Python > 3.4 (due to pathlib) and some libs from requirements.txt. Just run `pip install -r requirements.txt` and you're ready.


## Usage

You can either run arbsmapdo.py without any arguments to run an assistant (may be missing some advanced config stuff), specify some options from the command line or use a preset file.


### Presets

Preset files are in TOML format, so you can just create a txt file of the form
```
download_dir = "C:\\path\\to\\custom\\songs"
levels_to_download = 100
...
...
```
The options in the preset file are named the same as the command line options listed below. If you load a preset and have additional command line arguments, the specified command line args overwrite the variables in the preset. (These are not saved unless specified with --save_preset though!)


### Options

Currently available command line options (more to be implemented):

```
arbsmapdo.py --help

usage: arbsmapdo.py [-h] [--preset PRESET]
                    [--levels_to_download LEVELS_TO_DOWNLOAD]
                    [--stars_min STARS_MIN] [--stars_max STARS_MAX]
                    [--ranked RANKED] [--scoresaber_sorting {0,1,2}]
                    [--tmp_dir TMP_DIR] [--download_dir DOWNLOAD_DIR]
                    [--max_threads MAX_THREADS]
                    [--scoresaber_limit SCORESABER_LIMIT]
                    [--save_preset SAVE_PRESET]

optional arguments:
  -h, --help            show this help message and exit
  --preset PRESET       Path to the preset to use (default:
                        arbsmapdo_default.toml
  --levels_to_download LEVELS_TO_DOWNLOAD
                        Number of levels to download. One level may have
                        multiple difficulties!
  --stars_min STARS_MIN
                        Minimum star difficulty for ranked maps
  --stars_max STARS_MAX
                        Maximum star difficulty for ranked maps
  --ranked RANKED       Only download ranked maps (True or False / 1 or 0)
  --scoresaber_sorting {0,1,2}
                        Scoresaber Sorting Mode. Choices: 0 - Trends, 1 - Date
                        Ranked, 2 - Scores Set, 3 - Star Difficulty
  --tmp_dir TMP_DIR     Temporary download dir (default: './download/')
  --download_dir DOWNLOAD_DIR
                        Final download folder where custom levels get
                        extracted (usually '[BeatSaberPath]\Beat
                        Saber_Data\CustomLevels')
  --max_threads MAX_THREADS
                        Maximim thread count to use for downloading.
  --scoresaber_limit SCORESABER_LIMIT
                        Maps per 'page' for Scoresaber API. There seems to be
                        an upper limit. You usually don't have to change this.
  --save_preset SAVE_PRESET
                        Save specified settings into given file. You can load
                        it next time by using --preset
```
