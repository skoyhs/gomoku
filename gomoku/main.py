import pygame
import sys
from game import Game
import os
from sgf import get_sgf_files, parse_sgf, get_game_summary, create_history_record
from ai import get_ai_by_level

# 初始化pygame
pygame.init()

# 游戏常量
SCREEN_SIZE = 800
BOARD_SIZE = 15
GRID_SIZE = SCREEN_SIZE // (BOARD_SIZE + 1)
STONE_RADIUS = GRID_SIZE // 2 - 2
FONT_SIZE = 18
BUTTON_HEIGHT = 40
INFO_BAR_HEIGHT = 100  # 增加底部信息栏高度，容纳多个按钮

# 历史记录常量 - 使用相对路径
HISTORY_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "history"
)  # 相对于当前文件的history目录
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)  # 确保历史记录目录存在
LIST_ITEM_HEIGHT = 60  # 历史记录列表项高度

# 界面状态
GAME_SCREEN = 0  # 游戏主界面
HISTORY_SCREEN = 1  # 历史记录界面
REPLAY_SCREEN = 2  # 棋谱回放界面
AI_SELECT_SCREEN = 3  # AI选择界面

# 颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BOARD_COLOR = (222, 184, 135)
GRID_COLOR = (0, 0, 0)
INFO_COLOR = (50, 50, 50)
BUTTON_COLOR = (180, 180, 180)
BUTTON_HOVER_COLOR = (150, 150, 150)
BUTTON_TEXT_COLOR = (0, 0, 0)

# 创建游戏窗口
screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE + INFO_BAR_HEIGHT))
pygame.display.set_caption("五子棋")

# 加载中文字体
try:
    # 尝试加载系统中文字体
    font_paths = [
        "C:/Windows/Fonts/simhei.ttf",  # Windows黑体
        "C:/Windows/Fonts/msyh.ttc",  # Windows微软雅黑
        "/System/Library/Fonts/PingFang.ttc",  # macOS
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
    ]

    font = None
    for path in font_paths:
        if os.path.exists(path):
            font = pygame.font.Font(path, FONT_SIZE)
            break

    # 如果没有找到中文字体，使用默认字体
    if font is None:
        font = pygame.font.SysFont(None, FONT_SIZE)
        print("警告：未找到中文字体，可能无法正确显示中文")
except Exception as e:
    print(f"加载字体出错: {e}")
    font = pygame.font.SysFont(None, FONT_SIZE)


# 按钮类
class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.hovered = False

    def draw(self):
        color = BUTTON_HOVER_COLOR if self.hovered else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)  # 边框

        text_surface = font.render(self.text, True, BUTTON_TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)
        return self.hovered

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# 历史记录列表项类
class HistoryListItem:
    def __init__(self, x, y, width, height, game_info):
        self.game_info = game_info
        self.hovered = False

        # 创建要显示的文本行
        self.text_lines = []
        # 确保日期显示精确到分钟
        if "time" in self.game_info and self.game_info["time"]:
            self.text_lines.append(
                f"日期: {self.game_info['date']} {self.game_info['time']}"
            )
        else:
            self.text_lines.append(f"日期: {self.game_info['date']}")
        self.text_lines.append(
            f"{self.game_info['black']} VS {self.game_info['white']}"
        )
        self.text_lines.append(f"结果: {self.game_info['result']}")
        self.text_lines.append(f"总步数: {self.game_info['total_moves']}")

        # 计算文本行高度
        line_height = 20  # 每行文本的基本高度
        padding = 10  # 上下边距
        line_spacing = 5  # 行间距

        # 计算所需总高度
        total_height = (
            padding * 2
            + len(self.text_lines) * line_height
            + (len(self.text_lines) - 1) * line_spacing
        )

        # 创建矩形
        self.rect = pygame.Rect(x, y, width, total_height)
        self.line_height = line_height
        self.line_spacing = line_spacing
        self.padding = padding

    def draw(self):
        # 绘制背景
        color = BUTTON_HOVER_COLOR if self.hovered else WHITE
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 1)  # 边框

        # 逐行绘制文本
        for i, line in enumerate(self.text_lines):
            y_offset = (
                self.rect.y + self.padding + i * (self.line_height + self.line_spacing)
            )
            text_surface = font.render(line, True, BLACK)
            screen.blit(text_surface, (self.rect.x + 10, y_offset))

    def is_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)
        return self.hovered

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


