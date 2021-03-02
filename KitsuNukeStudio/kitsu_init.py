import hiero.core
from kitsu import (KitsuShotProcessor, KitsuShotProcessorUI, KitsuShotProcessorPreset,
                   KitsuPreviewExporter, KitsuPreviewExporterUI, KitsuPreviewPreset)


hiero.core.taskRegistry.registerProcessor(KitsuShotProcessorPreset, KitsuShotProcessor)
hiero.ui.taskUIRegistry.registerProcessorUI(KitsuShotProcessorPreset, KitsuShotProcessorUI)

hiero.core.taskRegistry.registerTask(KitsuPreviewPreset, KitsuPreviewExporter)
hiero.ui.taskUIRegistry.registerTaskUI(KitsuPreviewPreset, KitsuPreviewExporterUI)