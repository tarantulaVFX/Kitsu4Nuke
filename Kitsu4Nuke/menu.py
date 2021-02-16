# --------------------------Kitsu4Nuke--------------------------------
# menu.py for initializing Kitsu4Nuke
#
# (c) 2021 Tarantula
# Author: Moses Molina
# email:  moses.tarantula@gmail.com
# --------------------------------------------------------------------

import sys
import os
import nuke

p = os.path.dirname(os.path.abspath(__file__))
rootDir = str(p).replace('\\', '/')
libs = rootDir + "/libs"   
sys.path.append(libs)

import Kitsu4Nuke
nuke.menu('Nuke').addCommand('Kitsu/Post Comment', "Kitsu4Nuke.comment()")
nuke.menu('Nuke').addCommand('Kitsu/Login', "Kitsu4Nuke.login()")
