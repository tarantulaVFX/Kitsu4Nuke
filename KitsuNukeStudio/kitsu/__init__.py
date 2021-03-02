from .KitsuShotProcessor import (KitsuShotProcessor, KitsuShotProcessorUI, KitsuShotProcessorPreset)
from .KitsuPreviewExporter import (KitsuPreviewExporter, KitsuPreviewExporterUI, KitsuPreviewPreset)

from KitsuUtil.KitsuUtil import *

from hiero.core import events

import nuke

if nuke.env["studio"] and nuke.env.get("gui"):
    hieroKitsuSession = check_user_role()

    def requestKitsuSession(event):
        global hieroKitsuSession
        events.sendEvent(events.EventType.kLoadedKitsuSession, None, session=hieroKitsuSession)

    def loginKitsuSession(event):
        global hieroKitsuSession
        hieroKitsuSession = check_user_role()
        events.sendEvent(events.EventType.kLoadedKitsuSession, None, session=hieroKitsuSession)

    def logoutKitsuSession(event):
        global hieroKitsuSession
        hieroKitsuSession.logout()

    events.registerEventType("kRequestKitsuSession")
    events.registerEventType("kLoadedKitsuSession")
    events.registerEventType("kLoginKitsu")
    events.registerEventType("kLogoutKitsu")

    events.registerInterest(events.EventType.kRequestKitsuSession, requestKitsuSession)
    events.registerInterest(events.EventType.kLoginKitsu, loginKitsuSession)
    events.registerInterest(events.EventType.kLogoutKitsu, logoutKitsuSession)
