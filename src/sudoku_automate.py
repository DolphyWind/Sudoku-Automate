from ppadb.client import Client
from PIL import Image
import io
import os
from datetime import datetime
import sudoku_solver
import time

line_length = (0, 1, 2, 6, 1, 2, 6, 1, 2)  # Length of the lines between squares
square_width, square_height = 113, 113     # square size
grid_topleft = (21, 321)                   # Game grid's top left coord
grid_bottomright = (1058, 1358)            # Game grid's bottom right coord
answer1_pos = (90, 1650)                   # Position of the first answer button
answer_dist = 115                          # Distance between two answer buttons

debug_folder_suffix = datetime.now().strftime("%d-%m-%Y %H-%M-%S")

# Connect device via adb
def connect():
    adb = Client(host="127.0.0.1", port=5037)
    devices = adb.devices()
    if len(devices) == 0:
        print("No device found!")
        quit(1)
    return devices[0]

# Take screenshot
def takeScreenshot(device, save=False):
    global debug_folder_suffix
    image = device.screencap()
    image = Image.open(io.BytesIO(image))
    if save:
        image.save('debug/Images {}/screenshot.png'.format(debug_folder_suffix))
    return image

# Get lines from picture grid
def getLines(pic_grid: Image, save=False):
    global line_length
    global square_width, square_height
    global debug_folder_suffix
    line_list = list()
    for i in range(9):
        left = 0
        top = i * square_height + sum(line_length[:i]) + line_length[i]
        right = pic_grid.width
        bottom = top + square_height
        line = pic_grid.crop((left, top, right, bottom))
        if save:
            try:
                os.mkdir("debug/Images {}/lines".format(debug_folder_suffix))
            except FileExistsError:
                pass
            line.save('debug/Images {}/lines/line_{}.png'.format(debug_folder_suffix, i))
        line_list.append(line)
    return line_list

# Get all squares from line
def getSquares(line: Image, suffix='', save=False):
    global line_length
    global square_width, square_height
    global debug_folder_suffix
    square_list = list()
    for i in range(9):
        left = i * square_width + sum(line_length[:i]) + line_length[i]
        top = 0
        right = left + square_width
        bottom = square_height
        square = line.crop((left, top, right, bottom))
        if save:
            try:
                os.mkdir("debug/Images {}/squares".format(debug_folder_suffix))
            except FileExistsError:
                pass
            square.save('debug/Images {}/squares/square_{}_{}.png'.format(debug_folder_suffix, suffix, i))
        square_list.append(square)
    return square_list

# Convert picture square to number
def proccessSquare(square: Image):
    square = square.convert('RGB')
    control = lambda x, y: square.getpixel((x, y)) == (33, 33, 33)
    def controlmany(*args):
        for (x, y) in args:
            if control(x, y) == False:
                return False
        return True

    if controlmany((44, 37), (52, 34), (61, 30), (59, 56), (59, 80)):
        return 1
    if controlmany((41, 40), (54, 30), (68, 41), (57, 62), (42, 81), (72, 81)):
        return 2
    if controlmany((41, 39), (54, 29), (69, 41), (56, 54), (69, 67), (55, 80), (40, 71)) and not control(44, 48):
        return 3
    if controlmany((64, 30), (50, 47), (39, 66), (65, 66), (65, 78), (71, 67)):
        return 4
    if controlmany((70, 30), (48, 29), (47, 52), (59, 49), (72, 64), (58, 80), (44, 71)):
        return 5
    if controlmany((63, 30), (48, 37), (43, 55), (58, 80), (71, 65), (59, 49)):
        return 6
    if controlmany((41, 31), (72, 30), (63, 54), (50, 80)):
        return 7
    if controlmany((55, 29), (57, 53), (57, 81), (42, 67), (71, 68), (44, 41), (71, 42)):
        return 8
    if controlmany((53, 30), (40, 46), (68, 45), (54, 62), (65, 72), (49, 80)):
        return 9
    return 0

def main():
    global line_length
    global square_width, square_height
    global grid_topleft, grid_bottomright
    global answer1_pos, answer_dist
    global debug_folder_suffix
    
    # Create debug folder, if it's not exists
    try:
        os.mkdir("debug")
    except FileExistsError:
        pass

    # debug value: when set to True, all squares, lines etc. will be saved on thisk
    debug = True
    
    # If debug is enabled, create folder to save our images
    if debug:
        try:
            os.mkdir("debug/Images {}".format(debug_folder_suffix))
        except FileExistsError:
            pass

    t0 = time.time()

    # Connect
    my_device = connect()
    print('Connected ({} seconds elapsed)'.format(round(time.time() - t0, 2)))
    print('Creating sudoku grid...')

    # Take screenshot
    screenshot = takeScreenshot(my_device, save=debug)

    # Crop grid from screenshot
    picture_grid = screenshot.crop((grid_topleft[0], grid_topleft[1], grid_bottomright[0], grid_bottomright[1]))
    if debug:
        picture_grid.save('debug/Images {}/grid.png'.format(debug_folder_suffix))

    # find lines
    lines = getLines(picture_grid, save=debug)

    # Convert picture grid to list grid
    grid = list()
    for i in range(9):
        squares = getSquares(lines[i], suffix=i, save=debug)
        line = list()
        for square in squares:
            n = proccessSquare(square)
            line.append(n)
        grid.append(line)

    print('Sudoku grid created ({} seconds elapsed)'.format(round(time.time() - t0, 2)))
    print('Solving...')

    # Solve
    sudoku_solver.solve(grid)
    result = sudoku_solver.result

    print('Solved! ({} seconds elapsed)'.format(round(time.time() - t0, 2)))
    print('Solving the sudoku on your phone...')

    # Solve on phone (adb is so slow :( )
    for y in range(9):
        for x in range(9):
            if grid[y][x] == 0:
                tap_x = grid_topleft[0] + x * square_width + line_length[x] + square_width // 2
                tap_y = grid_topleft[1] + y * square_height + line_length[y] + square_height // 2
                my_device.shell('input tap {} {}'.format(tap_x, tap_y))
                answer = result[y, x]
                answer = answer - 1
                my_device.shell('input tap {} {}'.format(answer1_pos[0] + answer * answer_dist, answer1_pos[1]))
    print('Done!')
    print('Total time: {} seconds'.format(round(time.time() - t0, 2)))


if __name__ == '__main__':
    main()