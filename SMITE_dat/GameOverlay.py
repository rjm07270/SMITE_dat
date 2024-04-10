from asyncio import Lock
from re import X
from turtle import left
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QPixmap, QImage, QKeySequence
import pygetwindow as gw
import pyautogui
import psutil
from PIL import Image
import numpy as np
import sys
import time
import keyboard
import requests
import cv2
import time
from threading import Thread
from db import db
from SMITE import Item

from pyrect import TOP

class Worker(QtCore.QObject):
    update_signal = QtCore.pyqtSignal(object)  # Signal to send data to the main thread
    xCord=0
    yCord=0
    itemLocashions=[]

    def run(self, smite_titles):
        while True:
            game_window_found = False
            box =None
            for title in smite_titles:
                windows = gw.getWindowsWithTitle(title)
                for window in windows:
                    if not window.isMinimized:  # Check if the window is not minimized 
                        box = window.box
                        game_window_found = True
                        break

                if game_window_found:
                    break  # Exit the loop if a valid game window is found

            if not game_window_found:
                
                self.update_signal.emit(None)
            else:
                
                #left, top, width, height 
                # For testing, create a red square image
                left, top, width, height = box[0], box[1], box[2], box[3]  # Set the size of the square
                red_square = np.zeros((height, width, 3), dtype=np.uint8)
                red_square[:, :] = [0, 255, 0]  # Red color
                image = Image.fromarray(red_square)
                image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                #self.update_signal.emit(screenshot)  # Emit the signal with the screenshot
                self.xCord=left
                self.yCord=top
                self.update_signal.emit(image)
                
            time.sleep(1)  # Check every second

