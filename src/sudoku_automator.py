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
from skimage.metrics import structural_similarity as ssim
import warnings
import argparse
warnings.filterwarnings('ignore', message='Number of distinct clusters*')


def time_function(func, t0: float, message_before: str, message_after: str, *args: tuple) -> tuple:
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
    def __init__(self, debug=False, board_data_filename="board_data.json") -> None:
        self.debug: bool = debug
        self.device: Device = None
        self.total_debug_path: str = ""
        self.number_squares: list[np.ndarray] = []
        self.board_data_filename: str = board_data_filename

        self.createDebugFolders()
        self.load_number_squares()

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

    def load_number_squares(self) -> None:
        """Loads the number squares from the folder number_squares"""

        self.number_squares: list[np.ndarray] = []
        for i in range(1, 10):
            img = cv2.imread(f"./number_squares/{i}.png")
            self.number_squares.append(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))

    def connectToPhone(self) -> None:
        """Connects to your phone via adb"""

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
        """Gathers the board info, it asks some question to user if the board data file
        is not present. If the file is present, it just reads the file and returns
        the data it got.

        Args:
            screenshot (Image.Image): Screenshot of the phone with the board visible.

        Returns:
            dict[str, int]: The board data as dictionary.
        """

        # Reads the top left coordinate of the board. It asks the user for once. Reads board info,
        # then saves it to a file called "board_data.json". As long as that file exists,
        # it reads from there in the future.
        board_width, board_height = 0, 0
        square_x, square_y = 0, 0
        square_width, square_height = 0, 0
        horizontal_gaps = []
        vertical_gaps = []
        answer_x, answer_y = 0, 0
        answer_distance = 0

        board_data = dict()

        if (pathlib.Path(self.board_data_filename).exists()):
            with open(self.board_data_filename, "r") as file:
                board_data = json.load(file)
        else:
            while True:
                xy_coords: str = input("Please enter the top left coordinates of the first square seperated by a comma: ")
                try:
                    x_str, y_str = xy_coords.split(',')
                    square_x, square_y = int(x_str), int(y_str)
                    if square_x < 0 or square_y < 0 or square_x > screenshot.size[0] or square_y > screenshot.size[1]:
                        raise Exception()
                except Exception:
                    print("Please enter a valid coordinate!")
                else:
                    break
            pathlib.Path(self.board_data_filename).touch()

            def is_close_color(c1: tuple, c2: tuple, tol: float) -> bool:
                square_sum = 0
                for a, b in zip(c1, c2):
                    square_sum += (a - b) ** 2
                return (square_sum**.5) <= tol

            def get_size_of_area(img: Image.Image, x: int, y: int, height: bool = False) -> int:
                size = 0
                color = img.getpixel((x, y))

                while is_close_color(img.getpixel((x + size * int(not height), y + size * int(height))), color, 5):
                    size += 1
                return size

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

            board_width = 9 * square_width + sum(horizontal_gaps)
            board_height = 9 * square_height + sum(vertical_gaps)

            while True:
                answer_xy: str = input("Please enter the center position of the first answer button, seperated by comma: ")
                try:
                    answer_xstr, answer_ystr = answer_xy.split(',')
                    answer_x, answer_y = int(answer_xstr), int(answer_ystr)
                except Exception:
                    print("Please enter a valid input!")
                else:
                    break

            while True:
                answer_dist_str = input("Please enter the distance between two answer buttons: ")
                try:
                    answer_distance = int(answer_dist_str)
                except Exception:
                    print("Please enter a valid input!")
                else:
                    break

            board_data = {
                "board_width": board_width,
                "board_height": board_height,
                "square_x": square_x,
                "square_y": square_y,
                "square_width": square_width,
                "square_height": square_height,
                "horizontal_gaps": horizontal_gaps,
                "vertical_gaps": vertical_gaps,
                "answer_x": answer_x,
                "answer_y": answer_y,
                "answer_distance": answer_distance,
            }
            with open(self.board_data_filename, "w") as file:
                json.dump(board_data, file)

        return board_data

    def crop_image(self, img: Image.Image, x: int, y: int, width: int, height: int) -> Image.Image:
        """Crops the given image by the given coordinate and size

        Args:
            img (Image.Image): Image to crop
            x (int): X coordinate of the top left pixel of the new image
            y (int): Y coordinate of the top left pixel of the new image
            width (int): Width of the new image
            height (int): Height of the new image

        Returns:
            Image.Image: Cropped image
        """
        return img.crop((x, y, x + width, y + height))

    def get_square_coords(self, board_data: dict[str, int], x_board: int, y_board: int) -> tuple:
        """Get the top left coordinates of specified square on the screenshot

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
        """Get all square images that are on the board

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

    def get_empty_squares(self, board: list[list[int]]) -> list[tuple[int, int]]:
        """Get a list of indexes of empty squares on the given board

        Args:
            board (list[list[int]]): Board to process

        Returns:
            list[tuple[int, int]]: Indexes of empty squares
        """
        indexes: list[tuple[int, int]] = []
        for y in range(0, 9):
            for x in range(0, 9):
                if board[y][x] == 0:
                    indexes.append((x, y))

        return indexes

    def square_to_int(self, square_img: Image.Image) -> int:
        """Extract the number from given square image.

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

        gray_img = cv2.cvtColor(opencv_image, cv2.COLOR_RGB2GRAY)
        if gray_img.shape != self.number_squares[0].shape:
            gray_img = cv2.resize(gray_img, self.number_squares[0].shape)

        ssim_list: list[int] = []
        for i in range(0, 9):
            result = ssim(gray_img, self.number_squares[i])
            ssim_list.append(result)

        return ssim_list.index(max(ssim_list)) + 1

    def squares_to_board(self, squares: list[Image.Image]) -> list[list[int]]:
        """Convert the given list of square images to a sudoku board

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

    def solve_on_screen(
        self,
        empty_squares: list[tuple[int, int]],
        solution: list[list[int]],
        board_data: dict[str, int]
    ) -> None:
        """Solves the sudoku on your phone

        Args:
            empty_squares (list[tuple[int, int]]): A list containing the indexes of empty squares
            solution (list[list[int]]): Solution board
            board_data (dict[str, int]): Board data dictionary
        """
        half_square_width = board_data["square_width"] // 2
        half_square_height = board_data["square_height"] // 2

        answer_x: int = board_data["answer_x"]
        answer_y: int = board_data["answer_y"]
        answer_distance = board_data["answer_distance"]

        for x, y in empty_squares:
            answer: int = solution[y][x]
            square_pos = self.get_square_coords(board_data, x, y)
            square_pos = square_pos[0] + half_square_width, square_pos[1] + half_square_height

            answer_pos = answer_x + (answer - 1) * answer_distance, answer_y

            self.device.shell(f"input tap {square_pos[0]} {square_pos[1]}")
            self.device.shell(f"input tap {answer_pos[0]} {answer_pos[1]}")

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
                self, screenshot, board_data["square_x"], board_data["square_y"], board_data["board_width"], board_data["board_height"]
            )
            img.save(f"{self.total_debug_path}/grid.png")

        time, squares = time_function(
            SudokuAutomator.get_square_images,
            time,
            "Extracting squares...",
            "All squares are extracted!",
            self, screenshot, board_data
        )

        time, board = time_function(
            SudokuAutomator.squares_to_board,
            time,
            "Converting images to board...",
            "Converted images to board!",
            self, squares
        )

        time, empty_squares = time_function(
            SudokuAutomator.get_empty_squares,
            time,
            "Getting empty squares...",
            "Got empty squares!",
            self, board
        )

        time, solved_boards = time_function(
            SudokuSolver.solve,
            time,
            "Solving the board...",
            "Solved the board!",
            board
        )

        board_solution: list[list[int]] = None
        if len(solved_boards) > 1:
            print(f"Found {len(solved_boards)} solution(s).")
            print("Please select which solution you want to use:")

            for i, sb in enumerate(solved_boards):
                print(i, np.matrix(sb))

            while True:
                index_str: str = input(">>> ")
                try:
                    index = int(index_str)
                    if index >= len(solved_boards):
                        print("Please enter a valid number!")
                        continue
                    board_solution = solved_boards[index]
                except Exception:
                    print("Please enter a valid number!")
                else:
                    break
        elif len(solved_boards) == 0:
            raise RuntimeError("Could not find any solutions to given board!")
        else:
            board_solution = solved_boards[0]

        time = time_function(
            SudokuAutomator.solve_on_screen,
            time,
            "Solving the game on your phone...",
            "Solved the game on your phone!",
            self, empty_squares, board_solution, board_data
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A sudoku solver script that solves a sudoku game on your phone."
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debugging. If enabled, the program saves the images it got to a folder called debug."
    )
    parser.add_argument(
        "-bd", "--boarddata",
        help="The file to read and store the board data."
    )
    args = parser.parse_args()

    if args.boarddata is None:
        args.boarddata = "board_data.json"

    try:
        automator = SudokuAutomator(args.debug, args.boarddata)
        automator.run()
    except RuntimeError as re:
        print(f"A runtime error occured: {re}")
    except Exception as e:
        print(f"An unexpected error occured: {e}")
