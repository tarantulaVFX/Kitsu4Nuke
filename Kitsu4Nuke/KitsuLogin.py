# --------------------------Kitsu4Nuke--------------------------------
# PySide2 QDialog for Nuke for logging into a kitsu account
#
# (c) 2021 Tarantula
# Author: Moses Molina
# email:  moses.tarantula@gmail.com
# --------------------------------------------------------------------

from PySide2.QtWidgets import *
from KitsuUtil import KitsuSession, setConfig, getConfig, empty_conf

import threading
import os
import nuke


class KitsuLogin(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle("Login to Kitsu")
        self.setMinimumSize(250, 175)
        layout = self.layout = QVBoxLayout()

        self.url = QLineEdit()
        self.url.setPlaceholderText('kitsu server address')
        self.username = QLineEdit()
        self.username.setPlaceholderText('email')
        self.password = QLineEdit()
        self.password.setPlaceholderText('password')
        self.password.setEchoMode(QLineEdit.Password)

        self.status = QHBoxLayout()
        self.statusL = QLabel()
        self.status.addWidget(self.statusL)
        self.status.addStretch()

        self.loginBtn = QPushButton('login')
        self.loginBtn.clicked.connect(self.Login)
        self.logoutBtn = QPushButton('log out')
        self.logoutBtn.clicked.connect(self.Logout)
        self.logoutBtn.hide()

        self.buttonBox = QHBoxLayout()
        self.buttonBox.addStretch()
        self.buttonBox.addWidget(self.loginBtn)
        self.buttonBox.addWidget(self.logoutBtn)
        self.buttonBox.addStretch()

        # Setup Layouts
        layout.addWidget(self.url)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addLayout(self.status)
        layout.addStretch()
        layout.addLayout(self.buttonBox)
        self.setLayout(layout)

        self.curr_conf = getConfig()
        if self.curr_conf:
            self.url.setText(str(self.curr_conf['kitsu_url']))
            self.username.setText(str(self.curr_conf['kitsu_email']))
            self.password.setText(str(self.curr_conf['kitsu_password']))
            self.setUIEnabled(False)
            threading.Thread(target=self.threadedAuthenticate, args=(self.curr_conf,)).start()

    def success(self, new_conf):
        config = getConfig()
        if config:
            config.update(new_conf)
            setConfig(config)
        else:
            setConfig(new_conf)

        self.loginBtn.hide()
        self.logoutBtn.show()

    def setStatusL(self, txt):
        self.statusL.setText(txt)

    def threadedAuthenticate(self, config):
        if config['kitsu_url'] != '':
            client = KitsuSession(config)
            if client.tokens is None:
                msg = '<b><font color=\"#cc0000\">' + str(client.status) + '</font></b>'
                nuke.executeInMainThread(self.setStatusL, args=(msg,))
                nuke.executeInMainThread(self.setUIEnabled, args=(True,))
            else:
                msg = "<b><font color=\"#00cc44\">success!</font></b>"
                nuke.executeInMainThread(self.setStatusL, args=(msg,))
                nuke.executeInMainThread(self.setUIEnabled, args=(False,))
                # print('We got our tokens: ' + str(client.tokens))
                nuke.executeInMainThread(self.success, args=(config,))
        else:
            nuke.executeInMainThread(self.setUIEnabled, args=(True,))

    def setUIEnabled(self, b):
        self.username.setEnabled(b)
        self.password.setEnabled(b)
        self.url.setEnabled(b)
        self.loginBtn.setEnabled(b)

    def Login(self):
        config = {'kitsu_email': self.username.text(),
                  'kitsu_password': self.password.text(),
                  "kitsu_url": self.url.text()}
        self.setUIEnabled(False)
        threading.Thread(target=self.threadedAuthenticate, args=(config,)).start()

    def Logout(self):
        config = getConfig()
        if config:
            config.update(empty_conf)
            setConfig(config)
        else:
            setConfig(empty_conf)
        self.logoutBtn.hide()
        self.loginBtn.show()
        self.setUIEnabled(True)
        msg = ''
        self.setStatusL(msg)
