import numpy as np
import copy


class SudokuSolver:
    __result: list = []

    @staticmethod
    def __isPossible(grid: list[list], y: int, x: int, n: int) -> bool:
        """Checks whether the given number is suitable for the given
        sudoku cell

        Args:
            grid (list[list]): The sudoku grid
            y (int): Y coordinate of the current cell
            x (int): X coordinate of the current cell
            n (int): Number to check

        Returns:
            bool: True if the number is suitable for the given sudoku
            cell, False otherwise
        """
        # Check current rows
        for i in range(9):
            if grid[y][i] == n:
                return False

        # Check current column
        for i in range(9):
            if grid[i][x] == n:
                return False

        # Check current 3x3 square
        x0 = (x // 3) * 3
        y0 = (y // 3) * 3
        for i in range(3):
            for j in range(3):
                if grid[y0 + i][x0 + j] == n:
                    return False
        return True

    @staticmethod
    def __solve(grid: list[list]) -> None:
        """Solves sudoku recursively by treating zeros as empty cells
        and saves all results into __result variable

        Args:
            grid (list[list]): Sudoku board to solve
        """
        for y in range(9):
            for x in range(9):
                if grid[y][x] == 0:
                    for n in range(1, 10):
                        if SudokuSolver.__isPossible(grid, y, x, n):
                            grid[y][x] = n
                            SudokuSolver.__solve(grid)
                            grid[y][x] = 0
                    return
        SudokuSolver.__result.append(copy.deepcopy(grid))

    @staticmethod
    def solve(grid: list[list]) -> list[list[list]]:
        """Finds all possible solutions to tthe given sudoku board
        by treating zeros as empty cells. Also controls the state
        of the __results variable

        Args:
            grid (list[list]): Sudoku board to solve

        Returns:
            list[list[list]]: All possible solutions to the given sudoku board
        """
        SudokuSolver.__result = []
        SudokuSolver.__solve(grid.copy())
        return SudokuSolver.__result.copy()


if __name__ == "__main__":
    """Sudoku solver tests"""

    grid1 = [
        [0, 0, 0,     2, 6, 0,     7, 0, 1],
        [6, 8, 0,     0, 0, 0,     0, 9, 0],
        [1, 9, 0,     0, 0, 0,     5, 0, 0],

        [8, 2, 0,     1, 0, 0,     0, 4, 0],
        [0, 0, 4,     6, 0, 2,     9, 0, 0],
        [0, 5, 0,     0, 0, 3,     0, 2, 8],

        [0, 0, 9,     3, 0, 0,     0, 7, 4],
        [0, 4, 0,     0, 5, 0,     0, 3, 6],
        [7, 0, 3,     0, 1, 8,     0, 0, 0],
    ]

    results = SudokuSolver.solve(grid1)
    output_char_len = 40

    print(" ORIGINAL BOARD ".center(output_char_len, '-'))
    print(np.matrix(grid1))  # For pretty printing
    print("-" * output_char_len)
    print(f"Number of solutions: {len(results)}")
    print("-" * output_char_len)

    for i, result in enumerate(results, start=1):
        print(f"Solution #{i}")
        print(np.matrix(result))
        print("-" * output_char_len)