def draw_board():
    """绘制棋盘"""
    screen.fill(BOARD_COLOR)

    # 绘制网格线
    for i in range(BOARD_SIZE):
        # 横线
        pygame.draw.line(
            screen,
            GRID_COLOR,
            (GRID_SIZE, (i + 1) * GRID_SIZE),
            (SCREEN_SIZE - GRID_SIZE, (i + 1) * GRID_SIZE),
        )
        # 竖线
        pygame.draw.line(
            screen,
            GRID_COLOR,
            ((i + 1) * GRID_SIZE, GRID_SIZE),
            ((i + 1) * GRID_SIZE, SCREEN_SIZE - GRID_SIZE),
        )

    # 绘制五个小黑点（天元和四星）
    dots = [(3, 3), (3, 11), (11, 3), (11, 11), (7, 7)]
    for col, row in dots:
        pygame.draw.circle(
            screen, BLACK, ((col + 1) * GRID_SIZE, (row + 1) * GRID_SIZE), 5
        )


def draw_stones(game):
    """绘制棋子"""
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            stone = game.board.board[row][col]
            if stone != 0:
                # 绘制棋子
                color = BLACK if stone == 1 else WHITE
                pygame.draw.circle(
                    screen,
                    color,
                    ((col + 1) * GRID_SIZE, (row + 1) * GRID_SIZE),
                    STONE_RADIUS,
                )
                # 绘制白棋边框
                if stone == 2:
                    pygame.draw.circle(
                        screen,
                        BLACK,
                        ((col + 1) * GRID_SIZE, (row + 1) * GRID_SIZE),
                        STONE_RADIUS,
                        1,
                    )

                # 显示棋子序号
                move_number = game.move_numbers[row][col]
                if move_number > 0:
                    # 根据棋子颜色选择对比色
                    text_color = WHITE if stone == 1 else BLACK
                    # 创建序号文本
                    number_text = font.render(str(move_number), True, text_color)
                    # 计算文本位置(居中)
                    text_rect = number_text.get_rect(
                        center=((col + 1) * GRID_SIZE, (row + 1) * GRID_SIZE)
                    )
                    # 绘制序号
                    screen.blit(number_text, text_rect)


def draw_game_info(game, is_ai_mode=False, ai_player=None, ai_thinking=False):
    """绘制游戏信息"""
    info_bar = pygame.Rect(0, SCREEN_SIZE, SCREEN_SIZE, INFO_BAR_HEIGHT)
    pygame.draw.rect(screen, WHITE, info_bar)

    # 绘制当前状态信息
    if game.game_over:
        if game.winner:
            if game.resigned_player:
                # 显示认输信息
                player_str = "黑棋" if game.resigned_player == 1 else "白棋"
                winner_str = "白棋" if game.resigned_player == 1 else "黑棋"
                status_text = f"游戏结束！{player_str}认输，{winner_str}获胜！"
            else:
                status_text = (
                    "游戏结束！" + ("黑棋" if game.winner == 1 else "白棋") + "获胜！"
                )
        else:
            status_text = "游戏结束！平局！"
    else:
        status_text = "当前回合：" + ("黑棋" if game.current_player == 1 else "白棋")

        # 如果AI正在思考，显示思考状态
        if is_ai_mode and ai_thinking and game.current_player == 2:
            status_text += " (AI思考中...)"

    # 添加回合数显示
    turn_text = f"回合数：{game.turn_count}"

    # 添加悔棋信息显示
    undo_text = ""
    if game.last_undo_player is not None:
        undo_text = ("黑棋" if game.last_undo_player == 1 else "白棋") + "悔棋"

    # 渲染文本
    status_surface = font.render(status_text, True, INFO_COLOR)
    turn_surface = font.render(turn_text, True, INFO_COLOR)

    # 放置文本 - 将文本放在左侧
    screen.blit(status_surface, (20, SCREEN_SIZE + 20))
    screen.blit(turn_surface, (20, SCREEN_SIZE + 50))

    # 显示悔棋信息
    if undo_text:
        undo_surface = font.render(undo_text, True, INFO_COLOR)
        screen.blit(undo_surface, (20, SCREEN_SIZE + 80))

    # 如果是人机对战模式，显示AI名称
    if is_ai_mode and ai_player:
        ai_text = font.render(f"对战: {ai_player.name}", True, INFO_COLOR)
        screen.blit(ai_text, (20, SCREEN_SIZE + 80))


