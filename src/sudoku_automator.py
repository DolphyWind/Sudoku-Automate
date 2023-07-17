from ppadb.client import Client
from ppadb.device import Device
from PIL import Image
import pathlib
import io
import datetime
from sudoku_solver import SudokuSolver
import time
import pytesseract
from typing import get_type_hints


def time_function(func,
                  t0: float,
                  message_before: str,
                  message_after: str,
                  *args: tuple
                ) -> tuple:
    """Times a function and prints total time.
    Also returns total time.

    Args:
        func (function): Function to time
        t0 (float): Initial time in seconds
        message_before (str): Message to print before timing the function
        message_after (str): Message to print after timing the function

    Returns:
        float: Total time in seconds
    """
    
    print(message_before)
    start_time = time.time()
    result = func(*args)
    end_time = time.time()
    delta_time = end_time - start_time
    print(f"{message_after} Total time: {round(t0 + delta_time, 2)} seconds.")
    return t0 + delta_time, result

class SudokuAutomator:
    def __init__(self, debug=False) -> None:
        self.debug: bool = debug
        self.device: Device = None
        self.total_debug_path: str = ""
        self.createDebugFolders()

    def createDebugFolders(self):
        """Creates the debug folders if debugging is enabled"""
        if not self.debug:
            return
        
        debugFoldername = "debug"
        currentDate = datetime.datetime.now()
        currentDateStr = currentDate.strftime("%Y_%m_%d %H_%M_%S")
        self.total_debug_path = f"./{debugFoldername}/Images {currentDateStr}/"
        
        pathlib.Path(f"./{debugFoldername}").mkdir(exist_ok=True)
        pathlib.Path(self.total_debug_path).mkdir(exist_ok=True, parents=True)    

    def connectToPhone(self):
        """Connects your phone via adb"""
        adb = Client(host="127.0.0.1", port=5037)
        devices: list[Device] = adb.devices()

        if len(devices) == 0:
            raise RuntimeError("No devices found!")
        elif len(devices) == 1:
            self.device = devices[0]
            return
        
        for i, device in enumerate(devices):
            print(f"[{i}] {device.get_serial_no()}")
        
        while True:
            deviceIndex = int(input("Please choose your device: "))
            if deviceIndex >= len(devices) or deviceIndex < 0:
                print("Please enter a valid index!")
            else:
                self.device = devices[deviceIndex]
                break
    
    def takeScreenshot(self) -> Image.Image:
        """Takes a screenshot from your phone, converts it to PIL Image
        then returns it

        Returns:
            Image.Image: Screenshot of your phone
        """
        
        if not self.device:
            raise RuntimeError("Error: Please connect to your phone via ADB")
        
        image = self.device.screencap()
        image = Image.open(io.BytesIO(image))
        if self.debug:
            image.save(f"{self.total_debug_path}/screenshot.png")
        
        return image
    
    def run(self):
        """Runs the Automator"""
        time = 0.0
        time = time_function(
                            SudokuAutomator.connectToPhone,
                            time,
                            "Connecting to phone via ADB...",
                            "Connected to phone!",
                            self
                        )[0]
        time, screenshot = time_function(
                                        SudokuAutomator.takeScreenshot,
                                        time,
                                        "Taking a screenshot...",
                                        "Took the screenshot!",
                                        self
                                    )
        

if __name__ == "__main__":
    try:
        automator = SudokuAutomator(True)
        automator.run()
    except RuntimeError as re:
        print(f"A runtime error occured: {re}")
    except Exception as e:
        print(f"An unexpected error occured: {e}")