import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton,
    QListWidget, QFileDialog, QMessageBox, QDialog, QTabWidget, QWidget, QLabel, QLineEdit, QMenu, QListWidgetItem, QHBoxLayout
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QProcess

CONFIG_FILE = "launcher_config.json"

class SettingsDialog(QDialog):
    def __init__(self, item, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.item = item
        self.setWindowTitle("Settings")
        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget(self)
        self.name_tab = QWidget()
        self.image_tab = QWidget()

        self.tabs.addTab(self.name_tab, "Name")
        self.tabs.addTab(self.image_tab, "Image")

        self.name_layout = QVBoxLayout(self.name_tab)
        self.name_label = QLabel("Name:", self.name_tab)
        self.name_edit = QLineEdit(self.name_tab)
        self.name_edit.setText(item.text())
        self.name_layout.addWidget(self.name_label)
        self.name_layout.addWidget(self.name_edit)

        self.image_layout = QVBoxLayout(self.image_tab)
        self.image_label = QLabel("Image:", self.image_tab)
        self.image_path_edit = QLineEdit(self.image_tab)
        self.image_path_edit.setText(item.data(Qt.UserRole + 1))  # Use a different role for the image path
        self.image_browse_button = QPushButton("Browse", self.image_tab)
        self.image_browse_button.clicked.connect(self.browse_image)
        self.image_layout.addWidget(self.image_label)
        self.image_layout.addWidget(self.image_path_edit)
        self.image_layout.addWidget(self.image_browse_button)

        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_settings)
        self.layout.addWidget(self.tabs)
        self.layout.addWidget(self.save_button)

    def browse_image(self):
        image_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.bmp *.ico);;All Files (*)")
        if image_path:
            self.image_path_edit.setText(image_path)

    def save_settings(self):
        self.item.setText(self.name_edit.text())
        self.item.setData(Qt.UserRole, self.item.data(Qt.UserRole))  # Keep the game path
        self.item.setData(Qt.UserRole + 1, self.image_path_edit.text())  # Store the image path
        self.item.setIcon(QIcon(self.image_path_edit.text()))
        self.accept()

class SegaLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sega Launcher")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.list_widget = QListWidget(self)
        self.layout.addWidget(self.list_widget)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)

        # Layout for buttons
        self.button_layout = QHBoxLayout()
        self.layout.addLayout(self.button_layout)

        # Button to add a game
        add_game_button = QPushButton("Add Game", self)
        add_game_button.clicked.connect(self.add_game)
        self.button_layout.addWidget(add_game_button)

        # Button to launch the selected game
        launch_game_button = QPushButton("Launch Game", self)
        launch_game_button.clicked.connect(self.launch_selected_game)
        self.button_layout.addWidget(launch_game_button)

        # Load the config file
        self.load_config()

    def show_context_menu(self, position):
        menu = QMenu()
        settings_action = menu.addAction("Settings")
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.list_widget.viewport().mapToGlobal(position))
        item = self.list_widget.itemAt(position)
        if action == settings_action and item:
            dialog = SettingsDialog(item, self)
            dialog.exec_()
        elif action == delete_action and item:
            self.list_widget.takeItem(self.list_widget.row(item))

    def add_game(self):
        game_path, _ = QFileDialog.getOpenFileName(self, "Select Game", "", "Executable Files (*.exe *.bat);;All Files (*)")
        if game_path:
            item = QListWidgetItem(os.path.basename(game_path))
            item.setData(Qt.UserRole, game_path)
            item.setData(Qt.UserRole + 1, "")  # Initialize the image path
            self.list_widget.addItem(item)

    def launch_selected_game(self):
        item = self.list_widget.currentItem()
        if item:
            game_path = item.data(Qt.UserRole)
            if game_path:
                self.launch_game(game_path)
            else:
                QMessageBox.warning(self, "No Game Path", "No game path set for the selected game.")

    def launch_game(self, game_path):
        process = QProcess(self)
        # Handle .bat files with cmd /c
        if any(ext in game_path for ext in [".bat", "diva.exe"]):
            if not process.startDetached("cmd", ["/c", game_path]):
                QMessageBox.critical(self, "Launch Failed", "Failed to launch the .bat file.")
        else:
            if not process.startDetached(game_path):
                QMessageBox.critical(self, "Launch Failed", "Failed to launch the game.")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as file:
                try:
                    config = json.load(file)
                    print(f"Config type: {type(config)}")  # Debug statement
                    if isinstance(config, list):
                        for game in config:
                            print(f"Game type: {type(game)}, Game content: {game}")  # Debug statement
                            if isinstance(game, dict):
                                item = QListWidgetItem(game.get("name", "Unknown Game"))
                                item.setData(Qt.UserRole, game.get("path", ""))
                                item.setData(Qt.UserRole + 1, game.get("image", ""))  # Store the image path
                                item.setIcon(QIcon(game.get("image", "")) if game.get("image") else QIcon())
                                self.list_widget.addItem(item)
                            else:
                                print("Game is not a dictionary")
                    else:
                        print("Config file is not a list")
                except json.JSONDecodeError:
                    print("Failed to decode JSON from config file")

    def save_config(self):
        config = []
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            config.append({
                "name": item.text(),
                "path": item.data(Qt.UserRole),
                "image": item.data(Qt.UserRole + 1)  # Save the image path
            })
        with open(CONFIG_FILE, 'w') as file:
            json.dump(config, file, indent=4)

    def closeEvent(self, event):
        self.save_config()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = SegaLauncher()
    launcher.show()
    sys.exit(app.exec_())