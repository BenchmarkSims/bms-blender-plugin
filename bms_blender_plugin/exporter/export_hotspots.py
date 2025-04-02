import fileinput
import os


def export_hotspots(hotspots: dict, file_directory):
    """Exports a list of hotspots to the 3dButtons.dat"""
    """Will replace the lines of an existing 3dButtons.dat with new data"""

    if not hotspots or len(hotspots) == 0:
        return
    
    hotspots_filepath = os.path.join(file_directory, "3dButtons.dat")

    # 3dButtons.dat already exists
    if os.path.exists(hotspots_filepath):
        # first: check existing callbacks in the file and update them
        with fileinput.input(hotspots_filepath, inplace=True) as hotspots_file:
            for line in hotspots_file:
                if line.startswith("//") or len(line.strip()) <= 1:
                    print(line, end="")
                else:
                    callback_name = line.split(maxsplit=1)[0]
                    if callback_name in hotspots.keys():
                        hotspot = hotspots.pop(callback_name)
                        print(f"{hotspot}\n", end="")
                    else:
                        print(line, end="")

        # then: append the remaining hotspots
        with open(hotspots_filepath, "a") as hotspots_file:
            for hotspot in hotspots.values():
                hotspots_file.write(f"{hotspot}\n")

    # new file
    else:
        with open(hotspots_filepath, "w") as hotspots_file:
            for hotspot in hotspots.values():
                hotspots_file.write(f"{hotspot}\n")
