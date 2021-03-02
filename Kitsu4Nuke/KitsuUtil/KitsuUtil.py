# --------------------------Kitsu4Nuke--------------------------------
# Helper Classes and Functions for Kitsu4Nuke
#
# (c) 2021 Tarantula
# Author: Moses Molina
# --------------------------------------------------------------------

import os
import sys
import json
import base64
import hashlib
import libs.gazu as gazu
import nuke

from libs.Cryptodome.Cipher import AES
from libs.Cryptodome import Random
from PySide2.QtCore import *
from libs.gazu.exception import AuthFailedException

empty_conf = {'kitsu_email': "", 'kitsu_password': "", "kitsu_url": ""}


class AESCipher(object):
    def __init__(self, key):
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode()))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]


def removeLastSlash(address):
    if address[-1:] == "/":
        address = address[:-1]

    return address


def auth_kitsu_account():
    try:
        config = getConfig()
        if config:
            client = KitsuSession(config)
            if client.tokens:
                return client

    except Exception as e:
        nuke.message('Unexpected error while trying to authorize account info.')

    return False


def check_user_role():
    session = auth_kitsu_account()
    if session:
        # This check relies on kitsu only allowing Supervisors and Managers to see the "role" data of a person.
        # More specifically, it relies on all other types of users not being able to see their own role. 
        # I do not like this check, but it works for now.
        if session.person.get("role"):
            return session
        else:
            return -2
    else:
        return -1


class KitsuSession(QObject):
    onPostedComment = Signal(str)

    def __init__(self, config, parent=None):
        QObject.__init__(self, parent)
        self.config = config
        self.tokens = None
        self.status = ''
        self.authenticate()

    def notify_poster(self, result):
        self.onPostedComment.emit(result)

    def getProjects(self):
        return gazu.user.all_open_projects()

    def getAllProjects(self):
        return gazu.project.all_projects()

    def getSeqsForProj(self, id):
        return gazu.user.all_sequences_for_project(id)

    def getAllSeqsForProj(self, id):
        return gazu.shot.all_sequences_for_project(id)

    def getShotsForSeq(self, id):
        return gazu.user.all_shots_for_sequence(id)

    def getAllShotsForSeq(self, id):
        return gazu.shot.all_shots_for_sequence(id)  

    def getShotTasks(self, id):
        # return gazu.task.all_tasks_for_shot(id)
        return gazu.user.all_tasks_for_shot(id)

    def getTaskStatustypes(self):
        return gazu.task.all_task_statuses()

    def getTaskTypes(self):
        return gazu.task.all_task_types()

    def getTaskType(self, task_type_id):
        return gazu.task.get_task_type(task_type_id)

    def getSequenceByName(self, project_id, name):
        return gazu.shot.get_sequence_by_name(project_id, name)
        
    def createSequence(self, project_id, name):
        return gazu.shot.new_sequence(project_id, name)
    
    def createShot(self, project, sequence, shot, frame_in=0, frame_out=100):
        return gazu.shot.new_shot(project, sequence, shot, frame_in=frame_in, frame_out=frame_out)
    
    def createTask(self, entity, task_type, task_status):
        return gazu.task.new_task(entity, task_type, task_status=task_status)
    
    def postComment(self, in_task, in_status, comment, file=None):
        try:
            task = self.getTask(in_task['id'])
            task_status = self.getTaskStatus(in_status['id'])
            if comment == '':
                posted_comment = gazu.task.add_comment(task, task_status)
            else:
                posted_comment = gazu.task.add_comment(task, task_status, comment)

            prev_file = None
            main_prev = None
            if file:
                prev_file = gazu.task.add_preview(task, posted_comment, file)
                main_prev = gazu.task.set_main_preview(prev_file)

            if posted_comment.get('type') == "Comment":
                if file:
                    if prev_file.get('type') == "PreviewFile":
                        if main_prev.get('preview_file_id') == prev_file.get('id'):
                            self.notify_poster('Posted!')
                        else:
                            self.notify_poster('Posted, but failed to set main preview!')
                    else:
                        self.notify_poster('Posted, but failed to upload preview file!')
                else:
                    self.notify_poster('Posted!')
            else:
                self.notify_poster('Failed to post!')
            return (posted_comment, main_prev)
        except Exception as e:
            self.notify_poster('Failed to post: ' + str(e))
            return (False, False)

    def getTaskStatus(self, id):
        return gazu.task.get_task_status(id)

    def getTask(self, id):
        return gazu.task.get_task(id)

    def getShot(self, id):
        return gazu.shot.get_shot(id)

    def logout(self):
        gazu.log_out()

    def authenticate(self):
        host = removeLastSlash(self.config['kitsu_url'])
        host = host + "/api"
        gazu.set_host(host)
        if not gazu.client.host_is_up():
            self.status = 'Could not connect to kitsu server.'
            return

        try:
            self.tokens = gazu.log_in(self.config['kitsu_email'], self.config['kitsu_password'])
            if not self.tokens:
                self.status = 'Failed to login'
            else:
                self.person = gazu.person.get_person_by_email(self.config['kitsu_email'])
        except AuthFailedException as e:
            self.tokens = None
            self.status = 'Wrong username or password'


cipher = AESCipher("default")


def getConfig():
    rootDir = str(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
    conf_file = rootDir + "/config.json"

    try:
        if not os.path.isfile(conf_file):
            with open(conf_file, "w+") as conf:

                conf.write(json.dumps(empty_conf, indent=4))
                conf.close()

        with open(conf_file, "r") as conf:
            config = json.load(conf)
            conf.close()

            config['kitsu_email'] = cipher.decrypt(config['kitsu_email'])
            config['kitsu_password'] = cipher.decrypt(config['kitsu_password'])

            return config

    except:
        return None


def setConfig(new_config):
    try:
        rootDir = str(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
        conf_file = rootDir + "/config.json"

        with open(conf_file, 'w+') as conf:
            new_config['kitsu_email'] = cipher.encrypt(new_config['kitsu_email'])
            new_config['kitsu_password'] = cipher.encrypt(new_config['kitsu_password'])

            conf.write(json.dumps(new_config, indent=4))
            conf.close()
            return True
    except:
        pass

    return False

