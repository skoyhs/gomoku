import random
import copy
import time


class AI:
    """基础AI类"""

    def __init__(self, board_size=15):
        self.board_size = board_size
        self.name = "AI"

    def get_move(self, game):
        """获取AI的落子位置，由子类实现"""
        pass


class RandomAI(AI):
    """初级AI - 随机落子"""

    def __init__(self, board_size=15):
        super().__init__(board_size)
        self.name = "初级AI"

    def get_move(self, game):
        """随机选择一个空位落子"""
        empty_positions = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if game.board.board[row][col] == 0:
                    empty_positions.append((row, col))

        # 如果有空位，随机选择一个
        if empty_positions:
            return random.choice(empty_positions)
        return None


class PatternAI(AI):
    """中级AI - 模式匹配"""

    def __init__(self, board_size=15):
        super().__init__(board_size)
        self.name = "中级AI"

        # 定义评分模式
        # 格式: (连子数, 两端是否开放, 分数)
        # 两端开放: 2表示两端都开放, 1表示一端开放, 0表示两端都不开放
        self.patterns = [
            (5, 0, 100000),  # 五连(胜利)
            (4, 2, 10000),  # 活四
            (4, 1, 1000),  # 冲四
            (3, 2, 1000),  # 活三
            (3, 1, 100),  # 眠三
            (2, 2, 100),  # 活二
            (2, 1, 10),  # 眠二
            (1, 2, 10),  # 活一
            (1, 1, 1),  # 眠一
        ]

    def evaluate_position(self, board, row, col, player):
        """评估特定位置的分数"""
        if board[row][col] != 0:
            return 0  # 如果位置已经有棋子，返回0分

        # 设置方向: 水平、垂直、两个对角线
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        total_score = 0

        # 在每个方向上评估棋形
        for dr, dc in directions:
            # 评估我方棋形
            my_score = self._evaluate_direction(board, row, col, dr, dc, player)
            total_score += my_score

            # 评估对手棋形(防守分)，给予较高权重
            opponent = 3 - player  # 1->2, 2->1
            opponent_score = self._evaluate_direction(board, row, col, dr, dc, opponent)

            # 如果对手有威胁，增加此位置的防守价值
            if opponent_score >= 1000:  # 对手有冲四或活三
                total_score += opponent_score * 0.8  # 防守权重

        return total_score

    def _evaluate_direction(self, board, row, col, dr, dc, player):
        """评估某一方向上的棋形"""
        count = 1  # 连子数(包括当前位置)
        open_ends = 0  # 开放端数

        # 检查一个方向
        r, c = row + dr, col + dc
        while (
            0 <= r < self.board_size
            and 0 <= c < self.board_size
            and board[r][c] == player
        ):
            count += 1
            r += dr
            c += dc

        # 检查这个方向的端点是否开放
        if 0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == 0:
            open_ends += 1

        # 检查相反方向
        r, c = row - dr, col - dc
        while (
            0 <= r < self.board_size
            and 0 <= c < self.board_size
            and board[r][c] == player
        ):
            count += 1
            r -= dr
            c -= dc

        # 检查相反方向的端点是否开放
        if 0 <= r < self.board_size and 0 <= c < self.board_size and board[r][c] == 0:
            open_ends += 1

        # 根据模式评分
        for pattern_count, pattern_open_ends, score in self.patterns:
            if count == pattern_count and open_ends >= pattern_open_ends:
                return score

        return 0

    def get_move(self, game):
        """根据棋形评分选择最佳位置"""
        best_score = -1
        best_move = None

        # 复制游戏板以评估
        board = copy.deepcopy(game.board.board)

        # 评估所有空位
        for row in range(self.board_size):
            for col in range(self.board_size):
                if board[row][col] == 0:
                    score = self.evaluate_position(board, row, col, game.current_player)
                    if score > best_score:
                        best_score = score
                        best_move = (row, col)

        # 如果没有找到好的位置，随机选择
        if best_move is None:
            empty_positions = []
            for row in range(self.board_size):
                for col in range(self.board_size):
                    if board[row][col] == 0:
                        empty_positions.append((row, col))
            if empty_positions:
                best_move = random.choice(empty_positions)

        return best_move


