# --------------------------Kitsu4Nuke--------------------------------
# Functions for attaching to nuke menu actions
#
# (c) 2021 Tarantula
# Author: Moses Molina
# email:  moses.tarantula@gmail.com
# --------------------------------------------------------------------

from KitsuComment import KitsuComment
from KitsuLogin import KitsuLogin

from PySide2.QtWidgets import *
from PySide2.QtCore import *


def login():
    login_dlg = KitsuLogin(QApplication.activeWindow())
    login_dlg.show()


def comment():
    kitsu_publish_dlg = KitsuComment(QApplication.activeWindow())
    kitsu_publish_dlg.show()
    kitsu_publish_dlg.disableUI()
    QTimer.singleShot(100, kitsu_publish_dlg.getSession)
