#>-------------- Kitsu4Nuke Start--------------#
p = os.path.dirname(os.path.abspath(__file__)) #
rootDir = str(p).replace('\\', '/')            #
Kitsu4Nuke = rootDir + "/Kitsu4Nuke"           #
nuke.pluginAddPath(Kitsu4Nuke)                 #
#>-------------- Kitsu4Nuke End  --------------#
