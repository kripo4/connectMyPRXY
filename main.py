import sys
import json
import re
from PyQt5 import QtWidgets, QtCore, QtGui
import subprocess

class ProxyCard(QtWidgets.QWidget):
    removed = QtCore.pyqtSignal(object)

    def __init__(self, proxy):
        super().__init__()
        self.proxy = proxy
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        self.label = QtWidgets.QLabel(f"{self.proxy['address']}:{self.proxy['port']}")
        
        self.connect_btn = QtWidgets.QPushButton("Подключить")
        self.connect_btn.clicked.connect(self.connect_proxy)
        
        self.remove_btn = QtWidgets.QPushButton("Удалить")
        self.remove_btn.clicked.connect(self.remove_self)

        layout.addWidget(self.label)
        layout.addWidget(self.connect_btn)
        layout.addWidget(self.remove_btn)
        
        self.animation = QtCore.QPropertyAnimation(self, b"geometry")

    def remove_self(self):
        self.removed.emit(self)
        self.animation.setEndValue(QtCore.QRect(self.pos(), QtCore.QSize(0,0)))
        self.animation.start()
        QtCore.QTimer.singleShot(300, self.close)

    def connect_proxy(self):
        try:
            set_system_proxy(self.proxy['address'], self.proxy['port'])
            QtWidgets.QMessageBox.information(self, "Успех", "Прокси подключено")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось подключить прокси: {str(e)}")

class ProxyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Proxy Manager")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet(open("style.qss").read())
        
        self.proxies = []
        self.load_proxies()
        
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        self.add_btn = QtWidgets.QPushButton("Добавить прокси")
        self.add_btn.clicked.connect(self.add_proxy)
        layout.addWidget(self.add_btn)
        
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)
        
        self.load_cards()
        
    def load_cards(self):
        for proxy in self.proxies:
            card = ProxyCard(proxy)
            card.removed.connect(self.remove_proxy)
            self.scroll_layout.addWidget(card)
            self.animate_card(card)
            
    def animate_card(self, card):
        card.setGeometry(-card.width(), 0, card.width(), card.height())
        anim = QtCore.QPropertyAnimation(card, b"pos")
        anim.setDuration(300)
        anim.setStartValue(QtCore.QPoint(-card.width(), 0))
        anim.setEndValue(QtCore.QPoint(0, 0))
        anim.start()
        
    def add_proxy(self):
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Добавить прокси")
        form = QtWidgets.QFormLayout()
        
        address = QtWidgets.QLineEdit()
        port = QtWidgets.QLineEdit()
        
        form.addRow("Адрес:", address)
        form.addRow("Порт:", port)
        dialog.setLayout(form)
        
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, dialog
        )
        form.addRow(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        if dialog.exec_():
            if self.validate_proxy(address.text(), port.text()):
                new_proxy = {
                    "address": address.text(),
                    "port": port.text()
                }
                self.proxies.append(new_proxy)
                self.save_proxies()
                card = ProxyCard(new_proxy)
                card.removed.connect(self.remove_proxy)
                self.scroll_layout.addWidget(card)
                self.animate_card(card)
            else:
                QtWidgets.QMessageBox.warning(dialog, "Ошибка", "Неверный формат прокси")
                
    def validate_proxy(self, address, port):
        # Проверка адреса
        if not re.match(r'^([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|(\d{1,3}\.){3}\d{1,3})$', address):
            return False
        
        # Проверка порта
        try:
            port = int(port)
            if not 1 <= port <= 65535:
                return False
        except:
            return False
            
        return True

    def remove_proxy(self, card):
        index = self.scroll_layout.indexOf(card)
        if index != -1:
            self.scroll_layout.removeWidget(card)
            del self.proxies[index]
            self.save_proxies()
            card.deleteLater()
            
    def load_proxies(self):
        try:
            with open("proxies.json", "r") as f:
                self.proxies = json.load(f)
        except:
            self.proxies = []
            
    def save_proxies(self):
        with open("proxies.json", "w") as f:
            json.dump(self.proxies, f, indent=4)

def set_system_proxy(address, port):
    # Для Fedora с NetworkManager
    subprocess.run([
        'sudo', 'nmcli', 'connection', 'modify', 
        'your-connection-name', 
        f'proxy.http={address}:{port}',
        f'proxy.https={address}:{port}',
        'proxy.ignore-on-dsl=yes',
        'proxy.ignore-on-wireless=yes'
    ])
    subprocess.run(['sudo', 'nmcli', 'connection', 'up', 'your-connection-name'])

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ProxyApp()
    window.show()
    sys.exit(app.exec_())
