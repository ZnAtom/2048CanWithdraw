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

    # ---------------------- 移动方法(保持单次合并逻辑) ----------------------
    def move_left(self):
        print("test:move_left")
        moved = False
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
        return moved

    def move_right(self):
        print("test:move_right")
        moved = False
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
        return moved

    def move_up(self):
        print("test:move_up")
        moved = False
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
        return moved

    def move_down(self):
        print("test:move_down")
        moved = False
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
        # 绘制分数和回退提示(显示剩余可回退次数)
        score_text = FONT.render(f"分数: {self.score}", True, (0, 0, 0))
        self.screen.blit(score_text, (20, SIZE + 30))
        undo_count = self.history_list.get_length() - 1 # 可回退次数(不包括当前状态)
        if undo_count < 0:
            undo_count = 0
        # undo_text = FONT_SMALL.render(f"按Z回退(可回退{undo_count}步)", True, (0, 0, 0))
        # self.screen.blit(undo_text, (400, SIZE + 35))
        # 1. 游戏结束提示（右下角）
        if self.game_over:
            over_text = FONT.render("游戏结束!", True, (255, 0, 0))
            restart_text = FONT_SMALL.render("按R重启 | 按Z回退", True, (0, 0, 0))
            self.screen.blit(over_text, (400, SIZE + 35))
            self.screen.blit(restart_text, (400, SIZE + 15))
        
        # 2. 胜利提示（右下角）
        if self.win and not self.game_over:
            win_text = FONT.render("恭喜胜利!", True, (0, 255, 0))
            continue_text = FONT_SMALL.render("按任意键继续", True, (0, 0, 0))
            self.screen.blit(win_text, (400, SIZE + 35))
            self.screen.blit(continue_text, (400, SIZE + 15))
        # 绘制单元格
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
                    moved = False  # 提前初始化 moved
                    # 1. 先判断 R 键（重新开始）
                    if event.key == pygame.K_r:
                        self.reset_game()
                    # 2. 再判断 Z 键（回退）
                    elif event.key == pygame.K_z:
                        self.undo_to_latest()
                    # 3. 最后判断 WASD（无论游戏是否结束，都先监听按键）
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        moved = self.move_left()
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        moved = self.move_right()
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        moved = self.move_up()
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        moved = self.move_down()

                    # 4. 只有“游戏未结束且移动有效”时，才执行后续操作（添加方块、保存状态）
                    if not self.game_over and moved:
                        self.add_new_tile()
                        self.save_current_state()  # 移动有效才保存状态（避免无效操作占用历史）
                        self.win = self.check_win()
                        self.game_over = self.check_game_over()

            # 绘制界面
            self.draw_grid()
            pygame.display.update()
            clock.tick(60)

if __name__ == "__main__":
    game = Game2048()
    game.run()