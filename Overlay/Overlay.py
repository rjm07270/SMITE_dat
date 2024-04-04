from PyQt5 import QtWidgets, QtCore
import pygetwindow as gw
import pyautogui

class Overlay:
    window = None

    @staticmethod
    def create_overlay():
        if not GameOverlay.window:
            app = QtWidgets.QApplication([])
            GameOverlay.window = QtWidgets.QWidget()
            GameOverlay.window.setWindowFlags(
                QtCore.Qt.FramelessWindowHint | 
                QtCore.Qt.WindowStaysOnTopHint | 
                QtCore.Qt.WindowTransparentForInput | 
                QtCore.Qt.WindowDoesNotAcceptFocus)

            GameOverlay.window.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            GameOverlay.window.setGeometry(300, 300, 250, 150)  # Customize as needed
            GameOverlay.window.show()
            app.exec_()

    @staticmethod
    def capture_game_window():
        smite_window = gw.getWindowsWithTitle("Smite")[0]
        if smite_window:
            smite_window.activate()
            return pyautogui.screenshot(region=(smite_window.left, smite_window.top, smite_window.width, smite_window.height))
        return None

    @staticmethod
    def set_image(image):
        # Logic to update the overlay with a new image
        pass

    @staticmethod
    def update_overlay():
        image = GameOverlay.capture_game_window()
        GameOverlay.set_image(image)