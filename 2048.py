import pygame
import random
import sys

# 初始化pygame
pygame.init()

# 游戏常量
SIZE = 600
GRID_SIZE = (SIZE*0.9) // 4 + 2
GRID_GAP = 10
BACKGROUND_COLOR = (187, 173, 160)
EMPTY_CELL_COLOR = (205, 193, 180)
FONT = pygame.font.SysFont("SimHei", 40)
FONT_SMALL = pygame.font.SysFont("SimHei", 20)

# 颜色映射表
COLOR_MAP = {
    0: (205, 193, 180),
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
    4096: (237, 194, 46),
    8192: (237, 194, 46),
}

# 数字颜色映射表
TEXT_COLOR_MAP = {
    0: (0, 0, 0),
    2: (119, 110, 101),
    4: (119, 110, 101),
    8: (249, 246, 242),
    16: (249, 246, 242),
    32: (249, 246, 242),
    64: (249, 246, 242),
    128: (249, 246, 242),
    256: (249, 246, 242),
    512: (249, 246, 242),
    1024: (249, 246, 242),
    2048: (249, 246, 242),
    4096: (249, 246, 242),
    8192: (249, 246, 242),
}

# ---------------------- 1. 双向链表节点类(存储单个表格状态) ----------------------
class HistoryNode:
    def __init__(self, grid, score):
        self.grid = grid  # 存储当前表格状态(深拷贝后的4x4列表)
        self.score = score  # 对应状态的分数
        self.prev = None  # 前驱节点(上一个状态)
        self.next = None  # 后继节点(下一个状态)

# ---------------------- 2. 双向链表管理类(控制历史记录) ----------------------
class HistoryList:
    def __init__(self, max_length=6):
        self.max_length = max_length  # 最大记录数(不超过6个)
        self.head = None  # 链表头(最早的状态)
        self.tail = None  # 链表尾(最近的状态)
        self.length = 0  # 当前记录数

    def add_node(self, grid, score):
        print("test:add_node")
        """添加新节点(当前表格状态),超过最大长度则删除最早的节点"""
        # 深拷贝网格,避免引用问题
        grid_copy = [row.copy() for row in grid]
        new_node = HistoryNode(grid_copy, score)

        # 链表为空时,头和尾都指向新节点
        if self.length == 0:
            self.head = new_node
            self.tail = new_node
        else:
            # 新节点接在尾部(最近的状态在尾部)
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node

        self.length += 1

        # 超过最大长度,删除最早的节点(头部节点)
        if self.length > self.max_length:
            self.remove_head()

    def remove_head(self):
        print("test:remove_head")
        """删除最早的节点(头部)"""
        if self.length == 0:
            return
        # 只有一个节点时,清空链表
        if self.length == 1:
            self.head = None
            self.tail = None
        else:
            # 头部后移,删除原头部
            new_head = self.head.next
            new_head.prev = None
            self.head = new_head

        self.length -= 1

    def get_latest_node(self):
        print("test:get_latest_node")
        """获取最近的节点(尾部),用于回退"""
        return self.tail if self.length > 0 else None

    def remove_tail(self):
        print("test:remove_tail")
        """删除最近的节点(尾部),回退后移除已回退的状态"""
        if self.length == 0:
            return
        # 只有一个节点时,清空链表
        if self.length == 1:
            self.head = None
            self.tail = None
        else:
            # 尾部前移,删除原尾部
            new_tail = self.tail.prev
            new_tail.next = None
            self.tail = new_tail

        self.length -= 1
    def get_length(self):
        # print("test:get_length")
        """获取当前链表长度"""
        return self.length

