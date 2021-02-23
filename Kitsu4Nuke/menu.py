# --------------------------Kitsu4Nuke--------------------------------
# menu.py for initializing Kitsu4Nuke
#
# (c) 2021 Tarantula
# Author: Moses Molina
# --------------------------------------------------------------------

import sys
import os
import nuke

import Kitsu4Nuke
nuke.menu('Nuke').addCommand('Kitsu/Post Comment', "Kitsu4Nuke.comment()")
nuke.menu('Nuke').addCommand('Kitsu/Login', "Kitsu4Nuke.login()")
