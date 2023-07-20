# Sudoku Automate

This bot is designed to solve the Android game "Sudoku - Classic Sudoku Puzzle" created by "Kiduit Lovin". I have made efforts to make it compatible with various phone models and different Sudoku games. However, please note that I haven't extensively tested it with all setups.  

Upon running the script, if the board data file is not found, the bot will prompt you to provide the top-left coordinates of the first square, the coordinates of the first answer button, and the horizontal distance between two consecutive answer buttons. For this reason, if it's your first time running the program, I recommend using debug mode. This can be enabled using the -d or --debug options. In debug mode, the images that program obtains are saved into a folder called `debug`.  

After asking you these questions the program will gather other board information and saves all data it has about the board into a file called `board_data.json`. As long as that file is present, It wont ask you any questions if you run the script in the future. Also, you can change the board data filename using the `-bd` or `--boarddata` options.

This script is also designed to be embedablity in mind. You can use this script into another script without any problem.

To run the program, please ensure that you have all of the necessary python libraries and a running ADB server. If you don't know what ADB is please visit [this](https://developer.android.com/tools/adb) website. Then run the `sudoku_automator.py` with `python`.


To download the game, click [here](https://play.google.com/store/apps/details?id=easy.sudoku.puzzle.solver.free).
