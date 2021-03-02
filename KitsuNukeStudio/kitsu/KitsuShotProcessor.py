# --------------------------NukeStudioKitsuPlugin--------------------------------
#
# (c) 2021 Tarantula
# Authors: Moses Molina, Peter Timberlake
# -------------------------------------------------------------------------------

import os
import os.path as path
import json
import threading
import nuke
import re
import shiboken2
import hiero.core

from hiero.exporters import FnShotProcessor
from hiero.exporters.FnExportKeywords import kFileBaseKeyword, kFileHeadKeyword, kFilePathKeyword, KeywordTooltips
from hiero.ui import FnProcessorUI
from hiero.core import events

from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *

try:
    from hiero.exporters.FnShotProcessorUI import ShotProcessorUI
except ImportError:
    ShotProcessorUI = FnShotProcessor.ShotProcessor

from KitsuUtil.KitsuUtil import *
from .KitsuPreviewExporter import *


class KitsuShotProcessorUI(ShotProcessorUI):
    def __init__(self, preset):
        ShotProcessorUI.__init__(self, preset)
        self.auto_detect = True
        self.session = None
        self.selectedRow = -1
        self.selectedData = None
        self.kitsu_supported_files = ('png', 'jpg', 'mp4', 'mov', 'obj', 'pdf', 'ma', 'mb', 'zip', 'rar', 'jpeg', 'svg',
                                      'blend', 'wmv', 'm4v', 'ai', 'comp', 'exr', 'psd', 'hip', 'gif', 'ae', 'fla',
                                      'flv',
                                      'swf')
        self.session = None
        events.registerInterest(events.EventType.kLoadedKitsuSession, self.getSession)
        events.sendEvent(events.EventType.kRequestKitsuSession, None)

    def displayName(self):
        return "Kitsu Shot Export"

    def toolTip(self):
        return "Update Shots In Kitsu"

    def validate(self, exportItems):
        if self.session == -1:
            nuke.message("Please login to kitsu.")
            return False
        elif self.session == -2:
            nuke.message("Your kitsu account does not have the permission to create shots.")
            return False
        elif self.session:
            if self.projectsC.currentRow() > 0:
                self.preset().properties()["kitsuProjectID"] = self.projectsC.currentItem().data(Qt.UserRole)
                self.preset().properties()["kitsuTaskTypeName"] = self.tasksC.currentText()
                self.preset().properties()["kitsuTaskStatusName"] = self.statusC.currentText()

                foundKitsuPrev = False
                for (exportPath, preset) in self._exportTemplate.flatten():
                    if "kitsuProjectID" in preset.properties():
                        foundKitsuPrev = True
                        if preset.properties()["file_type"] != "mov":
                            nuke.message("kitsu uploader current only supports mov file type. ")
                            return False
                if foundKitsuPrev:
                    return ShotProcessorUI.validate(self, exportItems)
                else:
                    nuke.message("Did not find a KitsuPreviewExporter in the export structure.")
                    return False
            else:
                nuke.message("Please select a kitsu project.")
                return False
        else:
            nuke.message("Unknown kitsu error.")
            return False

    def loadProjects(self):
        self.projects = self.session.getAllProjects()
        nk_script = nuke.Root()['name'].value()
        self.projectsC.clear()
        for project in self.projects:
            item = QListWidgetItem(project['name'])
            item.setData(Qt.UserRole, project['id'])
            self.projectsC.addItem(item)

            if self.auto_detect:
                prod_match = re.search("^(.*)(" + project['name'] + ")(.*)$", nk_script)
                if prod_match:
                    self.projectsC.setCurrentItem(item)

    def loadProject(self, item):
        if self.auto_detect:
            self.auto_detect = False

    def loadTasks(self):
        task_types = self.session.getTaskTypes()
        self.tasksC.clear()
        for _type in task_types:
            if _type["for_shots"]:
                self.tasksC.addItem(_type["name"], _type)
        self.tasksC.setCurrentIndex(0)
        statuses = self.session.getTaskStatustypes()
        self.statusC.clear()
        for status in statuses:
            self.statusC.addItem(status['name'], userData=status)
        self.statusC.setCurrentIndex(0)

    def onPostResult(self, result):
        pass
        # if self.previewToggle.isChecked():
        #     nuke.delete(self.r)
        #     nuke.delete(self.w)
        #     if self.deletePrev.isChecked():
        #         os.remove(self.prev_file)
        # self.enableUI()
        # self.post_status.setText(result)

    def kitsuInit(self):
        if shiboken2.isValid(self.loadL):
            self.loadL.hide()
            if self.session == -1:
                nuke.message("Please login to kitsu.")
            elif self.session == -2:
                nuke.message("Your kitsu account does not have the permission to create shots.")
            elif self.session:
                self.session.onPostedComment[str].connect(self.onPostResult)
                self.loadProjects()
                self.loadTasks()

    def getSession(self, event):
        self.session = event.session

    def populateUI(self, *args, **kwargs):
        # Create proxy widget so we can add our own ui
        (widget, taskUIWidget, exportItems) = args
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        default = QWidget(None)
        main_layout.addWidget(default)

        # Logo
        logo_path = path.abspath(path.dirname(path.relpath(__file__)).replace('\\', '/') + "/logo.png").replace('\\', '/')
        if os.path.exists(logo_path):
            self.logo = QPixmap(logo_path)
        else:
            self.logo = QPixmap()

        # Header
        self.lineF = QFrame()
        self.lineF.setFrameShape(QFrame.HLine)
        self.lineF.setFrameShadow(QFrame.Sunken)
        self.logoL = QLabel()
        self.logoL.setPixmap(self.logo.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.loadL = QLabel("<font color=\"#a3a3a3\">(Loading ...)</font>")
        logo_layout = QHBoxLayout()
        logo_layout.addWidget(self.logoL)
        logo_layout.addWidget(QLabel("Kitsu Settings"))
        logo_layout.addWidget(self.loadL)
        logo_layout.addStretch()

        # Project Select
        self.projectsV = QVBoxLayout()
        self.projectsL = QLabel("project")
        self.projectsC = QListWidget()
        self.projects = []
        self.projectsV.addWidget(self.projectsL)
        self.projectsV.addWidget(self.projectsC)
        self.projectsC.currentItemChanged.connect(self.loadProject)

        # sequence
        seqE = QLineEdit()
        seqE.setText("{sequence}")
        seqE.setReadOnly(True)
        seqE.setEnabled(False)

        # shot
        shotE = QLineEdit()
        shotE.setText("{shot}")
        shotE.setReadOnly(True)
        shotE.setEnabled(False)

        # tasks
        self.tasksL = QLabel('task')
        self.tasksC = QComboBox()
        self.tasksC.setEditable(False)
        self.tasksC.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

        # statuses
        self.statusL = QLabel('task status')
        self.statusC = QComboBox()
        self.statusC.setEditable(False)
        self.statusC.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

        # Layout Setup
        shot_layout = QHBoxLayout()
        shot_layout.addLayout(self.projectsV)

        self.tasksG = QGridLayout()
        self.tasksG.setColumnMinimumWidth(0, 60)
        self.tasksG.addWidget(QLabel(), 0, 0)
        self.tasksG.addItem(QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, 2)
        self.tasksG.addWidget(QLabel("sequence"), 1, 0, alignment=Qt.AlignRight)
        self.tasksG.addWidget(seqE, 1, 1)
        self.tasksG.addWidget(QLabel("shot"), 2, 0, alignment=Qt.AlignRight)
        self.tasksG.addWidget(shotE, 2, 1)
        self.tasksG.addWidget(self.tasksL, 3, 0, alignment=Qt.AlignRight)
        self.tasksG.addWidget(self.tasksC, 3, 1)
        self.tasksG.addWidget(self.statusL, 4, 0, alignment=Qt.AlignRight)
        self.tasksG.addWidget(self.statusC, 4, 1)
        self.tasksG.addItem(QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding), 5, 0)
        shot_layout.addLayout(self.tasksG)

        main_layout.addWidget(self.lineF)
        main_layout.addLayout(logo_layout)
        main_layout.addLayout(shot_layout)

        if self._exportItems:
            self.kitsuInit()

        # Call super function
        FnProcessorUI.ProcessorUIBase.populateUI(self, default, taskUIWidget, exportItems)


