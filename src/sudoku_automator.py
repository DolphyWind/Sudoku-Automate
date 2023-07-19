from ppadb.client import Client
from ppadb.device import Device
from PIL import Image
import pathlib
import io
import datetime
from sudoku_solver import SudokuSolver
import time
import readline
import copy
import json
import cv2
import numpy as np
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore', message='Number of distinct clusters*')


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
    
    def crop_image(self, img: Image.Image, x: int, y: int, width: int, height: int) -> Image.Image:
        return img.crop((x, y, x + width, y + height))
    
    def get_square_coords(self, board_data: dict[str, int], x_board: int, y_board: int) -> tuple:
        """Get the top left coordinates of specified square in the coordinate space of the image

        Args:
            board_data (dict[str, int]): Board data dictionary
            x_board (int): Horizontal index of the square 
            y_board (int): Vertical index of the square

        Returns:
            tuple: x,y coordinate of the given square
        """
        square_x = board_data["square_x"]
        square_y = board_data["square_y"]
        square_width = board_data["square_width"]
        square_height = board_data["square_height"]
        horizontal_gaps = board_data["horizontal_gaps"]
        vertical_gaps = board_data["vertical_gaps"]
        
        return (
            square_x + (x_board) * square_width + sum(horizontal_gaps[:x_board]),
            square_y + (y_board) * square_height + sum(vertical_gaps[:y_board]),
                )
    
    def get_square_images(self, screenshot: Image.Image, board_data: dict[str, int]) -> list[Image.Image]:
        """Get all square images at the given indexes

        Args:
            screenshot (Image.Image): Screenshot of the game
            board_data (dict[str, int]): Board data dictionary

        Returns:
            list[Image.Image]: All 81 squares in a list
        """
        
        square_width = board_data["square_width"]
        square_height = board_data["square_height"]
        
        squares: list[Image.Image] = []
        for y in range(0, 9):
            for x in range(0, 9):
                current_x, current_y = self.get_square_coords(board_data, x, y)
                square = screenshot.crop((current_x, current_y, current_x + square_width, current_y + square_height))
                squares.append(square)
                
                if self.debug:
                    pathlib.Path(f"{self.total_debug_path}/squares/").mkdir(exist_ok=True, parents=True)
                    square.save(f"{self.total_debug_path}/squares/square_{y}_{x}.png")
        
        return copy.deepcopy(squares)

    def square_to_int(self, square_img: Image.Image) -> int:
        """Extract the number from square image. 

        Args:
            square_img (Image.Image): Image to process

        Returns:
            int: The number on the square
        """
        primary_color = (255, 255, 255, 255)
        secondary_color = (0, 0, 0, 255)
        
        opencv_image = np.array(square_img)
        reshaped_image = cv2.cvtColor(opencv_image, cv2.COLOR_RGBA2RGB).reshape(-1, 3)
        
        if (reshaped_image == reshaped_image[0]).all() == 1:
            return 0
        
        kmeans = KMeans(n_clusters=2, n_init='auto')
        kmeans.fit(reshaped_image)
        
        primary_number = 0
        labels = kmeans.labels_
        unique_labels, counts = np.unique(labels, return_counts=True)
        
        if counts[0] > counts[1]:
            primary_number = unique_labels[0]
        else:
            primary_number = unique_labels[1]
        
        labels = labels.reshape(opencv_image.shape[0], opencv_image.shape[1])
        for y in range(opencv_image.shape[0]):
            for x in range(opencv_image.shape[1]):
                if labels[y, x] == primary_number:
                    opencv_image[y, x] = primary_color
                else:
                    opencv_image[y, x] = secondary_color
        # import random
        # cv2.imwrite(f"./{self.total_debug_path}/square_{random.randint(0, 99999)}.png", opencv_image)       
        return 1
    
    def squares_to_board(self, squares: list[Image.Image]) -> list[list[int]]:
        """Convert list of square images to board

        Args:
            squares (list[Image.Image]): List of square images

        Returns:
            list[list[int]]: Board
        """
        
        board: list[list[int]] = []
        for y in range(0, 9):
            line: list[int] = []
            for x in range(0, 9):
                line.append(self.square_to_int(squares[y * 9 + x]))
            board.append(copy.deepcopy(line))
        return board
                
    
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
        
        if self.debug:
            time, img = time_function(
                SudokuAutomator.crop_image,
                time,
                "Cropping grid...",
                "Cropped grid!",
                self, screenshot, board_data["board_x"], board_data["board_y"], board_data["board_width"], board_data["board_height"]
            )
            img.save(f"{self.total_debug_path}/grid.png")
        
        time, squares = time_function(
            SudokuAutomator.get_square_images,
            time,
            "Extracting squares...",
            "All squares are extracted!",
            self, screenshot, board_data
        )
        
        print(np.matrix(self.squares_to_board(squares)))
        

if __name__ == "__main__":
    try:
        automator = SudokuAutomator(True)
        automator.run()
    except RuntimeError as re:
        print(f"A runtime error occured: {re}")
    # except Exception as e:
    #     print(f"An unexpected error occured: {e}")