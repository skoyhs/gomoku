class Board:
    def __init__(self, size=15):
        self.size = size
        self.board = [[0 for _ in range(size)] for _ in range(size)]
        # 0表示空，1表示黑子，2表示白子

    def place_stone(self, row, col, stone_type):
        """在指定位置放置棋子"""
        if 0 <= row < self.size and 0 <= col < self.size and self.board[row][col] == 0:
            self.board[row][col] = stone_type
            return True
        return False

    def check_win(self, row, col, stone_type):
        """检查是否有五子连珠"""
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]  # 横、竖、右斜、左斜

        for dr, dc in directions:
            count = 1  # 当前位置已经有一个棋子

            # 正向检查
            r, c = row + dr, col + dc
            while (
                0 <= r < self.size
                and 0 <= c < self.size
                and self.board[r][c] == stone_type
            ):
                count += 1
                r += dr
                c += dc

            # 反向检查
            r, c = row - dr, col - dc
            while (
                0 <= r < self.size
                and 0 <= c < self.size
                and self.board[r][c] == stone_type
            ):
                count += 1
                r -= dr
                c -= dc

            if count >= 5:
                return True

        return False

    def is_full(self):
        """检查棋盘是否已满"""
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row][col] == 0:
                    return False
        return True
