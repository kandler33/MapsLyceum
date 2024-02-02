from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QPixmap
from PyQt5 import uic
import requests
import sys


class GeocoderApi:
    pass


class StaticApi:
    def __init__(self):
        self.server = 'https://static-maps.yandex.ru/1.x'

    def get(self, longitude: float, latitude: float, scale: int,
            size: tuple[int, int] = (450, 450), layout: str = 'map') -> QPixmap:

        if longitude < -180 or longitude > 180:
            raise ValueError(f'longitude value must be between -180 and 180. got: {longitude}')

        if latitude < -90 or latitude > 90:
            raise ValueError(f'latitude value must be between -90 and 90. got: {latitude}')

        if scale < 0 or scale > 21:
            raise ValueError(f'scale value must be between 0 and 21. got: {scale}')

        if layout not in ('map', 'sat'):
            raise ValueError(f'layout must be in ("map", "sat"). got: {layout}')

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)
        self.setWindowTitle('MapsApi')
        self.IndexCheckBox.hide()
        self.label.setText('Формат запроса: [долгота] [широта] [масштаб карты]')
        self.static_api = StaticApi()
        pixmap = self.static_api.get(
            longitude=28.97709,
            latitude=41.005233,
            scale=12,
            layout='map'
        )
        self.MapLabel.setPixmap(pixmap)
        self.SearchButton.clicked.connect(self.search_button_handler)

    def search_button_handler(self):
        request = self.SearchLineEdit.text().split()
        try:
            lon, lat, scale = float(request[0]), float(request[1]), int(request[2])
            pixmap = self.static_api.get(
                longitude=lon,
                latitude=lat,
                scale=scale,
                layout='map'
            )
            self.MapLabel.setPixmap(pixmap)

        except ValueError as err:
            self.statusBar().showMessage(str(err))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())
