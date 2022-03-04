#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import PyQt5
from PyQt5 import QtGui, QtWidgets, QtCore
from .TSHScoreboardWidget import *
from .Workers import *
from .PlayerColumn import *
from .TSHPlayerDB import TSHPlayerDB
from .TSHAlertNotification import TSHAlertNotification
from .TournamentDataProvider.SmashGGDataProvider import SmashGGDataProvider
from .TSHTournamentDataProvider import TSHTournamentDataProvider
from .TSHTournamentInfoWidget import TSHTournamentInfoWidget
from .TSHGameAssetManager import TSHGameAssetManager
from .TSHCommentaryWidget import TSHCommentaryWidget
from qdarkstyle import palette
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import shutil
import tarfile
import py7zr

import qdarkstyle

import requests
import urllib
import json
import traceback
import sys
import time
import os
import threading
import re

import csv

import copy

from collections import Counter

import unicodedata

App = QApplication(sys.argv)


#sys.stderr = open('./log_error.txt', 'w')


def remove_accents_lower(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()


class WindowSignals(QObject):
    StopTimer = pyqtSignal()
    ExportStageStrike = pyqtSignal(object)
    DetectGame = pyqtSignal(int)
    SetupAutocomplete = pyqtSignal()
    UiMounted = pyqtSignal()


class Window(QMainWindow):
    signals = WindowSignals()

    def __init__(self):
        super().__init__()

        self.signals = WindowSignals()

        splash = QSplashScreen(self, QPixmap(
            'icons/icon.png').scaled(128, 128))
        splash.show()

        time.sleep(0.1)

        App.processEvents()

        self.programState = {}
        self.savedProgramState = {}
        self.programStateDiff = {}

        self.setWindowIcon(QIcon('icons/icon.png'))

        if not os.path.exists("out/"):
            os.mkdir("out/")

        if not os.path.exists("./assets/games"):
            os.makedirs("./assets/games")

        try:
            f = open('settings.json', encoding='utf-8')
            self.settings = json.load(f)
            print("Settings loaded")
        except Exception as e:
            self.settings = {}
            self.SaveSettings()
            print("Settings created")

        self.font_small = QFont(
            "./assets/font/RobotoCondensed.ttf", pointSize=8)

        self.threadpool = QThreadPool()
        self.saveMutex = QMutex()

        self.player_layouts = []

        self.allplayers = None
        self.local_players = None

        try:
            version = json.load(
                open('versions.json', encoding='utf-8')).get("program", "?")
        except Exception as e:
            version = "?"

        self.setGeometry(300, 300, 800, 100)
        self.setWindowTitle("TournamentStreamHelper v"+version)

        self.setDockOptions(
            QMainWindow.DockOption.ForceTabbedDocks)

        self.setTabPosition(
            Qt.DockWidgetArea.AllDockWidgetAreas, QTabWidget.TabPosition.North)

        # Layout base com status no topo
        central_widget = QWidget()
        pre_base_layout = QVBoxLayout()
        central_widget.setLayout(pre_base_layout)
        self.setCentralWidget(central_widget)
        central_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        tournamentInfo = TSHTournamentInfoWidget()
        tournamentInfo.setObjectName("Tournament Info")
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, tournamentInfo)

        self.scoreboard = TSHScoreboardWidget()
        self.scoreboard.setObjectName("Scoreboard")
        self.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, self.scoreboard)

        commentary = TSHCommentaryWidget()
        commentary.setObjectName("Commentary")
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, commentary)

        self.tabifyDockWidget(self.scoreboard, commentary)
        self.tabifyDockWidget(self.scoreboard, tournamentInfo)
        self.scoreboard.raise_()

        # pre_base_layout.setSpacing(0)
        # pre_base_layout.setContentsMargins(QMargins(0, 0, 0, 0))

        # Game
        base_layout = QHBoxLayout()

        group_box = QWidget()
        group_box.setLayout(QVBoxLayout())
        group_box.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Maximum)
        base_layout.layout().addWidget(group_box)

        self.setTournamentBt = QPushButton("Set tournament")
        group_box.layout().addWidget(self.setTournamentBt)
        self.setTournamentBt.clicked.connect(
            lambda bt, s=self: TSHTournamentDataProvider.instance.SetSmashggEventSlug(s))

        # Follow smashgg user
        hbox = QHBoxLayout()
        group_box.layout().addLayout(hbox)

        self.btLoadPlayerSet = QPushButton("Load SmashGG user set")
        self.btLoadPlayerSet.setIcon(QIcon("./icons/smashgg.svg"))
        self.btLoadPlayerSet.setEnabled(False)
        self.btLoadPlayerSet.clicked.connect(self.LoadUserSetClicked)
        hbox.addWidget(self.btLoadPlayerSet)
        TSHTournamentDataProvider.instance.signals.user_updated.connect(
            self.UpdateUserSetButton)
        TSHTournamentDataProvider.instance.signals.tournament_changed.connect(
            self.UpdateUserSetButton)

        TSHTournamentDataProvider.instance.signals.tournament_changed.connect(
            self.UpdateUserSetButton)

        self.btLoadPlayerSetOptions = QPushButton()
        self.btLoadPlayerSetOptions.setSizePolicy(
            QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.btLoadPlayerSetOptions.setIcon(QIcon("./icons/settings.svg"))
        self.btLoadPlayerSetOptions.clicked.connect(
            self.LoadUserSetOptionsClicked)
        hbox.addWidget(self.btLoadPlayerSetOptions)

        # Settings
        self.optionsBt = QToolButton()
        self.optionsBt.setIcon(QIcon('icons/menu.svg'))
        self.optionsBt.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.optionsBt.setPopupMode(QToolButton.InstantPopup)
        base_layout.addWidget(self.optionsBt)
        self.optionsBt.setSizePolicy(
            QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.optionsBt.setFixedSize(QSize(32, 32))
        self.optionsBt.setIconSize(QSize(32, 32))
        self.optionsBt.setMenu(QMenu())
        action = self.optionsBt.menu().addAction("Always on top")
        action.setCheckable(True)
        action.toggled.connect(self.ToggleAlwaysOnTop)
        action = self.optionsBt.menu().addAction("Check for updates")
        self.updateAction = action
        action.setIcon(QIcon('icons/undo.svg'))
        action.triggered.connect(self.CheckForUpdates)
        action = self.optionsBt.menu().addAction("Download assets")
        action.setIcon(QIcon('icons/download.svg'))
        action.triggered.connect(self.DownloadAssets)

        self.gameSelect = QComboBox()
        self.gameSelect.setEditable(True)
        self.gameSelect.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self.gameSelect.completer().setCompletionMode(QCompleter.PopupCompletion)
        proxyModel = QSortFilterProxyModel()
        proxyModel.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        proxyModel.setSourceModel(self.gameSelect.model())
        self.gameSelect.model().setParent(proxyModel)
        self.gameSelect.setModel(proxyModel)
        self.gameSelect.setFont(self.font_small)
        self.gameSelect.activated.connect(
            lambda x: TSHGameAssetManager.instance.LoadGameAssets(self.gameSelect.currentData()))
        TSHGameAssetManager.instance.signals.onLoad.connect(
            self.SetGame)
        TSHGameAssetManager.instance.signals.onLoadAssets.connect(
            self.ReloadGames)
        TSHTournamentDataProvider.instance.signals.tournament_changed.connect(
            self.SetGame)

        pre_base_layout.addLayout(base_layout)
        group_box.layout().addWidget(self.gameSelect)

        self.CheckForUpdates(True)
        self.ReloadGames()

        self.qtSettings = QSettings("joao_shino", "TournamentStreamHelper")

        if self.qtSettings.value("geometry"):
            self.restoreGeometry(self.qtSettings.value("geometry"))

        if self.qtSettings.value("windowState"):
            self.restoreState(self.qtSettings.value("windowState"))

        splash.finish(self)
        self.show()

        TSHTournamentDataProvider.instance.UiMounted()
        TSHGameAssetManager.instance.UiMounted()
        TSHAlertNotification.instance.UiMounted()
        TSHPlayerDB.LoadDB()

    def SetGame(self):
        index = next((i for i in range(self.gameSelect.model().rowCount()) if self.gameSelect.itemText(i) == TSHGameAssetManager.instance.selectedGame.get(
            "name") or self.gameSelect.itemText(i) == TSHGameAssetManager.instance.selectedGame.get("codename")), None)
        if index is not None:
            self.gameSelect.setCurrentIndex(index)

    def UpdateUserSetButton(self):
        if SettingsManager.Get("SmashGG_user"):
            self.btLoadPlayerSet.setText(
                f"Load tournament and sets from SmashGG user ({SettingsManager.Get('SmashGG_user')})")
            self.btLoadPlayerSet.setEnabled(True)
        else:
            self.btLoadPlayerSet.setText(
                "Load tournament and sets from SmashGG user")
            self.btLoadPlayerSet.setEnabled(False)

    def LoadUserSetClicked(self):
        self.scoreboard.lastSetSelected = None
        if SettingsManager.Get("SmashGG_user"):
            TSHTournamentDataProvider.instance.provider = SmashGGDataProvider(
                "smash.gg/",
                TSHTournamentDataProvider.instance.threadPool,
                TSHTournamentDataProvider.instance
            )
            TSHTournamentDataProvider.instance.LoadUserSet(
                self.scoreboard, SettingsManager.Get("SmashGG_user"))

    def LoadUserSetOptionsClicked(self):
        TSHTournamentDataProvider.instance.SetUserAccount(
            self.scoreboard, smashgg=True)

    def closeEvent(self, event):
        self.qtSettings.setValue("geometry", self.saveGeometry())
        self.qtSettings.setValue("windowState", self.saveState())

    def ReloadGames(self):
        print("Reload games")
        self.gameSelect.setModel(QStandardItemModel())
        self.gameSelect.addItem("", 0)
        for i, game in enumerate(TSHGameAssetManager.instance.games.items()):
            if game[1].get("name"):
                self.gameSelect.addItem(game[1].get("name"), i+1)
            else:
                self.gameSelect.addItem(game[0], i+1)
        self.gameSelect.model().sort(0)
        self.SetGame()

    def DetectGameFromId(self, id):
        game = next(
            (i+1 for i, game in enumerate(self.games)
             if str(self.games[game].get("smashgg_game_id", "")) == str(id)),
            None
        )

        if game is not None and self.gameSelect.currentIndex() != game:
            self.gameSelect.setCurrentIndex(game)
            self.LoadGameAssets(game)

    def CheckForUpdates(self, silent=False):
        release = None
        versions = None

        try:
            response = requests.get(
                "https://api.github.com/repos/joaorb64/TournamentStreamHelper/releases/latest")
            release = json.loads(response.text)
        except Exception as e:
            if silent == False:
                messagebox = QMessageBox()
                messagebox.setText(
                    "Failed to fetch version from github:\n"+str(e))
                messagebox.exec()

        try:
            versions = json.load(open('versions.json', encoding='utf-8'))
        except Exception as e:
            print("Local version file not found")

        if versions and release:
            myVersion = versions.get("program", "0.0")
            currVersion = release.get("tag_name", "0.0")

            if silent == False:
                if myVersion < currVersion:
                    buttonReply = QDialog(self)
                    buttonReply.setWindowTitle("Updater")
                    buttonReply.setWindowModality(Qt.WindowModal)
                    vbox = QVBoxLayout()
                    buttonReply.setLayout(vbox)

                    buttonReply.layout().addWidget(
                        QLabel("New update available: "+myVersion+" → "+currVersion))
                    buttonReply.layout().addWidget(QLabel(release["body"]))
                    buttonReply.layout().addWidget(QLabel(
                        "Update to latest version?\nNOTE: WILL BACKUP /layout/ AND OVERWRITE ALL OTHER DATA"))

                    hbox = QHBoxLayout()
                    vbox.addLayout(hbox)

                    btUpdate = QPushButton("Update")
                    hbox.addWidget(btUpdate)
                    btCancel = QPushButton("Cancel")
                    hbox.addWidget(btCancel)

                    buttonReply.show()

                    def Update():
                        self.downloadDialogue = QProgressDialog(
                            "Downloading update... ", "Cancel", 0, 0, self)
                        self.downloadDialogue.setWindowModality(
                            Qt.WindowModality.WindowModal)
                        self.downloadDialogue.show()

                        def worker(progress_callback):
                            with open("update.tar.gz", 'wb') as downloadFile:
                                downloaded = 0

                                response = urllib.request.urlopen(
                                    release["tarball_url"])

                                while(True):
                                    chunk = response.read(1024*1024)

                                    if not chunk:
                                        break

                                    downloaded += len(chunk)
                                    downloadFile.write(chunk)

                                    if self.downloadDialogue.wasCanceled():
                                        return

                                    progress_callback.emit(int(downloaded))
                                downloadFile.close()

                        def progress(downloaded):
                            self.downloadDialogue.setLabelText(
                                "Downloading update... "+str(downloaded/1024/1024)+" MB")

                        def finished():
                            self.downloadDialogue.close()
                            tar = tarfile.open("update.tar.gz")
                            print(tar.getmembers())
                            os.rename(
                                "./layout", f"./layout_backup_{str(time.time())}")
                            os.rename(
                                "./tournament_phases.txt", f"./tournament_phases_backup_{str(time.time())}.txt")
                            for m in tar.getmembers():
                                if "/" in m.name:
                                    m.name = m.name.split("/", 1)[1]
                                    tar.extract(m)
                            tar.close()
                            os.remove("update.tar.gz")

                            with open('versions.json', 'w') as outfile:
                                versions["program"] = currVersion
                                json.dump(versions, outfile)

                            messagebox = QMessageBox()
                            messagebox.setText(
                                "Update complete. The program will now close.")
                            messagebox.finished.connect(QApplication.exit)
                            messagebox.exec()

                        worker = Worker(worker)
                        worker.signals.progress.connect(progress)
                        worker.signals.finished.connect(finished)
                        self.threadpool.start(worker)

                    btUpdate.clicked.connect(Update)
                    btCancel.clicked.connect(lambda: buttonReply.close())
                else:
                    messagebox = QMessageBox()
                    messagebox.setText(
                        "You're already using the latest version")
                    messagebox.exec()
            else:
                if myVersion < currVersion:
                    baseIcon = QPixmap(QImage("icons/menu.svg").scaled(32, 32))
                    updateIcon = QImage(
                        "./icons/update_circle.svg").scaled(12, 12)
                    p = QPainter(baseIcon)
                    p.drawImage(QPoint(20, 0), updateIcon)
                    p.end()
                    self.optionsBt.setIcon(QIcon(baseIcon))
                    self.updateAction.setText(
                        "Check for updates [Update available!]")

    def DownloadAssets(self):
        assets = self.DownloadAssetsFetch()

        if assets is None:
            return

        self.preDownloadDialogue = QDialog(self)
        self.preDownloadDialogue.setWindowTitle("Download assets")
        self.preDownloadDialogue.setWindowModality(Qt.WindowModal)
        self.preDownloadDialogue.setLayout(QVBoxLayout())
        self.preDownloadDialogue.show()

        select = QComboBox()
        selectProxy = QSortFilterProxyModel()
        selectProxy.setSourceModel(select.model())
        select.model().setParent(selectProxy)
        selectProxy.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        select.setModel(selectProxy)
        select.setEditable(True)
        select.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        select.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.preDownloadDialogue.layout().addWidget(select)

        model = QStandardItemModel()

        proxyModel = QSortFilterProxyModel()
        proxyModel.setSourceModel(model)
        proxyModel.setFilterKeyColumn(-1)
        proxyModel.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        def filterList(text):
            proxyModel.setFilterFixedString(text)

        searchBar = QLineEdit()
        searchBar.setPlaceholderText("Filter...")
        self.preDownloadDialogue.layout().addWidget(searchBar)
        searchBar.textEdited.connect(filterList)

        downloadList = QTableView()
        self.preDownloadDialogue.layout().addWidget(downloadList)
        downloadList.setSortingEnabled(True)
        downloadList.setSelectionBehavior(QAbstractItemView.SelectRows)
        downloadList.setEditTriggers(QAbstractItemView.NoEditTriggers)
        downloadList.setModel(proxyModel)
        downloadList.verticalHeader().hide()
        self.preDownloadDialogue.resize(1200, 500)
        downloadList.horizontalHeader().setStretchLastSection(True)
        downloadList.setWordWrap(True)
        downloadList.resizeColumnsToContents()
        downloadList.resizeRowsToContents()

        for i, game in enumerate(assets):
            select.addItem(assets[game]["name"], i)

        select.model().sort(0)

        def ReloadGameAssets(index=None):
            nonlocal self

            index = select.currentData()

            if index == None:
                index = select.currentIndex()

            model.clear()
            model.setHorizontalHeaderLabels([
                "game", "asset_id", "Name", "Description", "Credits", "Installed version", "Latest version", "Size"
            ])
            downloadList.hideColumn(0)
            downloadList.hideColumn(1)
            downloadList.horizontalHeader().setStretchLastSection(True)
            downloadList.setWordWrap(True)
            downloadList.resizeColumnsToContents()
            downloadList.resizeRowsToContents()

            key = list(assets.keys())[index]

            for asset in assets[key]["assets"]:
                dlSize = "{:.2f}".format(sum(
                    [f.get("size", 0) for f in list(
                        assets[key]["assets"][asset]["files"].values())]
                )/1024/1024) + " MB"

                currVersion = str(TSHGameAssetManager.instance.games.get(key, {}).get(
                    "assets", {}).get(asset, {}).get("version"))
                print(currVersion)
                version = str(assets[key]["assets"][asset].get("version"))

                if currVersion != version:
                    version += " [!]"

                model.appendRow([
                    QStandardItem(key),
                    QStandardItem(asset),
                    QStandardItem(assets[key]["assets"][asset].get("name")),
                    QStandardItem(assets[key]["assets"]
                                  [asset].get("description")),
                    QStandardItem(assets[key]["assets"][asset].get("credits")),
                    QStandardItem(currVersion),
                    QStandardItem(version),
                    QStandardItem(dlSize)
                ])

            downloadList.horizontalHeader().setStretchLastSection(True)
            downloadList.resizeColumnsToContents()
            downloadList.resizeRowsToContents()

        self.reloadDownloadsList = ReloadGameAssets
        select.activated.connect(ReloadGameAssets)
        ReloadGameAssets(0)

        btOk = QPushButton("Download")
        self.preDownloadDialogue.layout().addWidget(btOk)

        def DownloadStart():
            nonlocal self
            row = downloadList.selectionModel().selectedRows()[0].row()
            game = downloadList.model().index(row, 0).data()
            key = downloadList.model().index(row, 1).data()

            filesToDownload = assets[game]["assets"][key]["files"]

            for f in filesToDownload:
                filesToDownload[f]["path"] = \
                    "https://github.com/joaorb64/StreamHelperAssets/releases/latest/download/" + \
                    filesToDownload[f]["name"]
                filesToDownload[f]["extractpath"] = "./assets/games/"+game

            self.downloadDialogue = QProgressDialog(
                "Downloading assets", "Cancel", 0, 100, self)
            self.downloadDialogue.setMinimumWidth(500)
            self.downloadDialogue.setWindowModality(
                Qt.WindowModality.WindowModal)
            self.downloadDialogue.show()
            worker = Worker(self.DownloadAssetsWorker, *
                            [list(filesToDownload.values())])
            worker.signals.progress.connect(self.DownloadAssetsProgress)
            worker.signals.finished.connect(self.DownloadAssetsFinished)
            self.threadpool.start(worker)

        btOk.clicked.connect(DownloadStart)

    def DownloadAssetsFetch(self):
        assets = None
        try:
            response = requests.get(
                "https://raw.githubusercontent.com/joaorb64/StreamHelperAssets/main/assets.json")
            assets = json.loads(response.text)
        except Exception as e:
            messagebox = QMessageBox()
            messagebox.setText("Failed to fetch github:\n"+str(e))
            messagebox.exec()
        return assets

    def DownloadAssetsWorker(self, files, progress_callback):
        totalSize = sum(f["size"] for f in files)
        downloaded = 0

        for f in files:
            with open("assets/games/"+f["name"], 'wb') as downloadFile:
                print("Downloading "+f["name"])
                progress_callback.emit("Downloading "+f["name"]+"...")

                response = urllib.request.urlopen(f["path"])

                while(True):
                    chunk = response.read(1024*1024)

                    if not chunk:
                        break

                    downloaded += len(chunk)
                    downloadFile.write(chunk)

                    if self.downloadDialogue.wasCanceled():
                        return

                    progress_callback.emit(int(downloaded/totalSize*100))
                downloadFile.close()

                print("OK")

        progress_callback.emit(100)

        filenames = ["./assets/games/"+f["name"] for f in files]
        mergedFile = "./assets/games/"+files[0]["name"].split(".")[0]+'.7z'

        is7z = next((f for f in files if ".7z" in f["name"]), None)

        if is7z:
            with open(mergedFile, 'ab') as outfile:
                for fname in filenames:
                    with open(fname, 'rb') as infile:
                        outfile.write(infile.read())

            print("Extracting "+mergedFile)
            progress_callback.emit("Extracting "+mergedFile)

            with py7zr.SevenZipFile(mergedFile, 'r') as parent_zip:
                parent_zip.extractall(files[0]["extractpath"])

            for f in files:
                os.remove("./assets/games/"+f["name"])

            os.remove(mergedFile)
        else:
            for f in files:
                if os.path.isfile(f["extractpath"]+"/"+f["name"]):
                    os.remove(f["extractpath"]+"/"+f["name"])
                shutil.move("./assets/games/"+f["name"], f["extractpath"])

        print("OK")

    def DownloadAssetsProgress(self, n):
        if type(n) == int:
            self.downloadDialogue.setValue(n)

            if n == 100:
                self.downloadDialogue.setMaximum(0)
                self.downloadDialogue.setValue(0)
        else:
            self.downloadDialogue.setLabelText(n)

    def DownloadAssetsFinished(self):
        TSHGameAssetManager.instance.LoadGames()
        self.downloadDialogue.close()
        self.reloadDownloadsList()

    def ToggleAlwaysOnTop(self, checked):
        if checked:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        else:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.show()

    def SaveSettings(self):
        with open('settings.json', 'w', encoding='utf-8') as outfile:
            json.dump(self.settings, outfile, indent=4, sort_keys=True)


App.setStyleSheet(qdarkstyle.load_stylesheet(
    palette=qdarkstyle.DarkPalette))

# App.setStyleSheet(qdarkstyle.load_stylesheet(
#     palette=qdarkstyle.LightPalette))

window = Window()
sys.exit(App.exec_())
