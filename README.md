# ARBSMapDo - Advanced Ranked Beat Saber Map Downloader

(WIP - some things ~~may~~ *will* still be broken. Please help me finding bugs! :) )

*Yet another map downloader tool? Who needs this?!?*

While there are plenty of tools and mods that help downloading playlists, trending maps from score saber and more, their filtering options are kinda limited. I wanted a tool with options like "Download 100 new ranked maps that range from 3.5 to 6 star difficulty, have a minimum of 70% positive Votes and a length between 2:00 and 3:30". ARBSMapDo allows exactly that.

## Features

* Easy mass downloading of (mostly ranked) maps crawled from Scoresaber
* Filtering options not relying solely on the (undocumented) Scoresaber API - new options can (and will!) be easily added
* Presets - if you want to apply the same filters and download new maps again in a few weeks, you can simply save your settings
* Open Source, of course.


## Dependencies

Python > 3.4 (due to pathlib) and some libs from requirements.txt. Just run `pip install -r requirements.txt` and you're ready.


## Usage

There are currently 3 ways to specify filters:
1) Without any arguments. There will be an assistant that guides you through common options. Some advanced options will not be shown.
2) Command line usage
3) Using a preset file



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
usage: arbsmapdo.py [-h] [--preset PRESET]
                    [--levels_to_download LEVELS_TO_DOWNLOAD]
                    [--stars_min STARS_MIN] [--stars_max STARS_MAX]
                    [--ranked RANKED] [--scoresaber_sorting {0,1,2}]
                    [--tmp_dir TMP_DIR] [--download_dir DOWNLOAD_DIR]
                    [--max_threads MAX_THREADS]
                    [--scoresaber_limit SCORESABER_LIMIT]
                    [--save_preset SAVE_PRESET]
                    [--vote_ratio_min VOTE_RATIO_MIN]
                    [--vote_ratio_max VOTE_RATIO_MAX]
                    [--duration_min DURATION_MIN]
                    [--duration_max DURATION_MAX]

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
                        Maximum thread count to use for downloading.
  --scoresaber_limit SCORESABER_LIMIT
                        Maps per 'page' for Scoresaber API. There seems to be
                        an upper limit. You usually don't have to change this.
  --save_preset SAVE_PRESET
                        Save specified settings into given file. You can load
                        it next time by using --preset
  --vote_ratio_min VOTE_RATIO_MIN
                        Minimum percentage of positive votes of total votes.
                        (Between 0 and 1)
  --vote_ratio_max VOTE_RATIO_MAX
                        Maximum percentage of positive votes of total votes.
                        (Between 0 and 1)
  --duration_min DURATION_MIN
                        Minimum song duration in seconds
  --duration_max DURATION_MAX
                        Maximum song duration in seconds
```


## Legal Disclaimer

ARBSMapDo is a tool that helps filtering and downloading Custom Levels for the Game *Beat Saber* developed by *Beat Games*. The level information is accessed from both the scoresaber API and BeatSaver. The levels itself are user-generated content hosted on BeatSaver, which is where they are downloaded from as well. BeatSaver allows users to upload these levels and hosts them for other users to download. I am not affiliated with BeatSaver in any form, nor do I host user-generated content myself. Any potential copyright infringements have to be directly reported to BeatSaver via a DCMA request at https://beatsaver.com/legal/dmca as I am not responsible for any content hosted there.
