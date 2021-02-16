# Kitsu4Nuke
Kitsu plugin for Nuke

## Installation
Copy the Kitsu4Nuke folder into your /.nuke folder and append the following to the init.py:

\#>-------------- Kitsu4Nuke Start--------------\#
p = os.path.dirname(os.path.abspath(__file__)) \#
rootDir = str(p).replace('\\', '/')            \#
Kitsu4Nuke = rootDir + "/Kitsu4Nuke"           \#
nuke.pluginAddPath(Kitsu4Nuke)                 \#
\#>-------------- Kitsu4Nuke End  --------------\#
