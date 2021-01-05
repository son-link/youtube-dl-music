from __future__ import unicode_literals
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QTableWidgetItem,
    QHeaderView,
    QInputDialog,
    QLabel
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaPlaylist, QMediaContent
from PyQt5.QtCore import (
    QUrl,
    pyqtSignal,
    QThread,
    QVariant,
    Qt,
    QCoreApplication,
    QTranslator,
    QLocale
)
from PyQt5.QtGui import QIcon
import youtube_dl
from .Ui_gui import Ui_MainWindow
from os import path


_translate = QCoreApplication.translate
LOCAL_DIR = path.dirname(path.realpath(__file__))


def ms_to_time(t):
    '''
    Convert nanoseconds to hours, minutes and seconds
    '''
    s, ns = divmod(t, 1000)
    m, s = divmod(s, 60)

    if m < 60:
        return "0:%02i:%02i" % (m, s)
    else:
        h, m = divmod(m, 60)
        return "%i:%02i:%02i" % (h, m, s)


class addVideos(QThread):
    video = pyqtSignal(QVariant)

    def __init__(self, parent, url):
        super(addVideos, self).__init__(parent)
        self.url = url
        ydl_opts = {
            'format': 'bestaudio',
            'ignoreerrors': True,
            'logger': MyLogger(parent),
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            self.ydl = ydl

    def run(self):
        info = self.ydl.extract_info(self.url, False)
        if '_type' in info:
            for entry in info['entries']:
                if entry:
                    for i in entry['formats']:
                        if i['format_id'] == '251':
                            trackData = {
                                'channel': entry['uploader'],
                                'title': entry['title'],
                                'duration': entry['duration'],
                                'cover': entry['thumbnails'][0]['url'],
                                'url': i['url']
                            }
                            self.video.emit(trackData)
        else:
            for i in info['formats']:
                if i['format_id'] == '251':
                    trackData = {
                        'channel': info['uploader'],
                        'title': info['title'],
                        'duration': info['duration'],
                        'cover': info['thumbnails'][0]['url'],
                        'url': i['url']
                    }
                    self.video.emit(trackData)
        self.video.emit(False)

    def stop(self):
        self.quit()
        self.wait()


class MyLogger(object):
    def __init__(self, parent):
        self.parent = parent

    def debug(self, msg):
        self.parent.statusBar().showMessage(msg)

    def warning(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)


class YtdlMusic(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        QMainWindow.__init__(self, *args, **kwargs)
        self.setupUi(self)
        self.setWindowIcon(QIcon(LOCAL_DIR + '/ytdl_music.svg'))

        self.player = QMediaPlayer()
        self.player.isSeekable()
        self.playList = QMediaPlaylist()
        self.playListData = []
        self.player.setPlaylist(self.playList)
        self.currentPos = 0
        self.currentTrackDuration = '0:00:00'

        self.player.positionChanged.connect(self.positionChanged)
        self.player.durationChanged.connect(self.durationChanged)
        self.playList.currentIndexChanged.connect(self.playlistPosChanged)
        self.playlistTable.itemDoubleClicked.connect(self.changeTrack)
        self.playlistTable.itemSelectionChanged.connect(self.selectedTracks)
        # self.timeSlider.valueChanged.connect(self.setPosition)
        self.addBtn.clicked.connect(self.addDialog)
        self.removeBtn.clicked.connect(self.delTracks)
        self.playBtn.clicked.connect(self.playPause)
        self.stopBtn.clicked.connect(self.stop)
        self.prevBtn.clicked.connect(self.playList.previous)
        self.nextBtn.clicked.connect(self.playList.next)

        self.playlistTable.setHorizontalHeaderLabels(['', _translate('MainWindow', 'Channel'), _translate('MainWindow', 'Title')])
        header = self.playlistTable.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

    def setPosition(self, pos):
        self.player.setPosition(pos)

    def durationChanged(self, duration):
        total_time = '0:00:00'
        duration = self.player.duration()
        total_time = ms_to_time(duration)
        # self.timeSlider.setMaximum(duration)
        self.currentTrackDuration = duration
        # self.totalTimeLabel.setText(total_time)
        self.currentTrackDuration = total_time

    def mediaStatusChanged(self, status):
        icon = QIcon.fromTheme("media-playback-pause")
        if self.player.state() == QMediaPlayer.StoppedState:
            icon = QIcon.fromTheme("media-playback-start")
        elif self.player.state() == QMediaPlayer.PausedState:
            icon = QIcon.fromTheme("media-playback-start")

        self.playBtn.setIcon(icon)

    def positionChanged(self, position, senderType=False):
        self.currentTime = position
        current_time = '0:00:00'

        if position != -1:
            current_time = ms_to_time(position)
            self.timeLabel.setText('{0} / {1}'.format(current_time, self.currentTrackDuration))

        '''self.timeSlider.blockSignals(True)
        self.timeSlider.setValue(position)
        self.timeSlider.blockSignals(False)'''

    def playlistPosChanged(self):
        pos = self.playList.currentIndex()
        data = self.playListData[pos]
        self.setWindowTitle('YouTube-dl Music: ' + data['title'])
        duration = ms_to_time(data['duration'] * 1000)
        self.timeLabel.setText('0:00:00 / {0}'.format(duration))
        # self.totalTimeLabel.setText(ms_to_time(data['duration'] * 1000))
        if self.playList.mediaCount() > 1:
            if pos < self.playList.mediaCount() - 1:
                self.nextBtn.setEnabled(True)
            else:
                self.nextBtn.setEnabled(False)

            if pos > 0:
                self.prevBtn.setEnabled(True)
            else:
                self.prevBtn.setEnabled(False)

            prevPos = 0
            if pos < self.playList.mediaCount():
                if self.currentPos < pos:
                    prevPos = pos - 1
                else:
                    prevPos = pos + 1

                statusItem = QLabel()
                icon = QIcon.fromTheme("media-playback-start")
                statusItem.setPixmap(icon.pixmap(16, 16))
                statusItem.setAlignment(Qt.AlignCenter)
                self.playlistTable.setCellWidget(pos, 0, statusItem)
                if prevPos > -1:
                    self.playlistTable.setCellWidget(prevPos, 0, QLabel())
            else:
                self.playlistTable.setItem(pos, 0, QTableWidgetItem(''))

            self.currentPos = pos

        else:
            statusItem = QLabel()
            icon = QIcon.fromTheme("media-playback-start")
            statusItem.setPixmap(icon.pixmap(16, 16))
            statusItem.setAlignment(Qt.AlignCenter)
            self.playlistTable.setCellWidget(pos, 0, statusItem)

    def playPause(self):
        icon = QIcon.fromTheme("media-playback-pause")

        if self.player.state() == QMediaPlayer.StoppedState:
            if self.player.mediaStatus() == QMediaPlayer.NoMedia:
                if self.playList.mediaCount() != 0:
                    self.player.play()
            elif self.player.mediaStatus() == QMediaPlayer.LoadedMedia:
                self.playList.setCurrentIndex(self.currentPos)
                self.player.play()
            elif self.player.mediaStatus() == QMediaPlayer.BufferedMedia:
                self.player.play()
        elif self.player.state() == QMediaPlayer.PlayingState:
            icon = QIcon.fromTheme("media-playback-start")
            self.player.pause()
        elif self.player.state() == QMediaPlayer.PausedState:
            self.player.play()

        self.playBtn.setIcon(icon)

    def stop(self):
        self.player.stop()
        icon = QIcon.fromTheme("media-playback-start")
        self.playBtn.setIcon(icon)

    def insertTrack(self, data):
        if data:
            self.playListData.append(data)
            totalTracks = self.playList.mediaCount()
            pos = totalTracks
            self.playlistTable.insertRow(totalTracks)
            self.playlistTable.setRowCount(totalTracks+1)
            self.playlistTable.setItem(pos, 0, QTableWidgetItem(''))
            self.playlistTable.setItem(pos, 1, QTableWidgetItem(data['channel']))
            self.playlistTable.setItem(pos, 2, QTableWidgetItem(data['title']))
            media = QMediaContent(QUrl(data['url']))
            self.playList.addMedia(media)
            if totalTracks > 1:
                self.nextBtn.setEnabled(True)
        else:
            self.statusBar().showMessage('Total pistas: {0}'.format(self.playList.mediaCount()))

    def addDialog(self):
        url, ok = QInputDialog.getText(self, _translate('MainWindow', 'Add video/playlist'), 'URL:')
        if ok and url != '':
            self.addPCThread = addVideos(self, url)
            self.addPCThread.video.connect(self.insertTrack)
            self.addPCThread.start()

    def changeTrack(self, item):
        pos = item.row()
        self.playlistTable.setCellWidget(self.currentPos, 0, QLabel())
        self.playList.setCurrentIndex(pos)
        if self.player.state() == QMediaPlayer.StoppedState:
            icon = QIcon.fromTheme("media-playback-pause")
            self.playBtn.setIcon(icon)
            self.player.play()

    def delTracks(self):
        indexes = self.playlistTable.selectionModel().selectedRows()
        del_first = True
        for index in sorted(indexes):
            pos = index.row()
            if not del_first:
                pos -= 1
            else:
                del_first = False

            self.playlistTable.removeRow(pos)
            self.playListData.pop(pos)
            self.playList.removeMedia(pos)

        self.playlistPosChanged()

    def selectedTracks(self):
        totalSelected = len(self.playlistTable.selectedItems())
        if totalSelected > 0:
            self.removeBtn.setEnabled(True)
        else:
            self.removeBtn.setEnabled(False)


def init():
    app = QApplication([])
    defaultLocale = QLocale.system().name()
    if defaultLocale.startswith == 'es':
        defaultLocale = 'es_ES'

    translator = QTranslator()
    translator.load(LOCAL_DIR + "/locales/ytdl-music-" + defaultLocale + ".qm")
    app.installTranslator(translator)
    music = YtdlMusic()
    music.retranslateUi(music)
    music.show()
    app.exec_()
