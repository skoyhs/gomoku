from board import Board


class Game:
    def __init__(self):
        self.board = Board()
        self.current_player = 1  # 1表示黑子，2表示白棋
        self.game_over = False
        self.winner = None
        self.turn_count = 1
        self.move_history = []
        self.resigned_player = None
        self.last_undo_player = None
        self.undo_count = 0
        self.move_numbers = [
            [0 for _ in range(self.board.size)] for _ in range(self.board.size)
        ]
        self.move_count = 0

        # 回放模式相关
        self.replay_mode = False
        self.replay_index = 0
        self.replay_moves = []
        self.replay_info = {}

    def make_move(self, row, col):
        """玩家在指定位置落子"""
        if self.game_over or self.replay_mode:
            return False

        if self.board.place_stone(row, col, self.current_player):
            # 每次有效落子时重置悔棋信息
            self.last_undo_player = None
            self.undo_count = 0

            # 棋子序号递增
            self.move_count += 1
            self.move_numbers[row][col] = self.move_count

            # 记录这一步
            self.move_history.append((row, col, self.current_player))

            # 检查是否获胜
            if self.board.check_win(row, col, self.current_player):
                self.game_over = True
                self.winner = self.current_player
            # 检查是否平局
            elif self.board.is_full():
                self.game_over = True
            else:
                # 切换玩家
                self.current_player = 3 - self.current_player  # 1->2, 2->1
                # 黑棋回合时增加回合计数
                if self.current_player == 1:
                    self.turn_count += 1
            return True
        return False

    def undo(self):
        """悔棋功能 - 撤销上一步"""
        if not self.move_history or self.replay_mode:
            return False

        # 如果游戏已经结束，无法悔棋
        if self.game_over:
            return False

        # 获取最后一步
        last_row, last_col, last_player = self.move_history.pop()

        # 记录悔棋玩家
        self.last_undo_player = last_player
        self.undo_count = 60  # 显示约2秒

        # 清除该位置的棋子序号和棋子
        self.move_numbers[last_row][last_col] = 0
        self.board.board[last_row][last_col] = 0
        self.move_count -= 1

        # 切换回上一个玩家
        self.current_player = last_player

        # 如果是白棋悔棋到黑棋，需要减少回合计数
        if last_player == 1 and len(self.move_history) > 0:
            self.turn_count -= 1

        return True

    def resign(self):
        """当前玩家认输"""
        if not self.game_over and not self.replay_mode:
            self.resigned_player = self.current_player
            self.game_over = True
            self.winner = 3 - self.current_player  # 另一方获胜
            return True
        return False

    def reset(self):
        """重置游戏"""
        self.board = Board()
        self.current_player = 1
        self.game_over = False
        self.winner = None
        self.turn_count = 1
        self.move_history = []
        self.resigned_player = None
        self.last_undo_player = None
        self.undo_count = 0
        self.move_numbers = [
            [0 for _ in range(self.board.size)] for _ in range(self.board.size)
        ]
        self.move_count = 0

        # 退出回放模式
        self.replay_mode = False
        self.replay_index = 0
        self.replay_moves = []
        self.replay_info = {}

    def update(self):
        """每帧更新游戏状态"""
        # 更新悔棋计数器
        if self.undo_count > 0:
            self.undo_count -= 1
            if self.undo_count == 0:
                self.last_undo_player = None

    def start_replay(self, moves, info=None):
        """开始回放模式"""
        self.reset()
        self.replay_mode = True
        self.replay_moves = moves
        self.replay_info = info or {}
        self.replay_index = 0
        return True

    def replay_step_forward(self):
        """回放模式下前进一步"""
        if not self.replay_mode or self.replay_index >= len(self.replay_moves):
            return False

        row, col, player = self.replay_moves[self.replay_index]
        self.board.board[row][col] = player
        self.move_count += 1
        self.move_numbers[row][col] = self.move_count
        self.replay_index += 1

        # 更新当前玩家
        if self.replay_index < len(self.replay_moves):
            self.current_player = (
                3 - self.replay_moves[self.replay_index - 1][2]
            )  # 下一手是对方下
        else:
            # 回放结束
            self.current_player = 3 - self.replay_moves[-1][2]
            if "RE" in self.replay_info:
                if "B+" in self.replay_info["RE"]:
                    self.winner = 1
                elif "W+" in self.replay_info["RE"]:
                    self.winner = 2
                self.game_over = True

        # 更新回合数
        self.turn_count = (self.replay_index + 1) // 2

        return True

    def replay_step_backward(self):
        """回放模式下后退一步"""
        if not self.replay_mode or self.replay_index <= 0:
            return False

        self.replay_index -= 1
        row, col, _ = self.replay_moves[self.replay_index]
        self.board.board[row][col] = 0
        self.move_numbers[row][col] = 0
        self.move_count -= 1

        # 更新当前玩家
        self.current_player = self.replay_moves[self.replay_index][2]

        # 更新回合数
        self.turn_count = (self.replay_index + 1) // 2

        # 如果之前是游戏结束状态，现在回到了回放中，则清除结束标志
        self.game_over = False
        self.winner = None

        return True

    def replay_to_start(self):
        """回到回放开始"""
        if not self.replay_mode:
            return False

        while self.replay_index > 0:
            self.replay_step_backward()

        return True

    def replay_to_end(self):
        """跳到回放结束"""
        if not self.replay_mode:
            return False

        while self.replay_index < len(self.replay_moves):
            self.replay_step_forward()

        return True

    def get_result_string(self):
        """获取比赛结果字符串，用于SGF记录"""
        if not self.game_over:
            return ""

        if self.winner == 1:
            return "B+R" if self.resigned_player == 2 else "B+"
        elif self.winner == 2:
            return "W+R" if self.resigned_player == 1 else "W+"
        else:
            return "Draw"  # 平局
