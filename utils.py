from pathlib import Path
import json
import hashlib

def calculate_Level_hash(levelPath):
    levelPath = Path(levelPath)
    infoPath = levelPath.joinpath("./info.dat")

    with open(infoPath, "rb") as tmpfile:
        info_binary = tmpfile.read()
        info_data = json.loads(info_binary, encoding="utf-8")

    # We need to calculate sha1 hashes of the concatenation of info.dat and each difficulty listed there
    hasher = hashlib.sha1()
    hasher.update(info_binary)

    # List difficulties
    difficulty_sets = info_data.get("_difficultyBeatmapSets")
    
    # Read each difficulty file
    for diffset in difficulty_sets:
        for beatmap in diffset.get("_difficultyBeatmaps"):
            beatmap_filename = beatmap.get("_beatmapFilename")
            beatmap_filepath = levelPath.joinpath(beatmap_filename)

            # Read difficulty file and concatenate to the binary info data
            with open(beatmap_filepath, "rb") as tmpfile:
                diff_binary = tmpfile.read()
                hasher.update(diff_binary)
    
    # Calculate the final hash
    sha1 = hasher.hexdigest()

    return sha1


