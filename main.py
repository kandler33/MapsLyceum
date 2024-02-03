from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QSizePolicy
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from PyQt5 import uic
import requests
import sys


class LongitudeError(ValueError):
    def __init__(self, longitude):
        self.longitude = longitude
        super().__init__(f'longitude value must be between -180 and 180. got: {self.longitude}')


class LatitudeError(ValueError):
    def __init__(self, latitude):
        self.latitude = latitude
        super().__init__(f'latitude value must be between -90 and 90. got: {self.latitude}')


class ScaleError(ValueError):
    def __init__(self, scale):
        self.scale = scale
        super().__init__(f'scale value must be between 0 and 21. got: {self.scale}')


class LayoutError(ValueError):
    def __init__(self, layout):
        self.layout = layout
        super().__init__(f'layout must be in ("map", "sat"). got: {self.layout}')


class GeocoderApi:
    pass


class StaticApi:
    def __init__(self):
        self.server = 'https://static-maps.yandex.ru/1.x'

    def get(self, longitude: float, latitude: float, scale: int,
            size: tuple[int, int] = (450, 450), layout: str = 'map') -> QPixmap:

        if longitude < -180 or longitude > 180:
            raise LongitudeError(longitude)

        if latitude < -90 or latitude > 90:
            raise LatitudeError(latitude)

        if scale < 0 or scale > 21:
            raise ScaleError(scale)

        if layout not in ('map', 'sat'):
            raise LayoutError(layout)

        ll = ','.join(str(i) for i in (longitude, latitude))
        size = ','.join(str(i) for i in size)

        params = {
            'll': ll,
            'z': scale,
            'size': size,
            'l': layout
        }
        response = requests.get(self.server, params=params)
        if not response:
            print('qw', response.url)
            raise Exception

        pixmap = QPixmap()
        pixmap.loadFromData(response.content)
        return pixmap


class Map(QLabel):
    def __init__(self, longitude, latitude, scale):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.static_api = StaticApi()
        self.longitude = longitude
        self.latitude = latitude
        self.scale = scale
        self.load_pixmap()

    @property
    def longitude(self):
        return self._longitude

    @longitude.setter
    def longitude(self, longitude: float):
        if longitude < -180 or longitude > 180:
            raise LongitudeError(longitude)

        self._longitude = longitude

    @property
    def latitude(self):
        return self._latitude

    @latitude.setter
    def latitude(self, latitude: float):
        if latitude < -90 or latitude > 90:
            raise LatitudeError(latitude)

        self._latitude = latitude

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, scale: int):
        if scale < 0 or scale > 21:
            raise ScaleError(scale)

        self._scale = scale

    @property
    def tile_length(self):
        return 720 / 2 ** self.scale

    @property
    def tile_height(self):
        return 360 / 2 ** self.scale

    def load_pixmap(self):
        pixmap = self.static_api.get(
                longitude=self.longitude,
                latitude=self.latitude,
                scale=self.scale,
                size=(650, 450)
            )
        self.setPixmap(pixmap)

    def move(self, longitude_coef: float = 0, latitude_coef: float = 0):
        longitude_coef *= 450/350
        latitude_coef *= 450/350
        self.longitude += self.tile_length * longitude_coef
        self.latitude += self.tile_height * latitude_coef
        self.load_pixmap()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.setWindowTitle('MapsApi')
        self.IndexCheckBox.hide()
        self.label.setText('Формат запроса: [долгота] [широта] [масштаб карты]')
        self.map = Map(28.97709, 41.005233, 12)
        self.setFocus()
        self.mainLayout.addWidget(self.map)
        self.SearchButton.clicked.connect(self.search_button_handler)

    def keyPressEvent(self, event):
        try:
            if event.key() == Qt.Key_PageUp:
                self.map.scale += 1
                self.map.load_pixmap()

            elif event.key() == Qt.Key_PageDown:
                self.map.scale -= 1
                self.map.load_pixmap()

            elif event.key() == Qt.Key_Up:
                self.map.move(latitude_coef=0.5)

            elif event.key() == Qt.Key_Down:
                self.map.move(latitude_coef=-0.5)

            elif event.key() == Qt.Key_Right:
                self.map.move(longitude_coef=0.5)

            elif event.key() == Qt.Key_Left:
                self.map.move(longitude_coef=-0.5)

        except ValueError as err:
            self.statusBar().showMessage(str(err))

    def mousePressEvent(self, event):
        if self.collide(self.SearchLineEdit, (event.pos().x(), event.pos().y())):
            self.SearchLineEdit.setFocus()
        else:
            self.setFocus()

    def search_button_handler(self):
        request = self.SearchLineEdit.text().split()
        try:
            lon, lat, scale = float(request[0]), float(request[1]), int(request[2])
            self.map.longitude = lon
            self.map.latitude = lat
            self.map.scale = scale
            self.map.load_pixmap()

        except ValueError as err:
            self.statusBar().showMessage(str(err))

    @staticmethod
    def collide(obj, pos):
        return obj.x() <= pos[0] <= obj.x() + obj.width() and obj.y() <= pos[1] <= obj.y() + obj.height()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())
