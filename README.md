# ARBSMapDo - Advanced Ranked Beat Saber Map Downloader

**A standalone release without any prerequisites is available here: https://github.com/Luux/ARBSMapDo/releases**

*Yet another map downloader tool? Who needs that?!?*

While there are plenty of tools and mods that help downloading playlists, trending maps from score saber and more, their filtering options are kinda limited. I wanted a tool with options like "Download 100 new ranked maps that range from 3.5 to 6 star difficulty, have a minimum of 70% positive Votes and a length between 2:00 and 3:30". ARBSMapDo allows to do exactly that.


## Features

* Easy mass downloading of maps crawled from Scoresaber
* It's fast. Both in execution and in handling.
* Filtering options not relying solely on the (undocumented) Scoresaber API - new options can (and will!) be easily added
  - Filter by difficulty, community rating, notes per second, length, ...
* Playlist support - Ever wanted to create a playlist with the best (or worst!) ranked maps? You can do that.
* Give ARBSMapDo a link to BeatSaver, bsaber or Scoresaber and it will download the song. It just works, even with bsaber playlists.
    - You can even download some songs from scoresaber and a playlist from bsaber and automatically add everything to a custom playlist.
* CL usage - want to automate things? Here you go!
* Presets - if you want to apply the same filters and download new maps again in a few weeks, you can simply save your settings
* Open Source, of course.


## Dependencies

Python > 3.4 (due to pathlib) and some libs from requirements.txt. Just run `pip install -r requirements.txt` and you're ready.
Or just use the latest standalone release, which is an ready-to-run .exe ;)


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
usage: arbsmapdo.exe [-h] [--preset PRESET] [-levels LEVELS_TO_DOWNLOAD]xe --help
                     [--noextract] [--stars_min STARS_MIN]
                     [--stars_max STARS_MAX] [--ranked_only RANKED_ONLY]
                     [--scoresaber_sorting {0,1,2}] [--tmp_dir TMP_DIR]
                     [--download_dir DOWNLOAD_DIR]
                     [--playlist_dir PLAYLIST_DIR] [--max_threads MAX_THREADS]
                     [--scoresaber_maxlimit SCORESABER_MAXLIMIT]
                     [--save_preset SAVE_PRESET]
                     [--beatmap_rating_min BEATMAP_RATING_MIN]
                     [--beatmap_rating_max BEATMAP_RATING_MAX]
                     [--length_min LENGTH_MIN] [--length_max LENGTH_MAX]
                     [--nps_min NPS_MIN] [--nps_max NPS_MAX]
                     [--notes_min NOTES_MIN] [--notes_max NOTES_MAX]
                     [--rescan] [--beatsaver_cachefile BEATSAVER_CACHEFILE]
                     [--levelhash_cachefile LEVELHASH_CACHEFILE]
                     [--playlist PLAYLIST] [--playlist_image PLAYLIST_IMAGE]
                     [-s]
                     [URIs [URIs ...]]

positional arguments:
  URIs                  URI (Path or URL) to map or playlist (*.bplist).
                        ARBSMapDo will download and install the specified
                        map/list.

optional arguments:
  -h, --help            show this help message and exit
  --preset PRESET       Path to the preset to use (default:
                        arbsmapdo_default.toml
  -levels LEVELS_TO_DOWNLOAD, --levels_to_download LEVELS_TO_DOWNLOAD
                        Number of levels to download. One level may have
                        multiple difficulties!
  --noextract           Do not extract *.zip files. Helpful for Quest users as
                        you can upload them directly to BMBF!
  --stars_min STARS_MIN
                        Minimum star difficulty for ranked maps
  --stars_max STARS_MAX
                        Maximum star difficulty for ranked maps
  --ranked_only RANKED_ONLY
                        Only download ranked maps (True or False / 1 or 0)
  --scoresaber_sorting {0,1,2}
                        Scoresaber Sorting Mode. Choices: 0 - Trends, 1 - Date
                        Ranked, 2 - Scores Set, 3 - Star Difficulty
  --tmp_dir TMP_DIR     Temporary download dir (default: './download/')
  --download_dir DOWNLOAD_DIR
                        Final download folder where custom levels get
                        extracted (usually '[BeatSaberPath]\Beat
                        Saber_Data\CustomLevels')
  --playlist_dir PLAYLIST_DIR
                        Directory where playlist files will be saved at
                        (usually '[BeatSaberPath]\Playlists')
  --max_threads MAX_THREADS
                        Maximim thread count to use for downloading.
  --scoresaber_maxlimit SCORESABER_MAXLIMIT
                        Maximum maps per 'page' for Scoresaber API. (You
                        usually don't have to change this.)
  --save_preset SAVE_PRESET
                        Save specified settings into given file. You can load
                        it next time by using --preset
  --beatmap_rating_min BEATMAP_RATING_MIN
                        Minimum beatmap rating. (Between 0 and 1)
  --beatmap_rating_max BEATMAP_RATING_MAX
                        Maximum beatmap rating. (Between 0 and 1)
  --length_min LENGTH_MIN
                        Minimum map length in seconds
  --length_max LENGTH_MAX
                        Maximum map length in seconds
  --nps_min NPS_MIN     Minimum notes per second
  --nps_max NPS_MAX     Maximum notes per second
  --notes_min NOTES_MIN
                        Minimum total note count
  --notes_max NOTES_MAX
                        Maximum total note count
  --rescan              Force rescan of already downloaded songs. This resets
                        the cache and results in manually deleted songs being
                        in the pool again.
  --beatsaver_cachefile BEATSAVER_CACHEFILE
                        Cache file used for BeatSaver cache. (You usually
                        don't have to change this.)
  --levelhash_cachefile LEVELHASH_CACHEFILE
                        Cache file used for caching already calculated level
                        hashes. (You usually don't have to change this.)
  --playlist PLAYLIST   Playlist (file name) where levels from this session
                        should be added. If the specified playlist does not
                        exist yet, it will be created.
  --playlist_image PLAYLIST_IMAGE
                        When creating a new playlist, use this image. If not
                        given, the default image will be used.
  -s, --skip_assistant  Skip assistant except for neccessary things. You'll
                        need to specify every argument via command line or
                        preset
```


## Legal Disclaimer

ARBSMapDo is a tool that helps filtering and downloading Custom Levels for the Game *Beat Saber* developed by *Beat Games*. The level information is accessed from both the scoresaber API and BeatSaver. The levels itself are user-generated content hosted on BeatSaver, which is where they are downloaded from as well. BeatSaver allows users to upload these levels and hosts them for other users to download. I am not affiliated with BeatSaver in any form, nor do I host user-generated content myself. Any potential copyright infringements have to be directly reported to BeatSaver via a DCMA request at https://beatsaver.com/legal/dmca as I am not responsible for any content hosted there.
