from collections import deque
import time


def build_sample_warehouse():
    """A small 6x6 warehouse with racks blocking some aisles."""
    grid = [
        [0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 0],
        [0, 1, 0, 0, 0, 0],
        [0, 1, 0, 1, 1, 0],
        [0, 0, 0, 1, 0, 0],
        [0, 0, 0, 1, 0, 0],
    ]
    robot_start = (0, 0)   # docking bay, (row, col)
    bin_location = (5, 5)  # empty bin to restock
    return grid, robot_start, bin_location


class WarehouseAgent:
    def __init__(self, grid, start, goal):
        self.grid = grid
        self.start = start
        self.goal = goal
        self.rows = len(grid)
        self.cols = len(grid[0])

    def sense_neighbours(self, cell):
        r, c = cell
        candidates = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
        free = []
        for (nr, nc) in candidates:
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid[nr][nc] == 0:
                    free.append((nr, nc))
        return free

    def think_and_act_bfs(self):
        to_do = deque([self.start])
        visited = {self.start}
        came_from = {self.start: None}

        while to_do:
            current = to_do.popleft()
            if current == self.goal:
                return self._rebuild_path(came_from, current)
            for neighbour in self.sense_neighbours(current):
                if neighbour not in visited:
                    visited.add(neighbour)
                    came_from[neighbour] = current
                    to_do.append(neighbour)
        return None

    def think_and_act_dfs(self):
        stack = [self.start]
        visited = {self.start}
        came_from = {self.start: None}

        while stack:
            current = stack.pop()
            if current == self.goal:
                return self._rebuild_path(came_from, current)
            for neighbour in self.sense_neighbours(current):
                if neighbour not in visited:
                    visited.add(neighbour)
                    came_from[neighbour] = current
                    stack.append(neighbour)
        return None

    @staticmethod
    def _rebuild_path(came_from, current):
        path = []
        while current is not None:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path


def print_grid(grid, path=None, start=None, goal=None):
    path_cells = set(path) if path else set()
    for r, row in enumerate(grid):
        line = []
        for c, val in enumerate(row):
            cell = (r, c)
            if cell == start:
                line.append("R")
            elif cell == goal:
                line.append("B")
            elif cell in path_cells:
                line.append("*")
            elif val == 1:
                line.append("#")
            else:
                line.append(".")
        print(" ".join(line))
    print()


def run_agent(grid, start, goal, strategy="bfs", label=""):
    agent = WarehouseAgent(grid, start, goal)

    t0 = time.perf_counter()
    if strategy == "bfs":
        path = agent.think_and_act_bfs()
    else:
        path = agent.think_and_act_dfs()
    elapsed = time.perf_counter() - t0

    print(f"--- {label} ({strategy.upper()}) ---")
    print_grid(grid, path, start, goal)

    if path:
        print(f"Bin restocked      : YES")
        print(f"Steps taken         : {len(path) - 1}")
        print(f"Path taken          : {path}")
    else:
        print("Bin restocked      : NO (no reachable path)")
        print("Steps taken         : -")
        print("Path taken          : -")
    print(f"Time taken          : {elapsed:.6f} seconds")
    print()
    return path, elapsed


# ---- MAIN ----
grid, start, goal = build_sample_warehouse()
run_agent(grid, start, goal, "bfs", label="Warehouse Layout 1")
run_agent(grid, start, goal, "dfs", label="Warehouse Layout 1")

grid2 = [
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 0],
    [0, 0, 0, 0, 1, 0],
    [0, 1, 1, 0, 1, 0],
    [0, 1, 0, 0, 0, 0],
    [0, 1, 0, 1, 1, 0],
]
run_agent(grid2, start, goal, "bfs", label="Warehouse Layout 2 (rack moved)")
run_agent(grid2, start, goal, "dfs", label="Warehouse Layout 2 (rack moved)")