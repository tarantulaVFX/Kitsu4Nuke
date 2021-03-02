# Kitsu4Nuke
Kitsu plugin for Nuke

## OS Support
Current only tested on Windows 10.

## Installation
1. Copy the Kitsu4Nuke folder into your .nuke/ folder.
2. Append init.py to the init.py in your .nuke/ folder:

## Installation for Nuke Studio Kitsu Exporter
1. Install Kitsu4Nuke first (see above).
2. From "KitsuNukeStudio/" copy __*"kitsu/"*__ and __*"kitsu_init.py"*__ from "KitsuNukeStudio/" into your .nuke/Python/Startup folder.
3. From "KitsuNukeStudio/" copy __*"kitsu.KitsuShotProcessor.KitsuShotProcessor/"*__ into your .nuke/TaskPresets/{NukeVersionNumber}/Processors folder, where '{NukeVersionNumber}' is your nuke's version number (i.e. 12.2)
4. **do not copy the "KitsuNukeStudio/" folder itself"**

## Features
- Login to a kitsu server
- Automcaitally detect the kitsu shot based on file path
- Post a comment to a kitsu shot
- Render and attach mp4 previews to comments
- Export from Nuke Studio as shots for kitsu (must have permission to create shots)

&nbsp;  
&nbsp;  
&nbsp;  
#
_(c) 2021 Tarantula_ 