class KitsuShotProcessor(FnShotProcessor.ShotProcessor):
    def __init__(self, preset, submission=None, synchronous=False):
        FnShotProcessor.ShotProcessor.__init__(self, preset, submission, synchronous)
        self.session = None
        events.registerInterest(events.EventType.kLoadedKitsuSession, self.getSession)
        events.sendEvent(events.EventType.kRequestKitsuSession, None)

    def getSession(self, event):
        self.session = event.session

    def processKitsuShots(self, exportItems):
        sequences = []
        # Track items were selected
        if exportItems[0].trackItem():
            sequences.append(exportItems[0].trackItem().parent().parent())
        else:
            # Items were selected in the project panel. Build a list of selected sequences
            sequences = [item.sequence() for item in exportItems if item.sequence() is not None]

        kitsuSeqs = self.session.getAllSeqsForProj(self.preset().properties()["kitsuProjectID"])
        kitsuSeqNames = []
        for seq in kitsuSeqs:
            kitsuSeqNames.append(seq["name"])
        for seq in sequences:
            if seq.name() in kitsuSeqNames:
                pass
            else:
                newSeq = self.session.createSequence(self.preset().properties()["kitsuProjectID"], seq.name())
                kitsuSeqs.append(newSeq)

    def startProcessing(self, exportItems, preview=False):
        if preview:
            return FnShotProcessor.ShotProcessor.startProcessing(self, exportItems, preview)

        if self.session == -1:
            pass
        elif self.session == -2:
            pass
        elif self.session:
            self.processKitsuShots(exportItems)
            for (exportPath, preset) in self._exportTemplate.flatten():
                if "kitsuProjectID" in preset.properties():
                    preset.properties()["kitsuProjectID"] = self.preset().properties()["kitsuProjectID"]
                    preset.properties()["kitsuTaskTypeName"] = self.preset().properties()["kitsuTaskTypeName"]
                    preset.properties()["kitsuTaskStatusName"] = self.preset().properties()["kitsuTaskStatusName"]

            FnShotProcessor.ShotProcessor.startProcessing(self, exportItems, preview)