class GameOverlay(QtWidgets.QWidget):
    tab_down_key=False
    def __init__(self):
        super().__init__()
        tab_down_key=False
        self.initUI()
        self.isItemMenueUp = False
        sql = "SELECT ActiveFlag, ChildItemId, DeviceName, Glyph, IconId, ItemId, ItemTier, Price, RootItemId, StartingItem, Type, itemIcon_URL, ret_msg FROM items"
        raw_data=db.get(sql)
        self.items_list = None
       # self.items_list = [Item(*data) for data in raw_data]
        print("Done loading images")


    def initUI(self):
        self.setWindowTitle("Game Overlay")
        self.setGeometry(1, 1, 1, 1)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # Set window flags
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |  # Frameless window
            QtCore.Qt.WindowStaysOnTopHint |  # Always on top
            QtCore.Qt.WindowTransparentForInput  # Transparent for input
        )
        self.setStyleSheet("background: transparent;")
        self.show()

        self.worker = Worker()
        self.worker.update_signal.connect(self.set_image)

        self.thread = Thread(target=self.start_worker_thread)
        self.thread.daemon = True
        self.thread.start()
        
        keyboard.on_press_key("tab", self.on_tab_press)
        keyboard.on_release_key("tab", self.on_tab_press)
        
        keyboard.on_press_key("i", self.on_i_press)
        

    def start_worker_thread(self):
        smite_titles = ["Smite (64-bit, DX9)", "Smite (32-bit, DX9)", "Smite (64-bit, DX11)", "Smite (32-bit, DX11)"]
        self.worker.run(smite_titles)

    def set_image(self, image):
        
        if image:   
            if isinstance(image, QPixmap):
                pixmap = image
            elif hasattr(image, 'tobytes'):
                # Assuming 'image' is your PIL Image object
                if image.mode == "RGBA":
                    # Ensure the image is in RGBA format to include an alpha channel
                    qimage = QImage(image.tobytes(), image.size[0], image.size[1], QImage.Format_ARGB32)
                else:
                    # Convert the image to RGBA first if it's not
                    rgba_image = image.convert("RGBA")
                    qimage = QImage(rgba_image.tobytes(), rgba_image.size[0], rgba_image.size[1], QImage.Format_ARGB32)

                pixmap = QPixmap.fromImage(qimage)
            else:
                return  # If the image is neither QPixmap nor PIL Image, do nothing

            # Resize and reposition the overlay window to match the image size
            self.resize(pixmap.size())
            self.move(self.worker.xCord, self.worker.yCord)  # Adjust the position as needed

            # Display the image
            label = QtWidgets.QLabel(self)
            label.setPixmap(pixmap)
            label.resize(pixmap.size())
            label.show()
        else:
            self.hide()  # Hide the overlay if no image is passed


        
   
    def on_tab_press(self, event):
        #print(event.event_type)
        if event.event_type == 'down':
            # Key is pressed down
            if not GameOverlay.tab_down_key:
                # If the key was not already down, set it to down and capture the screen
                GameOverlay.tab_down_key = True
                print("Tab key pressed down.")
                self.capture_screen()
        elif event.event_type == 'up':
            # Key is released
            GameOverlay.tab_down_key = False
            print("Tab key released.")

    def capture_screen(self):
        """Capture the screen and save it to a file, cropped to the overlay's geometry."""
        print("Capture the screen")
        # Get the geometry of the overlay window
        geometry = self.geometry()
        x, y, width, height = geometry.x(), geometry.y(), geometry.width(), geometry.height()
        time.sleep(0.15)    #Too fast
        # Capture the specified region
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        #screenshot.save('screenshot.png')  # Save the screenshot
        #print("saving")
        self.find_rectangle_by_border_color(screenshot)
        
    def find_rectangle_by_border_color(self, pil_image):
        # Check if pil_image is empty
        if pil_image is None:
            raise ValueError("The image is empty or not loaded correctly.")

        # Convert the PIL Image to a NumPy array
        image_cv = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        # RGB color to search for (as provided earlier)
        target_rgb_color = (190, 133, 81)

        # Convert the RGB color to BGR color format (OpenCV uses BGR)
        target_bgr_color = target_rgb_color[::-1]

        # Set a threshold for color matching
        # You may need to adjust this if your color match needs to be more or less strict
        threshold = 10

        # Create a mask where the color matches
        min_bgr_color = np.array([max(target_bgr_color[0]-threshold, 0),
                                   max(target_bgr_color[1]-threshold, 0),
                                   max(target_bgr_color[2]-threshold, 0)])
        max_bgr_color = np.array([min(target_bgr_color[0]+threshold, 255),
                                   min(target_bgr_color[1]+threshold, 255),
                                   min(target_bgr_color[2]+threshold, 255)])

        # Find the color within the specified threshold
        color_mask = cv2.inRange(image_cv, min_bgr_color, max_bgr_color)

        # Use the mask to extract the contour/rectangle
        # You can use cv2.findContours to find the contours of the rectangles
        contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        largest_area = 0
        largest_rectangle = None

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h

            # Check if the rectangle meets the size criteria
            if w >= 20 and h >=21  and w <= 21 and h <= 21:
                if area > largest_area:
                    largest_area = area
                    largest_rectangle = (x, y, w, h)

                # Draw a red rectangle on the image
                cv2.rectangle(image_cv, (x, y), (x + w, y + h), (0, 0, 255), 2)

        # Print the coordinates of the largest rectangle
        print(largest_rectangle)

        # Display the image with rectangles drawn
        cv2.imshow('Image with Rectangles', image_cv)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        return largest_rectangle
        



    def find_image_in_screenshot(screenshot_cv, webp_image_cv):
        # Apply template matching with the mask if your image has transparency
        # If your webp_image_cv doesn't have an alpha channel, you can omit the mask part
        result = cv2.matchTemplate(screenshot_cv, webp_image_cv, cv2.TM_CCOEFF_NORMED)
    
        # Threshold and position detection remains the same as in the previous example
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val > 0.8:  # Adjust the threshold as necessary
            top_left = max_loc
            print(f"Image found at position: {top_left}")
        else:
            print("Image not found.")

    def on_i_press(self, event):
        self.isItemMenueUp=True
        