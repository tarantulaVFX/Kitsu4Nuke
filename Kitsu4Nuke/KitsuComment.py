# --------------------------Kitsu4Nuke--------------------------------
# PySide2 QDialog for Nuke for rendering and uploading shots to Kitsu
#
# (c) 2021 Tarantula
# Author: Moses Molina
# --------------------------------------------------------------------


from PySide2.QtGui import *
from PySide2.QtWidgets import *

import nuke
import os
import threading
import re
from KitsuUtil import *
import time

this_script = os.path.dirname(os.path.abspath(__file__))


class groupW(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.state = True
        self.rootDir = str(this_script).replace('\\', '/')
        self.arrow = QLabel()
        self.up = QPixmap(self.rootDir + '/res/arrow.png').scaledToHeight(12, Qt.SmoothTransformation)
        self.down = QPixmap(self.rootDir + '/res/arrow_down.png').scaledToHeight(12, Qt.SmoothTransformation)
        self.arrow.setPixmap(self.down)
        self.widgets = None
        self.layout = QVBoxLayout()
        self.name = QLabel('render settings')
        self.top = QHBoxLayout()
        self.top.addWidget(self.arrow)
        self.top.addWidget(self.name)
        self.top.addStretch()
        self.layout.addLayout(self.top)
        self.layout.setMargin(0)
        self.setLayout(self.layout)

    def mousePressEvent(self, event):
        if self.state:
            self.state = False
            self.arrow.setPixmap(self.up)
            self.widgets.hide()
        else:
            self.state = True
            self.arrow.setPixmap(self.down)
            self.widgets.show()


class KitsuComment(QDialog):
    def __init__(self, parent=None, session=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle("Post Comment to Kitsu")
        self.session = session
        self.auto_detect = True
        layout = QVBoxLayout()

        # projects
        self.projectsV = QVBoxLayout()
        self.projectsL = QLabel("project")
        self.projectsC = QListWidget()
        self.projects = []
        self.projectsV.addWidget(self.projectsL)
        self.projectsV.addWidget(self.projectsC)
        self.projectsC.currentItemChanged.connect(self.loadProject)

        # sequences
        self.seqsV = QVBoxLayout()
        self.seqsL = QLabel('sequence')
        self.seqsC = QListWidget()
        self.seqs = []
        self.seqsV.addWidget(self.seqsL)
        self.seqsV.addWidget(self.seqsC)
        self.seqsC.currentItemChanged.connect(self.loadSeq)

        # shots
        self.shotsV = QVBoxLayout()
        self.shotsL = QLabel('shot')
        self.shotsC = QListWidget()
        self.shots = []
        self.shotsV.addWidget(self.shotsL)
        self.shotsV.addWidget(self.shotsC)
        self.shotsC.currentItemChanged.connect(self.loadShot)

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

        # top row
        self.select_row = QHBoxLayout()
        self.select_row.addLayout(self.projectsV)
        self.select_row.addLayout(self.seqsV)
        self.select_row.addLayout(self.shotsV)

        # preview render settings
        self.fpsL = QLabel('FPS')
        self.fps = QDoubleSpinBox()
        self.fps.setValue(24)
        self.fps.setDecimals(3)

        self.deletePrev = QCheckBox('delete mp4 preview after posting')
        self.deletePrev.clicked.connect(self.onDeletePrevClick)
        self.deletePrev.setChecked(True)

        # comment
        self.commentE = QTextEdit()
        self.commentE.setMinimumHeight(50)
        self.commentE.setPlaceholderText('Optional')
        self.commentL = QLabel('comment')

        self.postBtn = QPushButton('post comment')
        self.postBtn.clicked.connect(self.publish)
        self.postBtn.setEnabled(False)
        self.postBtn.setToolTip('no kitsu shot selected')

        self.previewToggle = QCheckBox('attach mp4 preview')
        self.previewToggle.stateChanged.connect(self.onPrevToggle)
        self.previewToggle.setChecked(True)

        self.post_status = QLabel()

        self.post_row = QHBoxLayout()
        self.post_row.addStretch()
        self.post_row.addWidget(self.post_status)
        self.post_row.addWidget(self.postBtn)

        self.commentLayout = QVBoxLayout()
        self.commentLayout.addWidget(self.commentL)
        self.commentLayout.addWidget(self.commentE)

        self.tasksG = QGridLayout()
        self.tasksG.setColumnMinimumWidth(0, 60)
        self.tasksG.addWidget(self.tasksL, 0, 0, alignment=Qt.AlignRight)
        self.tasksG.addWidget(self.tasksC, 0, 1)
        self.tasksG.addItem(QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, 2)
        self.tasksG.addWidget(self.statusL, 1, 0, alignment=Qt.AlignRight)
        self.tasksG.addWidget(self.statusC, 1, 1)
        self.tasksG.addWidget(self.previewToggle, 2, 1)

        self.g = groupW(self)
        self.g.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.widgets = QWidget(self)
        sp = self.widgets.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.widgets.setSizePolicy(sp)
        self.g.widgets = self.widgets

        self.glayout = QGridLayout()
        self.glayout.setColumnMinimumWidth(0, 60)
        self.glayout.setMargin(0)
        self.widgets.setLayout(self.glayout)
        self.glayout.addWidget(self.fpsL, 0, 0, alignment=Qt.AlignRight)
        self.glayout.addWidget(self.fps, 0, 1)
        self.glayout.addItem(QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, 2)
        self.glayout.addWidget(self.deletePrev, 1, 1)

        self.commentLayout.addLayout(self.tasksG)
        self.commentLayout.addWidget(self.g)
        self.commentLayout.addWidget(self.widgets)
        self.commentLayout.addLayout(self.post_row)

        self.line = QFrame()
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)
        self.vline = QFrame()
        self.vline.setFrameShape(QFrame.VLine)
        self.vline.setFrameShadow(QFrame.Sunken)

        self.bot_row = QHBoxLayout()
        self.bot_row.addLayout(self.commentLayout)

        layout.addLayout(self.select_row)
        layout.addWidget(self.line)
        layout.addLayout(self.bot_row)

        self.setLayout(layout)
        self.resize(450, 600)
        self.prev_file = None
        self.rootDir = str(this_script).replace('\\', '/')
        self.supported_files = ('png', 'jpg', 'mp4', 'mov', 'obj', 'pdf', 'ma', 'mb', 'zip', 'rar', 'jpeg', 'svg',
                                'blend', 'wmv', 'm4v', 'ai', 'comp', 'exr', 'psd', 'hip', 'gif', 'ae', 'fla', 'flv',
                                'swf')

    def onDeletePrevClick(self):
        pass

    def afterRender(self):
        nuke.removeAfterRender(self.afterRender)
        self.r = nuke.toNode("kitsu4nuke_reformat")
        self.w = nuke.toNode("kitsu4nuke_write")
        task = self.tasksC.currentData()
        status = self.statusC.currentData()
        comment = self.commentE.toPlainText()
        threading.Thread(target=self.session.postComment, args=(task, status, comment, self.prev_file)).start()

    def renderPrev(self):
        nuke.addAfterRender(self.afterRender)
        prod = self.projectsC.currentItem().text()
        seq = self.seqsC.currentItem().text()
        shot = self.shotsC.currentItem().text()
        self.prev_file = self.rootDir + '/tmp/' + prod + '_' + seq + '_' + shot + '.mp4'

        self.reformatNode = nuke.createNode('Reformat')
        for f in nuke.formats():
            if f.name() == 'HD_720':
                self.reformatNode.knob('format').setValue(f)
                self.reformatNode.knob('name').setValue('kitsu4nuke_reformat')

        self.writeNode = nuke.createNode('Write')
        self.writeNode['file'].setValue(self.prev_file)
        self.writeNode['file_type'].setValue('mov')
        self.writeNode['mov64_codec'].setValue('h264')
        self.writeNode['mov64_fps'].setValue(self.fps.value())
        self.writeNode.knob('name').setValue('kitsu4nuke_write')
        self.writeNode['Render'].execute()

    def getSession(self):
        session = auth_kitsu_account()
        if session:
            self.session = session
            self.session.onPostedComment[str].connect(self.onPostResult)
            nuke.addKnobChanged(self.knobChanged)
            self.knobChanged()
            self.loadProjects()
            self.enableUI()

        else:
            nuke.message('Please login to kitsu.')
            self.close()

    def disableUI(self):
        self.postBtn.setEnabled(False)
        self.projectsC.setEnabled(False)
        self.seqsC.setEnabled(False)
        self.shotsC.setEnabled(False)
        self.tasksC.setEnabled(False)
        self.statusC.setEnabled(False)
        self.previewToggle.setEnabled(False)
        self.commentE.setEnabled(False)
        self.fps.setEnabled(False)
        self.deletePrev.setEnabled(False)

    def enableUI(self):
        self.postBtn.setEnabled(True)
        self.projectsC.setEnabled(True)
        self.seqsC.setEnabled(True)
        self.shotsC.setEnabled(True)
        self.tasksC.setEnabled(True)
        self.statusC.setEnabled(True)
        self.previewToggle.setEnabled(True)
        self.commentE.setEnabled(True)
        self.fps.setEnabled(True)
        self.deletePrev.setEnabled(True)

    def check_can_post(self):
        if self.tasksC.count() > 0:
            self.postBtn.setEnabled(True)
            self.postBtn.setToolTip('post comment to kitsu shot')
            if self.previewToggle.isChecked():
                if len(nuke.selectedNodes()) > 0:
                    node = nuke.selectedNodes()[0]
                    if node.Class() == 'Read':
                        self.postBtn.setEnabled(True)
                        self.postBtn.setToolTip('post comment to kitsu shot')
                        return
                self.postBtn.setEnabled(False)
                self.postBtn.setToolTip('please select a read node to upload')
        else:
            self.postBtn.setEnabled(False)
            self.postBtn.setToolTip('no kitsu shot selected')

    def onPrevToggle(self, state):
        self.check_can_post()

    def onPostResult(self, result):
        if self.previewToggle.isChecked():
            nuke.delete(self.r)
            nuke.delete(self.w)
            if self.deletePrev.isChecked():
                os.remove(self.prev_file)
        self.enableUI()
        self.post_status.setText(result)

    def publish(self):
        self.disableUI()
        task = self.tasksC.currentData()
        status = self.statusC.currentData()
        comment = self.commentE.toPlainText()
        if task and status:
            if self.previewToggle.isChecked():
                self.renderPrev()
            else:
                threading.Thread(target=self.session.postComment, args=(task, status, comment)).start()

    def closeEvent(self, event):
        nuke.removeKnobChanged(self.knobChanged)

    def knobChanged(self):
        self.check_can_post()

    def get_abs_path(self, path):
        if not os.path.isfile(path):
            proj_dir = nuke.root().knob('project_directory').value()
            if proj_dir.endswith('/') and path.startswith('/'):
                proj_dir = proj_dir[:-1]
            elif not proj_dir.endswith('/') and not path.startswith('/'):
                proj_dir += '/'
            path = proj_dir + path
        return path

    def loadProjects(self):
        self.projects = self.session.getProjects()
        nk_script = nuke.Root()['name'].value()
        for project in self.projects:
            item = QListWidgetItem(project['name'], self.projectsC)
            item.setData(Qt.UserRole, project['id'])
            if self.auto_detect:
                prod_match = re.search("^(.*)(" + project['name'] + ")(.*)$", nk_script)
                if prod_match:
                    self.projectsC.setCurrentItem(item)

    def loadProject(self):
        self.seqs = self.session.getSeqsForProj(self.projectsC.currentItem().data(Qt.UserRole))
        self.seqsC.clear()
        self.shotsC.clear()
        self.tasksC.clear()
        self.statusC.clear()
        self.check_can_post()
        nk_script = nuke.Root()['name'].value()
        for seq in self.seqs:
            item = QListWidgetItem(seq['name'], self.seqsC)
            item.setData(Qt.UserRole, seq['id'])
            if self.auto_detect:
                seq_match = re.search("^(.*)(" + self.projectsC.currentItem().text() + ")(.*)(" + seq['name'] + ")(.*)$", nk_script)
                if seq_match:
                    self.seqsC.setCurrentItem(item)

    def loadSeq(self):
        self.shotsC.clear()
        self.tasksC.clear()
        self.statusC.clear()
        self.check_can_post()
        nk_script = nuke.Root()['name'].value()
        if self.seqsC.currentItem() and self.seqsC.currentItem().data(Qt.UserRole):
            self.shots = self.session.getShotsForSeq(self.seqsC.currentItem().data(Qt.UserRole))
            for shot in self.shots:
                item = QListWidgetItem(shot['name'], self.shotsC)
                item.setData(Qt.UserRole, shot['id'])

                if self.auto_detect:
                    r = "^(.*)(" + self.projectsC.currentItem().text() + ")(.*)("
                    r += self.seqsC.currentItem().text() + ")(.*)("
                    r += shot['name'] + ")(.*)$"
                    shot_match = re.search(r, nk_script)
                    if shot_match:
                        self.shotsC.setCurrentItem(item)
            self.auto_detect = False

    def threadedShotLoad(self):
        tasks = self.session.getShotTasks(self.shotsC.currentItem().data(Qt.UserRole))
        if len(tasks) > 0:
            for task in tasks:
                task_type = self.session.getTaskType(task['task_type_id'])
                self.tasksC.addItem(task_type['name'], userData=task)
            self.tasksC.adjustSize()
            statuses = self.session.getTaskStatustypes()
            for status in statuses:
                self.statusC.addItem(status['name'], userData=status)
            self.statusC.setCurrentIndex(0)
            self.check_can_post()

    def loadShot(self):
        self.tasksC.clear()
        self.statusC.clear()
        if self.shotsC.currentItem() and self.shotsC.currentItem().data(Qt.UserRole):
            threading.Thread(target=self.threadedShotLoad).start()