def draw_history_screen(history_items, back_button, scroll_offset=0):
    """绘制历史记录界面"""
    screen.fill(WHITE)

    # 绘制标题
    title = font.render("历史对局记录", True, BLACK)
    screen.blit(title, (SCREEN_SIZE // 2 - title.get_width() // 2, 20))

    # 绘制历史记录列表
    list_area = pygame.Rect(50, 60, SCREEN_SIZE - 100, SCREEN_SIZE - 100)
    pygame.draw.rect(screen, (240, 240, 240), list_area)
    pygame.draw.rect(screen, BLACK, list_area, 1)

    # 裁剪列表区域，防止项目绘制超出
    screen.set_clip(list_area)

    # 绘制列表项
    y_pos = 60 + scroll_offset
    for item in history_items:
        if list_area.y - LIST_ITEM_HEIGHT < y_pos < list_area.bottom:
            item.rect.y = y_pos
            item.draw()
        y_pos += item.rect.height + 5

    # 重置裁剪区域
    screen.set_clip(None)

    # 绘制返回按钮
    back_button.draw()


def draw_replay_screen(
    game, replay_info, back_button, step_prev_button, step_next_button, auto_play_button
):
    """绘制回放界面"""
    draw_board()
    draw_stones(game)

    # 绘制回放信息
    info_bar = pygame.Rect(0, SCREEN_SIZE, SCREEN_SIZE, INFO_BAR_HEIGHT)
    pygame.draw.rect(screen, WHITE, info_bar)

    # 显示当前回放信息
    info_text = f"回放: {replay_info['black']} VS {replay_info['white']} | 步数: {replay_info['current_step']}/{replay_info['total_moves']}"
    info_surface = font.render(info_text, True, INFO_COLOR)
    screen.blit(info_surface, (20, SCREEN_SIZE + 20))

    # 显示对局结果
    result_text = f"对局结果: {replay_info['result']}"
    result_surface = font.render(result_text, True, INFO_COLOR)
    screen.blit(result_surface, (20, SCREEN_SIZE + 50))

    # 绘制控制按钮
    back_button.draw()
    step_prev_button.draw()
    step_next_button.draw()
    auto_play_button.draw()


def draw_ai_select_screen(ai_buttons, back_button):
    """绘制AI难度选择界面"""
    screen.fill(WHITE)

    # 绘制标题
    title = font.render("选择AI难度", True, BLACK)
    screen.blit(title, (SCREEN_SIZE // 2 - title.get_width() // 2, 100))

    # 绘制AI难度按钮
    for button in ai_buttons:
        button.draw()

    # 绘制返回按钮
    back_button.draw()


def load_replay_game(sgf_filepath, step=None):
    """加载回放游戏"""
    info, moves = parse_sgf(sgf_filepath)
    game = Game()
    game.reset()

    # 如果指定了步数，则加载到该步
    max_step = len(moves) if step is None else min(step, len(moves))

    # 加载指定步数的棋子
    for i in range(max_step):
        row, col, player = moves[i]
        game.board.board[row][col] = player
        game.move_numbers[row][col] = i + 1
        game.move_history.append((row, col, player))
        game.turn_count = i + 1

        # 更新当前玩家
        if i == max_step - 1:
            game.current_player = 1 if player == 2 else 2

    return game, info, moves


def main():
    game = Game()
    current_screen = GAME_SCREEN
    history_scroll_offset = 0
    replay_info = None
    replay_game = None
    replay_moves = None
    replay_step = 0
    auto_play = False
    auto_play_timer = 0

    # AI相关变量
    ai_player = None  # 当前AI实例
    is_ai_mode = False  # 是否为人机对战模式
    ai_thinking = False  # AI是否在思考中
    ai_thinking_time = 0  # AI思考时间计时器
    ai_move = None  # AI的落子位置
    ai_thinking_start_time = 0  # AI开始思考的时间

    # 创建按钮 - 调整按钮位置到右侧
    button_width = 80
    button_spacing = 15
    buttons_start_x = SCREEN_SIZE - (button_width * 5 + button_spacing * 4) - 20
    buttons_y = SCREEN_SIZE + 30

    restart_button = Button(
        buttons_start_x + button_width + button_spacing,
        buttons_y,
        button_width,
        BUTTON_HEIGHT,
        "重新开始",
    )

    resign_button = Button(
        buttons_start_x + (button_width + button_spacing) * 2,
        buttons_y,
        button_width,
        BUTTON_HEIGHT,
        "认输",
    )

    undo_button = Button(
        buttons_start_x + (button_width + button_spacing) * 3,
        buttons_y,
        button_width,
        BUTTON_HEIGHT,
        "悔棋",
    )

    history_button = Button(
        buttons_start_x + (button_width + button_spacing) * 4,
        buttons_y,
        button_width,
        BUTTON_HEIGHT,
        "历史记录",
    )

    # 添加AI按钮
    ai_button = Button(
        buttons_start_x, buttons_y, button_width, BUTTON_HEIGHT, "人机对战"
    )

    # 历史记录界面的返回按钮
    back_button = Button(
        SCREEN_SIZE - button_width - 20,
        SCREEN_SIZE + 30,
        button_width,
        BUTTON_HEIGHT,
        "返回",
    )

    # 回放控制按钮
    step_prev_button = Button(
        buttons_start_x, buttons_y, button_width, BUTTON_HEIGHT, "上一步"
    )

    step_next_button = Button(
        buttons_start_x + button_width + button_spacing,
        buttons_y,
        button_width,
        BUTTON_HEIGHT,
        "下一步",
    )

    auto_play_button = Button(
        buttons_start_x + (button_width + button_spacing) * 2,
        buttons_y,
        button_width,
        BUTTON_HEIGHT,
        "自动播放",
    )

    # AI难度选择按钮
    ai_easy_button = Button(
        SCREEN_SIZE // 2 - button_width // 2, 200, button_width, BUTTON_HEIGHT, "初级"
    )

    ai_medium_button = Button(
        SCREEN_SIZE // 2 - button_width // 2,
        200 + BUTTON_HEIGHT + 20,
        button_width,
        BUTTON_HEIGHT,
        "中级",
    )

    ai_hard_button = Button(
        SCREEN_SIZE // 2 - button_width // 2,
        200 + (BUTTON_HEIGHT + 20) * 2,
        button_width,
        BUTTON_HEIGHT,
        "高级",
    )

    ai_buttons = [ai_easy_button, ai_medium_button, ai_hard_button]

    # 游戏按钮组
    game_buttons = [
        restart_button,
        resign_button,
        undo_button,
        history_button,
        ai_button,
    ]

    while True:
        mouse_pos = pygame.mouse.get_pos()
        current_time = pygame.time.get_ticks()

        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    if current_screen == GAME_SCREEN:
                        # 游戏界面按钮点击
                        if restart_button.is_clicked(event.pos):
                            game.reset()
                            is_ai_mode = False  # 重置AI模式
                            ai_thinking = False
                        elif resign_button.is_clicked(event.pos) and not game.game_over:
                            game.resign()
                            ai_thinking = False
                            if is_ai_mode and game.game_over:
                                # 保存AI对战棋谱
                                result = "B+R" if game.winner == 1 else "W+R"
                                ai_name = ai_player.name if ai_player else "AI"
                                create_history_record(
                                    game, HISTORY_DIR, "玩家", ai_name, result
                                )
                        elif undo_button.is_clicked(event.pos) and not game.game_over:
                            if is_ai_mode:
                                # 在AI模式下，需要悔两步棋（玩家和AI的各一步）
                                game.undo()  # 撤销AI的一步
                                game.undo()  # 撤销玩家的一步
                                ai_thinking = False
                            else:
                                game.undo()
                        elif history_button.is_clicked(event.pos):
                            # 切换到历史记录界面
                            current_screen = HISTORY_SCREEN
                            # 加载历史记录
                            sgf_files = get_sgf_files(HISTORY_DIR)
                            history_items = []

                            # 使用动态位置创建历史记录项
                            y_pos = 60  # 起始Y位置
                            for file in sgf_files:
                                summary = get_game_summary(file)
                                item = HistoryListItem(
                                    50, y_pos, SCREEN_SIZE - 100, 0, summary
                                )
                                history_items.append(item)
                                # 更新下一个项目的位置
                                y_pos += item.rect.height + 10
                        elif ai_button.is_clicked(event.pos):
                            # 切换到AI选择界面
                            current_screen = AI_SELECT_SCREEN
                        elif not game.game_over and not ai_thinking:
                            # 棋盘下棋
                            x, y = event.pos
                            if (
                                GRID_SIZE // 2 <= x <= SCREEN_SIZE - GRID_SIZE // 2
                                and GRID_SIZE // 2 <= y <= SCREEN_SIZE - GRID_SIZE // 2
                            ):
                                col = round((x - GRID_SIZE) / GRID_SIZE)
                                row = round((y - GRID_SIZE) / GRID_SIZE)

                                if is_ai_mode and game.current_player == 2:
                                    # 如果是AI回合，不允许玩家下棋
                                    continue

                                if game.make_move(row, col):
                                    # 如果是人机模式且游戏未结束，准备AI下棋
                                    if (
                                        is_ai_mode
                                        and not game.game_over
                                        and game.current_player == 2
                                    ):
                                        # 设置AI思考状态
                                        ai_thinking = True
                                        ai_thinking_start_time = current_time
                                        ai_move = None

                                    # 如果游戏结束，保存棋谱
                                    if game.game_over:
                                        result = (
                                            "B+R"
                                            if game.winner == 1
                                            else "W+R" if game.winner == 2 else "Draw"
                                        )
                                        if is_ai_mode:
                                            ai_name = (
                                                ai_player.name if ai_player else "AI"
                                            )
                                            create_history_record(
                                                game,
                                                HISTORY_DIR,
                                                "玩家",
                                                ai_name,
                                                result,
                                            )
                                        else:
                                            create_history_record(
                                                game,
                                                HISTORY_DIR,
                                                "黑棋",
                                                "白棋",
                                                result,
                                            )

                    elif current_screen == AI_SELECT_SCREEN:
                        # AI选择界面
                        if back_button.is_clicked(event.pos):
                            current_screen = GAME_SCREEN
                        elif ai_easy_button.is_clicked(event.pos):
                            # 选择初级AI
                            ai_player = get_ai_by_level(1)
                            is_ai_mode = True
                            game.reset()
                            current_screen = GAME_SCREEN
                        elif ai_medium_button.is_clicked(event.pos):
                            # 选择中级AI
                            ai_player = get_ai_by_level(2)
                            is_ai_mode = True
                            game.reset()
                            current_screen = GAME_SCREEN
                        elif ai_hard_button.is_clicked(event.pos):
                            # 选择高级AI
                            ai_player = get_ai_by_level(3)
                            is_ai_mode = True
                            game.reset()
                            current_screen = GAME_SCREEN

                    elif current_screen == HISTORY_SCREEN:
                        # 历史记录界面
                        if back_button.is_clicked(event.pos):
                            current_screen = GAME_SCREEN
                        else:
                            # 检查是否点击了历史记录项
                            for item in history_items:
                                if item.is_clicked(event.pos):
                                    # 加载所选棋谱
                                    replay_game, info, moves = load_replay_game(
                                        item.game_info["filepath"]
                                    )
                                    replay_info = {
                                        "black": info.get("PB", "黑棋"),
                                        "white": info.get("PW", "白棋"),
                                        "result": info.get("RE", "未知"),
                                        "total_moves": len(moves),
                                        "current_step": len(moves),
                                    }
                                    replay_moves = moves
                                    replay_step = len(moves)
                                    current_screen = REPLAY_SCREEN
                                    auto_play = False
                                    break

                    elif current_screen == REPLAY_SCREEN:
                        # 回放界面
                        if back_button.is_clicked(event.pos):
                            current_screen = HISTORY_SCREEN
                        elif step_prev_button.is_clicked(event.pos) and replay_step > 0:
                            replay_step -= 1
                            replay_game, _, _ = load_replay_game(
                                item.game_info["filepath"], replay_step
                            )
                            replay_info["current_step"] = replay_step
                            auto_play = False
                        elif (
                            step_next_button.is_clicked(event.pos)
                            and replay_step < replay_info["total_moves"]
                        ):
                            replay_step += 1
                            replay_game, _, _ = load_replay_game(
                                item.game_info["filepath"], replay_step
                            )
                            replay_info["current_step"] = replay_step
                            auto_play = False
                        elif auto_play_button.is_clicked(event.pos):
                            auto_play = not auto_play
                            if auto_play:
                                auto_play_button.text = "暂停播放"
                            else:
                                auto_play_button.text = "自动播放"

                # 鼠标滚轮事件
                elif event.button == 4:  # 向上滚动
                    if current_screen == HISTORY_SCREEN:
                        history_scroll_offset += 20
                elif event.button == 5:  # 向下滚动
                    if current_screen == HISTORY_SCREEN:
                        history_scroll_offset -= 20

        # 处理AI思考和落子
        if (
            current_screen == GAME_SCREEN
            and is_ai_mode
            and ai_thinking
            and not game.game_over
        ):
            # 如果AI尚未计算落子位置
            if ai_move is None:
                # 计算AI落子，可能需要一些时间
                ai_move = ai_player.get_move(game)

            # 确保AI至少"思考"一段时间，即使计算很快
            thinking_time = current_time - ai_thinking_start_time
            min_thinking_time = 800  # 最少思考800毫秒，增强游戏体验

            if thinking_time >= min_thinking_time and ai_move is not None:
                # AI完成思考，执行落子
                row, col = ai_move
                if row is not None and col is not None:
                    game.make_move(row, col)

                # 重置AI状态
                ai_thinking = False
                ai_move = None

                # 如果游戏结束，保存棋谱
                if game.game_over:
                    result = (
                        "B+R"
                        if game.winner == 1
                        else "W+R" if game.winner == 2 else "Draw"
                    )
                    ai_name = ai_player.name if ai_player else "AI"
                    create_history_record(
                        game,
                        HISTORY_DIR,
                        "玩家",
                        ai_name,
                        result,
                    )

        # 更新按钮悬停状态
        if current_screen == GAME_SCREEN:
            for button in game_buttons:
                button.is_hover(mouse_pos)
        elif current_screen == AI_SELECT_SCREEN:
            back_button.is_hover(mouse_pos)
            for button in ai_buttons:
                button.is_hover(mouse_pos)
        elif current_screen == HISTORY_SCREEN:
            back_button.is_hover(mouse_pos)
            for item in history_items:
                item.is_hover(mouse_pos)
        elif current_screen == REPLAY_SCREEN:
            back_button.is_hover(mouse_pos)
            step_prev_button.is_hover(mouse_pos)
            step_next_button.is_hover(mouse_pos)
            auto_play_button.is_hover(mouse_pos)

            # 处理自动播放
            if auto_play and replay_step < replay_info["total_moves"]:
                auto_play_timer += 1
                if auto_play_timer >= 30:  # 大约1秒播放一步
                    replay_step += 1
                    replay_game, _, _ = load_replay_game(
                        item.game_info["filepath"], replay_step
                    )
                    replay_info["current_step"] = replay_step
                    auto_play_timer = 0

                    # 播放完毕时停止自动播放
                    if replay_step >= replay_info["total_moves"]:
                        auto_play = False
                        auto_play_button.text = "自动播放"

        # 更新游戏状态
        if current_screen == GAME_SCREEN:
            game.update()

        # 绘制界面
        if current_screen == GAME_SCREEN:
            draw_board()
            draw_stones(game)
            draw_game_info(game, is_ai_mode, ai_player, ai_thinking)

            # 绘制按钮
            for button in game_buttons:
                button.draw()

        elif current_screen == AI_SELECT_SCREEN:
            draw_ai_select_screen(ai_buttons, back_button)

        elif current_screen == HISTORY_SCREEN:
            draw_history_screen(history_items, back_button, history_scroll_offset)

        elif current_screen == REPLAY_SCREEN:
            draw_replay_screen(
                replay_game,
                replay_info,
                back_button,
                step_prev_button,
                step_next_button,
                auto_play_button,
            )

        pygame.display.flip()

        # 控制帧率
        pygame.time.Clock().tick(30)


if __name__ == "__main__":
    main()