class KitsuShotProcessorPreset(hiero.core.ProcessorPreset):
    def __init__(self, name, properties):
        hiero.core.ProcessorPreset.__init__(self, KitsuShotProcessor, name)

        # setup defaults
        self._excludedTrackIDs = []
        self.nonPersistentProperties()["excludedTracks"] = []
        self.properties()["excludeTags"] = []
        self.properties()["includeTags"] = []
        self.properties()["versionIndex"] = 1
        self.properties()["versionPadding"] = 2
        self.properties()["exportTemplate"] = ( )
        self.properties()["exportRoot"] = "{projectroot}"
        self.properties()["cutHandles"] = 12
        self.properties()["cutUseHandles"] = False
        self.properties()["cutLength"] = False
        self.properties()["includeRetimes"] = False
        self.properties()["startFrameIndex"] = 1001
        self.properties()["startFrameSource"] = KitsuShotProcessor.kStartFrameSource

        self.properties()["kitsuProjectID"] = ""
        self.properties()["kitsuTaskTypeName"] = ""
        self.properties()["kitsuTaskStatusName"] = ""


        self.properties().update(properties)

        # This remaps the project root if os path remapping has been set up in the preferences
        self.properties()["exportRoot"] = hiero.core.remapPath(self.properties()["exportRoot"])

    def addCustomResolveEntries(self, resolver):
        """addDefaultResolveEntries(self, resolver)
        Create resolve entries for default resolve tokens shared by all task types.
        @param resolver : ResolveTable object"""

        resolver.addResolver("{filename}", "Filename of the media being processed",
                             lambda keyword, task: task.fileName())
        resolver.addResolver(kFileBaseKeyword, KeywordTooltips[kFileBaseKeyword], lambda keyword, task: task.filebase())
        resolver.addResolver(kFileHeadKeyword, KeywordTooltips[kFileHeadKeyword], lambda keyword, task: task.filehead())
        resolver.addResolver(kFilePathKeyword, KeywordTooltips[kFilePathKeyword], lambda keyword, task: task.filepath())
        resolver.addResolver("{filepadding}", "Source Filename padding for formatting frame indices", lambda keyword, task: task.filepadding())
        resolver.addResolver("{fileext}", "Filename extension part of the media being processed", lambda keyword, task: task.fileext())
        resolver.addResolver("{clip}", "Name of the clip used in the shot being processed", lambda keyword, task: task.clipName())
        resolver.addResolver("{shot}", "Name of the shot being processed", lambda keyword, task: task.shotName())
        resolver.addResolver("{track}", "Name of the track being processed", lambda keyword, task: task.trackName())
        resolver.addResolver("{sequence}", "Name of the sequence being processed", lambda keyword, task: task.sequenceName())
        resolver.addResolver("{event}", "EDL event of the track item being processed", lambda keyword, task: task.editId())
        resolver.addResolver("{_nameindex}", "Index of the shot name in the sequence preceded by an _, for avoiding clashes with shots of the same name", lambda keyword, task: task.shotNameIndex())

    # check that all nuke shot exporters have at least one write node
    def isValid(self):
        allNukeShotsHaveWriteNodes = True

        for itemPath, itemPreset in self.properties()["exportTemplate"]:
            isNukeShot = isinstance(itemPreset, hiero.exporters.FnNukeShotExporter.NukeShotPreset)
            if isNukeShot and not itemPreset.properties()["writePaths"]:
                allNukeShotsHaveWriteNodes = False
                return (False, "Your Export Structure has no Write Nodes defined.")
        return (True, "")