class EnhancedMinimaxAI(AI):
    """高级AI - 使用优化的Minimax算法"""

    def __init__(self, board_size=15, depth=2):
        super().__init__(board_size)
        self.name = "高级AI"
        self.depth = depth
        self.pattern_ai = PatternAI(board_size)
        self.transposition_table = {}  # 置换表，存储已搜索过的状态

    def get_move(self, game):
        """使用Minimax算法选择最佳位置"""
        self.transposition_table = {}  # 重置置换表

        # 复制游戏状态
        board = copy.deepcopy(game.board.board)
        player = game.current_player

        # 优化: 只考虑棋子周围的空位
        candidates = self._get_candidate_positions(board)
        if not candidates:
            # 如果是空棋盘，就下中央位置
            return (self.board_size // 2, self.board_size // 2)

        # 根据启发式评估对候选位置进行排序
        candidates = sorted(
            candidates,
            key=lambda pos: self._get_position_heuristic(board, pos[0], pos[1], player),
            reverse=True,
        )

        best_score = float("-inf")
        best_move = None
        alpha = float("-inf")
        beta = float("inf")

        # 对每个候选位置应用Minimax
        for row, col in candidates[: min(len(candidates), 10)]:  # 只考虑最佳的10个位置
            if board[row][col] == 0:
                board[row][col] = player
                score = self._minimax(board, self.depth - 1, False, player, alpha, beta)
                board[row][col] = 0  # 撤销移动

                if score > best_score:
                    best_score = score
                    best_move = (row, col)
                alpha = max(alpha, best_score)

        # 如果minimax没找到好的位置，使用PatternAI
        if best_move is None:
            return self.pattern_ai.get_move(game)

        return best_move

    def _get_position_heuristic(self, board, row, col, player):
        """获取位置的启发式价值，用于排序"""
        if board[row][col] != 0:
            return float("-inf")  # 已经有棋子的位置

        # 使用PatternAI的评估函数
        score = self.pattern_ai.evaluate_position(board, row, col, player)

        # 增加靠近中心的位置的分数
        center = self.board_size // 2
        distance_from_center = abs(row - center) + abs(col - center)
        centrality_score = (self.board_size - distance_from_center) * 5

        return score + centrality_score

    def _get_candidate_positions(self, board):
        """获取候选位置(棋子周围的空位)"""
        candidates = set()

        # 寻找已有棋子
        has_pieces = False
        for row in range(self.board_size):
            for col in range(self.board_size):
                if board[row][col] != 0:
                    has_pieces = True
                    # 添加周围的空位作为候选
                    for dr in range(-2, 3):
                        for dc in range(-2, 3):
                            r, c = row + dr, col + dc
                            if (
                                0 <= r < self.board_size
                                and 0 <= c < self.board_size
                                and board[r][c] == 0
                            ):
                                candidates.add((r, c))

        # 如果棋盘为空，返回中心位置
        if not has_pieces:
            mid = self.board_size // 2
            return [(mid, mid)]

        return list(candidates)

    def _board_to_key(self, board):
        """将棋盘转换为可哈希的键值(用于置换表)"""
        return "".join("".join(str(cell) for cell in row) for row in board)

    def _minimax(self, board, depth, is_maximizing, player, alpha, beta):
        """Minimax算法实现，带Alpha-Beta剪枝和置换表"""
        opponent = 3 - player  # 1->2, 2->1

        # 生成棋盘的键
        board_key = self._board_to_key(board)

        # 查找置换表
        if board_key in self.transposition_table:
            stored_depth, stored_value = self.transposition_table[board_key]
            if stored_depth >= depth:
                return stored_value

        # 判断终止条件
        if depth == 0:
            eval_score = self._evaluate_board(board, player)
            self.transposition_table[board_key] = (depth, eval_score)
            return eval_score

        # 获取最佳候选位置
        candidates = self._get_candidate_positions(board)

        # 根据启发式排序候选位置(提高剪枝效率)
        if is_maximizing:
            candidates = sorted(
                candidates,
                key=lambda pos: self._get_position_heuristic(
                    board, pos[0], pos[1], player
                ),
                reverse=True,
            )
        else:
            candidates = sorted(
                candidates,
                key=lambda pos: self._get_position_heuristic(
                    board, pos[0], pos[1], opponent
                ),
                reverse=True,
            )

        if is_maximizing:
            max_eval = float("-inf")
            for row, col in candidates:
                if board[row][col] == 0:
                    board[row][col] = player
                    eval_score = self._minimax(
                        board, depth - 1, False, player, alpha, beta
                    )
                    board[row][col] = 0
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break  # Beta剪枝

            # 存储结果到置换表
            self.transposition_table[board_key] = (depth, max_eval)
            return max_eval
        else:
            min_eval = float("inf")
            for row, col in candidates:
                if board[row][col] == 0:
                    board[row][col] = opponent
                    eval_score = self._minimax(
                        board, depth - 1, True, player, alpha, beta
                    )
                    board[row][col] = 0
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break  # Alpha剪枝

            # 存储结果到置换表
            self.transposition_table[board_key] = (depth, min_eval)
            return min_eval

    def _evaluate_board(self, board, player):
        """评估整个棋盘状态"""
        opponent = 3 - player

        # 检查是否有胜者
        for row in range(self.board_size):
            for col in range(self.board_size):
                if board[row][col] == player:
                    # 检查水平、垂直、对角线方向是否有五连珠
                    for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                        count = 1
                        for i in range(1, 5):
                            r, c = row + dr * i, col + dc * i
                            if (
                                0 <= r < self.board_size
                                and 0 <= c < self.board_size
                                and board[r][c] == player
                            ):
                                count += 1
                            else:
                                break
                        if count >= 5:
                            return 100000  # 胜利
                elif board[row][col] == opponent:
                    # 检查对手是否有五连珠
                    for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                        count = 1
                        for i in range(1, 5):
                            r, c = row + dr * i, col + dc * i
                            if (
                                0 <= r < self.board_size
                                and 0 <= c < self.board_size
                                and board[r][c] == opponent
                            ):
                                count += 1
                            else:
                                break
                        if count >= 5:
                            return -100000  # 失败

        # 评估双方的形势
        my_score = 0
        opp_score = 0

        # 快速模式匹配：统计各种棋形
        for row in range(self.board_size):
            for col in range(self.board_size):
                if board[row][col] == 0:  # 空位
                    # 评估如果我方下在这里
                    my_score += (
                        self.pattern_ai.evaluate_position(board, row, col, player) * 0.8
                    )

                    # 评估如果对手下在这里
                    opp_score += (
                        self.pattern_ai.evaluate_position(board, row, col, opponent)
                        * 0.7
                    )

        # 返回综合评分，优先考虑防守
        return my_score - opp_score * 1.2  # 给对手的威胁更高的权重


def get_ai_by_level(level, board_size=15):
    """根据难度级别获取相应的AI实例"""
    if level == 1:
        return RandomAI(board_size)
    elif level == 2:
        return PatternAI(board_size)
    elif level == 3:
        return EnhancedMinimaxAI(board_size)
    else:
        return RandomAI(board_size)  # 默认使用随机AI
