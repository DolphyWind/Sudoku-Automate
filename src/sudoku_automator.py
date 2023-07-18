from ppadb.client import Client
from ppadb.device import Device
from PIL import Image
import pathlib
import io
import datetime
from sudoku_solver import SudokuSolver
import time
import pytesseract
import readline
import json


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
    start_time: float = time.time()
    result = func(*args)
    end_time: float = time.time()
    delta_time: float = end_time - start_time
    print(f"{message_after} Total time: {round(t0 + delta_time, 2)} seconds.")
    return t0 + delta_time, result

class SudokuAutomator:
    def __init__(self, debug=False) -> None:
        self.debug: bool = debug
        self.device: Device = None
        self.total_debug_path: str = ""
        self.createDebugFolders()

    def createDebugFolders(self) -> None:
        """Creates the debug folders if debugging is enabled"""
        if not self.debug:
            return
        
        debugFoldername = "debug"
        currentDate: datetime.datetime = datetime.datetime.now()
        currentDateStr = currentDate.strftime("%Y_%m_%d %H_%M_%S")
        self.total_debug_path = f"./{debugFoldername}/Images {currentDateStr}/"
        
        pathlib.Path(f"./{debugFoldername}").mkdir(exist_ok=True)
        pathlib.Path(self.total_debug_path).mkdir(exist_ok=True, parents=True)    

    def connectToPhone(self) -> None:
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
        image: Image = Image.open(io.BytesIO(image))
        if self.debug:
            image.save(f"{self.total_debug_path}/screenshot.png")
        
        return image
    
    def analyze_board(self, screenshot: Image.Image) -> dict[str, int]:
        """Gets the board info, it asks for the top left coordinates of the board to user once.
        Then it saves it to a file and reads it from there.
        """
        
        # Reads the top left coordinate of the board. It asks the user for once. Reads board info,
        # then saves it to a file called "board_data.json". As long as that file exists, 
        # it reads from there in the future.
        data_file_path = "./board_data.json"
        board_x, board_y = 0, 0
        board_width, board_height = 0, 0
        square_x, square_y = 0, 0
        square_width, square_height = 0, 0
        horizontal_gaps = []
        vertical_gaps = []
        
        board_data = dict()
        
        if (pathlib.Path(data_file_path).exists()):
            with open(data_file_path, "r") as file:
                board_data = json.load(file)
        else:
            while True:
                xy_coords: str = input("Please enter the top left coordinates of the board, include the border of the board, seperated by a comma: ")
                try:
                    x_str, y_str = xy_coords.split(',')
                    board_x, board_y = int(x_str), int(y_str)
                    if board_x < 0 or board_y < 0 or board_x > screenshot.size[0] or board_y > screenshot.size[1]:
                        raise Exception()
                except:
                    print("Please enter a valid coordinate!")
                else:
                    break
            pathlib.Path(data_file_path).touch()
            
            top_left_color = screenshot.getpixel((board_x, board_y))
            
            def get_size_of_area(img: Image.Image, x: int, y: int, height: bool=False) -> int:
                size = 0
                color = img.getpixel((x, y))
                while img.getpixel((x + size * int(not height), y + size * int(height))) == color:
                    size += 1
                return size
            
            # Get board dimensions
            board_width = get_size_of_area(screenshot, board_x, board_y, False)
            board_height = get_size_of_area(screenshot, board_x, board_y, True)
            
            # Find top left coords of the first square
            for h in range(0, board_height):
                broke_out = False
                for w in range(0, board_width):
                    if screenshot.getpixel((board_x + w, board_y + h)) != top_left_color:
                        broke_out = True
                        square_x = board_x + w
                        square_y = board_y + h
                        break
                if broke_out:
                    break
            
            square_top_left_color = screenshot.getpixel((square_x, square_y))
            
            # Get square dimensions
            square_width = get_size_of_area(screenshot, square_x, square_y, False)
            square_height = get_size_of_area(screenshot, square_x, square_y, True)
            
            # Get the sizes of horizontal and vertical haps
            start_x_original = square_x + square_width
            start_y_original = square_y + square_height
            
            start_x = start_x_original
            while len(horizontal_gaps) < 8:
                size = get_size_of_area(screenshot, start_x, square_y)
                start_x += size + square_width
                horizontal_gaps.append(size)
            
            start_y = start_y_original
            while len(vertical_gaps) < 8:
                size = get_size_of_area(screenshot, square_x, start_y, True)
                start_y += size + square_height
                vertical_gaps.append(size)
            
            board_data = {
                "board_x": board_x,
                "board_y": board_y,
                "board_width": board_width,
                "board_height": board_height,
                "square_x": square_x,
                "square_y": square_y,
                "square_width": square_width,
                "square_height": square_height,
                "horizontal_gaps": horizontal_gaps,
                "vertical_gaps": vertical_gaps
            }
            with open(data_file_path, "w") as file:
                json.dump(board_data, file)
        
        return board_data
    
    def run(self) -> None:
        """Runs the Automator"""
        time: float = 0.0
        time: float = time_function(
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
        time, board_data = time_function(
                        SudokuAutomator.analyze_board,
                        time,
                        "Analyzing board...",
                        "Board analyzed!",
                        self, screenshot
                        )
        

if __name__ == "__main__":
    try:
        automator = SudokuAutomator(True)
        automator.run()
    except RuntimeError as re:
        print(f"A runtime error occured: {re}")
    except Exception as e:
        print(f"An unexpected error occured: {e}")