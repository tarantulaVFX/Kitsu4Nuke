# --------------------------NukeStudioKitsuPlugin--------------------------------
#
# (c) 2021 Tarantula
# Authors: Moses Molina, Peter Timberlake
# -------------------------------------------------------------------------------

import os
import os.path as path
import threading

import hiero.core
import nuke

from hiero.exporters import FnTranscodeExporter, FnTranscodeExporterUI, FnExternalRenderUI, FnExternalRender, FnAudioHelper
from hiero.core import events


class KitsuPreviewExporter(FnTranscodeExporter.TranscodeExporter):
    def __init__(self, initDict):
        FnTranscodeExporter.TranscodeExporter.__init__(self, initDict)

        self.uploaded = False
        self.upload_started = False
        self.fullFilePath = ""
        self.fileDir = ""
        self.fullFileName = ""
        self.root = ""
        self.ext = ""
        self.upload_progress = 0.0
        self.upload_reply = None
        self.cancelled = False

        self.session = None
        events.registerInterest(events.EventType.kLoadedKitsuSession, self.getSession)
        events.sendEvent(events.EventType.kRequestKitsuSession, None)

    def getSession(self, event):
        self.session = event.session

    def startTask(self):
        self.fullFilePath = self.resolvedExportPath()
        self.fileDir, self.fullFileName = os.path.split(self.fullFilePath)

        kitsu_prj_id = self._preset.properties()["kitsuProjectID"]
        seq_name = self.sequenceName()
        kitsu_sequence = self.session.getSequenceByName(kitsu_prj_id, seq_name)
        self.kitsu_shot = self.session.createShot(kitsu_prj_id, kitsu_sequence, self.shotName(), frame_in=self.outputRange()[0], frame_out=self.outputRange()[1])
        FnTranscodeExporter.TranscodeExporter.startTask(self)

    def upload(self):
        print("Uploading " + str(self.shotName()) + " ...")
        task_types = self.session.getTaskTypes()
        status_types = self.session.getTaskStatustypes()
        task_type = None
        status_type = None
        for t in task_types:
            if t["name"] == self._preset.properties()["kitsuTaskTypeName"]:
                task_type = t
        for s in status_types:
            if s["name"] == self._preset.properties()["kitsuTaskStatusName"]:
                status_type = s
        task = self.session.createTask(self.kitsu_shot, task_type, status_type)
        (posted_comment, main_prev) = self.session.postComment(task, status_type, "", self.fullFilePath)
        if posted_comment and main_prev:
            if posted_comment.get('type') == "Comment":
                if main_prev.get('preview_file_id'):
                    self.uploaded = True
                    self._finished = True
                    print("Upload Complete: " + str(self.shotName()))
                else:
                    self.setError('Posted, but failed to set main preview!')
            else:
                self.setError('Failed to post!')

    def progress(self):
        if self.uploaded:
            self._finished = True
            return 1.0
        _p = FnTranscodeExporter.TranscodeExporter.progress(self)
        if _p > 1.0:
            _p = 1.0
        return _p / 2.0

    def forcedAbort(self):
        self.cancelled = True
        FnTranscodeExporter.TranscodeExporter.forcedAbort(self)

    def finishTask(self):
        if not self.upload_started and not self.cancelled:
            self.upload_started = True
            threading.Thread(target=self.upload).start()
        elif self.uploaded or self.cancelled:
            FnTranscodeExporter.TranscodeExporter.finishTask(self)
        else:
            pass


class KitsuPreviewPreset(FnTranscodeExporter.TranscodePreset):
    def __init__(self, name, properties):

        hiero.core.RenderTaskPreset.__init__(self, KitsuPreviewExporter, name, properties)

        # Set any preset defaults here
        self.properties()["keepNukeScript"] = False
        self.properties()["readAllLinesForExport"] = self._defaultReadAllLinesForCodec()
        self.properties()["useSingleSocket"] = False
        self.properties()["burninDataEnabled"] = False
        self.properties()["burninData"] = dict((datadict["knobName"], None) for datadict in FnExternalRender.NukeRenderTask.burninPropertyData)
        self.properties()["additionalNodesEnabled"] = False
        self.properties()["additionalNodesData"] = []
        self.properties()["method"] = "Blend"
        self.properties()["includeEffects"] = True
        self.properties()["includeAudio"] = False
        self.properties()["deleteAudio"] = True

        self.properties()["kitsuProjectID"] = ""
        self.properties()["kitsuTaskTypeName"] = ""
        self.properties()["kitsuTaskStatusName"] = ""

        FnAudioHelper.defineExportPresetProperties(self)

        # Give the Write node a name, so it can be referenced elsewhere
        if "writeNodeName" not in self.properties():
          self.properties()["writeNodeName"] = "Write_{ext}"

        self.properties().update(properties)

    def supportedItems(self):
        return hiero.core.TaskPresetBase.kAllItems


class KitsuPreviewExporterUI(FnTranscodeExporterUI.TranscodeExporterUI):
    def __init__(self, preset):
        FnExternalRenderUI.NukeRenderTaskUI.__init__(self, preset, KitsuPreviewExporter, "Kitsu Transcode")
        self._tags = []