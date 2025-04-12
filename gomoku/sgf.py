import os
from datetime import datetime
import re


def create_sgf(game, black_name="黑棋", white_name="白棋", result=""):
    """根据游戏记录创建SGF格式的棋谱"""
    # 基本信息
    sgf = "(;GM[2]FF[4]SZ[15]\n"  # GM[2]表示五子棋
    sgf += f"DT[{datetime.now().strftime('%Y-%m-%d')}]\n"
    sgf += f"PB[{black_name}]\n"
    sgf += f"PW[{white_name}]\n"

    # 游戏结果
    if result:
        sgf += f"RE[{result}]\n"

    # 着手记录
    for move in game.move_history:
        row, col, player = move
        # 将行列转换为SGF坐标(字母表示)
        sgf_col = chr(ord("a") + col)
        sgf_row = chr(ord("a") + row)

        if player == 1:  # 黑棋
            sgf += f";B[{sgf_col}{sgf_row}]"
        else:  # 白棋
            sgf += f";W[{sgf_col}{sgf_row}]"

    sgf += ")"
    return sgf


def save_sgf(sgf_content, filename):
    """保存SGF内容到文件"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(sgf_content)
    return os.path.abspath(filename)


def parse_sgf(sgf_file):
    """解析SGF文件，返回游戏信息和落子序列"""
    with open(sgf_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 解析基本信息
    info = {}
    for key in ["DT", "PB", "PW", "RE"]:
        start = content.find(f"{key}[") + len(key) + 1
        if start > len(key):
            end = content.find("]", start)
            if end > start:
                info[key] = content[start:end]

    # 解析落子序列
    moves = []
    # 提取所有的B[xx]和W[xx]
    pattern = r";([BW])\[([a-o])([a-o])\]"
    for match in re.finditer(pattern, content):
        player = 1 if match.group(1) == "B" else 2
        col = ord(match.group(2)) - ord("a")
        row = ord(match.group(3)) - ord("a")
        moves.append((row, col, player))

    return info, moves


def get_sgf_files(directory):
    """获取目录下所有的SGF文件"""
    if not os.path.exists(directory):
        os.makedirs(directory)

    files = []
    for file in os.listdir(directory):
        if file.endswith(".sgf"):
            files.append(os.path.join(directory, file))

    # 按修改日期排序，最新的在前
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return files


def generate_sgf_filename(directory, black_name="黑棋", white_name="白棋"):
    """生成带有时间戳的唯一SGF文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 替换可能在文件名中造成问题的字符
    black_name = re.sub(r'[\\/*?:"<>|]', "", black_name)
    white_name = re.sub(r'[\\/*?:"<>|]', "", white_name)

    filename = f"{timestamp}_{black_name}_VS_{white_name}.sgf"
    return os.path.join(directory, filename)


def get_game_summary(sgf_file):
    """获取SGF文件的摘要信息，用于历史记录显示"""
    info, moves = parse_sgf(sgf_file)

    # 提取基本信息
    date = info.get("DT", "未知日期")
    black = info.get("PB", "黑棋")
    white = info.get("PW", "白棋")
    result = info.get("RE", "未知结果")

    # 计算总手数
    total_moves = len(moves)

    # 获取文件的修改时间，精确到分钟
    mod_time = datetime.fromtimestamp(os.path.getmtime(sgf_file)).strftime(
        "%Y-%m-%d %H:%M"
    )

    # 从修改时间中提取时间部分
    time_part = mod_time.split(" ")[1] if " " in mod_time else ""

    return {
        "filename": os.path.basename(sgf_file),
        "filepath": sgf_file,
        "date": date,
        "time": time_part,  # 添加时间字段，精确到分钟
        "black": black,
        "white": white,
        "result": result,
        "total_moves": total_moves,
        "modified": mod_time,
    }


def create_history_record(
    game, directory, black_name="黑棋", white_name="白棋", result=""
):
    """创建并保存对局记录，返回保存的文件路径"""
    # 确保目录存在
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 创建SGF内容
    sgf_content = create_sgf(game, black_name, white_name, result)

    # 生成文件名并保存
    filename = generate_sgf_filename(directory, black_name, white_name)
    return save_sgf(sgf_content, filename)
