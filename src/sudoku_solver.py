import numpy as np

result = None

def isPossible(grid, y, x, n):
    for i in range(9):
        if grid[y][i] == n:
            return False
    for i in range(9):
        if grid[i][x] == n:
            return False
    x0 = (x // 3) * 3
    y0 = (y // 3) * 3
    for i in range(3):
        for j in range(3):
            if grid[y0 + i][x0 + j] == n:
                return False
    return True

def solve(grid):
    global result
    for y in range(9):
        for x in range(9):
            if grid[y][x] == 0:
                for n in range(1, 10):
                    if isPossible(grid, y, x, n):
                        grid[y][x] = n
                        solve(grid)
                        grid[y][x] = 0
                return
    result = np.matrix(grid)