# ---------------------- 3. 游戏主类 ----------------------
class Game2048:
    def __init__(self):
        self.screen = pygame.display.set_mode((SIZE, SIZE + 100))
        pygame.display.set_caption("2048 (update roll back)")
        # 动画相关属性
        self.is_animating = False  # 是否正在播放动画
        self.animation_progress = 0  # 动画进度（0=开始，1=结束）
        self.animation_speed = 0.1  # 动画时长（秒），值越小越快
        self.animation_frames = int(self.animation_speed * 60)  # 总帧数（按60FPS计算）
        self.start_positions = {}  # 移动前的方块位置：{(值): [(初始行, 初始列)]}
        self.target_positions = {}  # 移动后的方块位置：{(值): [(目标行, 目标列)]}
        self.reset_game()

    def reset_game(self):
        print("test:reset_game")
        """重置游戏状态,初始化双向链表"""
        self.grid = [[0 for _ in range(4)] for _ in range(4)]
        self.score = 0
        self.add_new_tile()
        self.add_new_tile()
        self.game_over = False
        self.win = False
        # 初始化双向链表(最大6个记录)
        self.history_list = HistoryList(max_length=6)
        # 初始状态存入链表
        self.save_current_state()

    def save_current_state(self):
        print("test:save_current_state")
        """记录当前表格状态(调用此函数,将当前grid和score存入双向链表)"""
        self.history_list.add_node(self.grid, self.score)

    def undo_to_latest(self):
        print("test:undo_to_latest")
        """回退到最近记录的状态:获取尾部节点,更新grid和score,删除该尾部节点"""
        if self.history_list.get_length() == 6:  # 确保有可回退的状态
            self.history_list.remove_tail()
            latest_node = self.history_list.get_latest_node()
        else:
            latest_node = self.history_list.get_latest_node()
        if latest_node:
                # 更新当前游戏状态为最近记录的状态
                self.grid = [row.copy() for row in latest_node.grid]
                self.score = latest_node.score
                # 删除已回退的节点(避免重复回退同一状态)
                self.history_list.remove_tail()
                # 回退后重新检查游戏状态
                self.game_over = False
                self.win = self.check_win()

    def add_new_tile(self):
        print("test:add_new_tile")
        """在空白位置添加2或4"""
        empty_cells = [(i, j) for i in range(4) for j in range(4) if self.grid[i][j] == 0]
        if empty_cells:
            i, j = random.choice(empty_cells)
            self.grid[i][j] = 2 if random.random() < 0.9 else 4
    def _get_current_positions(self):
        """获取当前网格中所有非空方块的位置，返回格式：{(值): [(行1, 列1), (行2, 列2)]}"""
        positions = {}
        for row in range(4):
            for col in range(4):
                value = self.grid[row][col]
                if value != 0:
                    if value not in positions:
                        positions[value] = []
                    positions[value].append((row, col))
        return positions
    
    # ---------------------- 移动方法(保持单次合并逻辑) ----------------------
    def move_left(self):
        moved = False
        # 【新增】记录移动前的初始位置
        self.start_positions = self._get_current_positions()
        
        # 原移动逻辑不变
        for row in range(4):
            new_row = [num for num in self.grid[row] if num != 0]
            merged_row = []
            i = 0
            while i < len(new_row):
                if i + 1 < len(new_row) and new_row[i] == new_row[i+1]:
                    merged_num = new_row[i] * 2
                    merged_row.append(merged_num)
                    self.score += merged_num
                    i += 2
                    moved = True
                else:
                    merged_row.append(new_row[i])
                    i += 1
            while len(merged_row) < 4:
                merged_row.append(0)
            if merged_row != self.grid[row]:
                moved = True
            self.grid[row] = merged_row
        
        # 【新增】记录移动后的目标位置，并开启动画
        if moved:
            self.target_positions = self._get_current_positions()
            self.is_animating = True
            self.animation_progress = 0  # 重置进度
        
        return moved

    def move_right(self):
        print("test:move_right")
        moved = False
        # 【新增】记录移动前的初始位置
        self.start_positions = self._get_current_positions()
        # 原移动逻辑不变
        for row in range(4):
            new_row = [num for num in self.grid[row] if num != 0][::-1]
            merged_row = []
            i = 0
            while i < len(new_row):
                if i + 1 < len(new_row) and new_row[i] == new_row[i+1]:
                    merged_num = new_row[i] * 2
                    merged_row.append(merged_num)
                    self.score += merged_num
                    i += 2
                    moved = True
                else:
                    merged_row.append(new_row[i])
                    i += 1
            while len(merged_row) < 4:
                merged_row.append(0)
            merged_row = merged_row[::-1]
            if merged_row != self.grid[row]:
                moved = True
            self.grid[row] = merged_row
        # 【新增】记录移动后的目标位置，并开启动画
        if moved:
            self.target_positions = self._get_current_positions()
            self.is_animating = True
            self.animation_progress = 0  # 重置进度
        return moved

    def move_up(self):
        print("test:move_up")
        moved = False
        # 【新增】记录移动前的初始位置
        self.start_positions = self._get_current_positions()
        # 原移动逻辑不变

        for col in range(4):
            new_col = []
            for row in range(4):
                if self.grid[row][col] != 0:
                    new_col.append(self.grid[row][col])
            merged_col = []
            i = 0
            while i < len(new_col):
                if i + 1 < len(new_col) and new_col[i] == new_col[i+1]:
                    merged_num = new_col[i] * 2
                    merged_col.append(merged_num)
                    self.score += merged_num
                    i += 2
                    moved = True
                else:
                    merged_col.append(new_col[i])
                    i += 1
            while len(merged_col) < 4:
                merged_col.append(0)
            for row in range(4):
                if merged_col[row] != self.grid[row][col]:
                    moved = True
                self.grid[row][col] = merged_col[row]
        # 【新增】记录移动后的目标位置，并开启动画
        if moved:
            self.target_positions = self._get_current_positions()
            self.is_animating = True
            self.animation_progress = 0  # 重置进度
        return moved

    def move_down(self):
        print("test:move_down")
        moved = False
        # 【新增】记录移动前的初始位置
        self.start_positions = self._get_current_positions()
        # 原移动逻辑不变
        for col in range(4):
            new_col = []
            for row in range(3, -1, -1):
                if self.grid[row][col] != 0:
                    new_col.append(self.grid[row][col])
            merged_col = []
            i = 0
            while i < len(new_col):
                if i + 1 < len(new_col) and new_col[i] == new_col[i+1]:
                    merged_num = new_col[i] * 2
                    merged_col.append(merged_num)
                    self.score += merged_num
                    i += 2
                    moved = True
                else:
                    merged_col.append(new_col[i])
                    i += 1
            while len(merged_col) < 4:
                merged_col.append(0)
            merged_col = merged_col[::-1]
            for row in range(4):
                if merged_col[row] != self.grid[row][col]:
                    moved = True
                self.grid[row][col] = merged_col[row]

        # 【新增】记录移动后的目标位置，并开启动画
        if moved:
            self.target_positions = self._get_current_positions()
            self.is_animating = True
            self.animation_progress = 0  # 重置进度
        return moved

    # ---------------------- 游戏状态检查 ----------------------
    def check_game_over(self):
        print("test:check_game_over")
        for row in range(4):
            for col in range(4):
                if self.grid[row][col] == 0:
                    return False
        for row in range(4):
            for col in range(3):
                if self.grid[row][col] == self.grid[row][col+1]:
                    return False
        for col in range(4):
            for row in range(3):
                if self.grid[row][col] == self.grid[row+1][col]:
                    return False
        return True

    def check_win(self):
        print("test:check_win")
        for row in range(4):
            for col in range(4):
                if self.grid[row][col] >= 2048:
                    return True
        return False

    # ---------------------- 绘制界面 ----------------------
    def draw_grid(self):
        self.screen.fill(BACKGROUND_COLOR)
        # 原分数、提示文字绘制逻辑不变（省略，保持原样）
        
        # 【修改】根据动画状态绘制方块
        if self.is_animating:
            # 动画播放中：按进度计算当前位置
            self.animation_progress += 1
            # 动画结束（进度达到总帧数），重置状态
            if self.animation_progress >= self.animation_frames:
                self.is_animating = False
                self.animation_progress = 0
            
            # 计算进度比例（0到1）
            progress_ratio = self.animation_progress / self.animation_frames
            
            # 遍历所有目标位置的方块，绘制过渡效果
            for value, target_list in self.target_positions.items():
                # 匹配初始位置（按顺序对应，确保移动方向正确）
                start_list = self.start_positions.get(value, [])
                for i in range(len(target_list)):
                    if i >= len(start_list):
                        continue  # 新生成的方块（如移动后新增的2/4），无初始位置，暂不处理
                    start_row, start_col = start_list[i]
                    target_row, target_col = target_list[i]
                    
                    # 计算当前帧的坐标（初始位置 + 进度*(目标-初始)）
                    x = start_col * GRID_SIZE + GRID_GAP * (start_col + 1)
                    target_x = target_col * GRID_SIZE + GRID_GAP * (target_col + 1)
                    current_x = x + (target_x - x) * progress_ratio
                    
                    y = start_row * GRID_SIZE + GRID_GAP * (start_row + 1)
                    target_y = target_row * GRID_SIZE + GRID_GAP * (target_row + 1)
                    current_y = y + (target_y - y) * progress_ratio
                    
                    # 绘制当前帧的方块
                    pygame.draw.rect(
                        self.screen,
                        COLOR_MAP[value],
                        (current_x, current_y, GRID_SIZE, GRID_SIZE),
                        border_radius=5
                    )
                    text = FONT.render(str(value), True, TEXT_COLOR_MAP[value])
                    text_rect = text.get_rect(center=(current_x + GRID_SIZE//2, current_y + GRID_SIZE//2))
                    self.screen.blit(text, text_rect)
        else:
            # 无动画：绘制当前网格（原逻辑不变）
            for i in range(4):
                for j in range(4):
                    value = self.grid[i][j]
                    x = j * GRID_SIZE + GRID_GAP * (j + 1)
                    y = i * GRID_SIZE + GRID_GAP * (i + 1)
                    pygame.draw.rect(
                        self.screen,
                        COLOR_MAP[value],
                        (x, y, GRID_SIZE, GRID_SIZE),
                        border_radius=5
                    )
                    if value != 0:
                        text = FONT.render(str(value), True, TEXT_COLOR_MAP[value])
                        text_rect = text.get_rect(center=(x + GRID_SIZE//2, y + GRID_SIZE//2))
                        self.screen.blit(text, text_rect)

    # ---------------------- 游戏主循环 ----------------------
    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    moved = False
                    # 【新增】动画播放时，只响应R（重启）和Z（回退），不响应移动按键
                    if self.is_animating:
                        if event.key == pygame.K_r:
                            self.reset_game()
                            self.is_animating = False  # 重置动画状态
                        elif event.key == pygame.K_z:
                            self.undo_to_latest()
                            self.is_animating = False  # 重置动画状态
                        continue  # 跳过移动按键处理
                    
                    # 原按键逻辑不变（R、Z、WASD）
                    if event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_z:
                        self.undo_to_latest()
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        moved = self.move_left()
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        moved = self.move_right()
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        moved = self.move_up()
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        moved = self.move_down()

                    if not self.game_over and moved:
                        self.add_new_tile()
                        self.save_current_state()
                        self.win = self.check_win()
                        self.game_over = self.check_game_over()

            self.draw_grid()
            pygame.display.update()
            clock.tick(60)

if __name__ == "__main__":
    game = Game2048()
    game.run()