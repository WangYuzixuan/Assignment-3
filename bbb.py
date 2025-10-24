import pygame
import sys
import random
import os
import math
from collections import deque


# Maze generation using recursive backtracker on an odd-sized grid
TILE_SIZE = 20
UI_BAR_HEIGHT = 60
OFFSET_Y = 0
VISION_RADIUS = 120
# load or generate wall texture
wall_tex = None
player_tex = None
enemy_tex = None
goal_tex = None
SHOW_TEXTURE = True
SHOW_FOG = True

def load_wall_texture():
    global wall_tex
    try:
        tex_path = os.path.join(os.path.dirname(__file__), 'wall_texture.png')
    except Exception:
        tex_path = 'wall_texture.png'

    try:
        if os.path.exists(tex_path):
            wall_tex = pygame.image.load(tex_path)
            wall_tex = pygame.transform.scale(wall_tex, (TILE_SIZE, TILE_SIZE))
            print(f"[debug] Loaded wall texture from {tex_path}, size={wall_tex.get_size()}")
        else:
            # generate a simple procedural texture and save
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
            surf.fill((70, 70, 70))
            for i in range(0, TILE_SIZE, 2):
                c = 60 + (i % 8) * 2
                pygame.draw.line(surf, (c, c, c), (i, 0), (0, i), 1)
            wall_tex = surf
            try:
                pygame.image.save(surf, tex_path)
            except Exception:
                pass
            print(f"[debug] Generated wall texture and saved to {tex_path}")
    except Exception as e:
        wall_tex = None
        print("[debug] Failed to load or create wall texture:", e)


def load_player_texture():
    """加载玩家贴图，支持 player.png 或 player_texture.png"""
    global player_tex
    for filename in ['player.png', 'player_texture.png', 'player_sprite.png']:
        try:
            tex_path = os.path.join(os.path.dirname(__file__), filename)
        except Exception:
            tex_path = filename
        
        try:
            if os.path.exists(tex_path):
                player_tex = pygame.image.load(tex_path)
                player_tex = pygame.transform.scale(player_tex, (TILE_SIZE - 4, TILE_SIZE - 4))
                print(f"[debug] Loaded player texture from {tex_path}")
                return
        except Exception as e:
            print(f"[debug] Failed to load {filename}:", e)
    
    print("[debug] No player texture found, will use default shape")


def load_enemy_texture():
    """加载敌人贴图，支持 enemy.png 或 enemy_texture.png"""
    global enemy_tex
    for filename in ['enemy.png', 'enemy_texture.png', 'enemy_sprite.png', 'monster.png']:
        try:
            tex_path = os.path.join(os.path.dirname(__file__), filename)
        except Exception:
            tex_path = filename
        
        try:
            if os.path.exists(tex_path):
                enemy_tex = pygame.image.load(tex_path)
                enemy_tex = pygame.transform.scale(enemy_tex, (TILE_SIZE - 4, TILE_SIZE - 4))
                print(f"[debug] Loaded enemy texture from {tex_path}")
                return
        except Exception as e:
            print(f"[debug] Failed to load {filename}:", e)
    
    print("[debug] No enemy texture found, will use default shape")


def load_goal_texture():
    """加载终点贴图，支持 goal.png 或 exit.png"""
    global goal_tex
    for filename in ['goal.png', 'exit.png', 'goal_texture.png', 'exit_texture.png', 'flag.png']:
        try:
            tex_path = os.path.join(os.path.dirname(__file__), filename)
        except Exception:
            tex_path = filename
        
        try:
            if os.path.exists(tex_path):
                goal_tex = pygame.image.load(tex_path)
                goal_tex = pygame.transform.scale(goal_tex, (TILE_SIZE - 4, TILE_SIZE - 4))
                print(f"[debug] Loaded goal texture from {tex_path}")
                return
        except Exception as e:
            print(f"[debug] Failed to load {filename}:", e)
    
    print("[debug] No goal texture found, will use default shape")


def make_maze(rows=31, cols=31, extra_passages=0):
    """Generate a maze where 1=wall, 0=path. rows and cols should be odd numbers."""
    if rows % 2 == 0:
        rows += 1
    if cols % 2 == 0:
        cols += 1

    maze = [[1 for _ in range(cols)] for _ in range(rows)]

    def neighbors(r, c):
        for dr, dc in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < rows and 0 <= cc < cols:
                yield rr, cc

    stack = []
    start = (1, 1)
    maze[start[0]][start[1]] = 0
    stack.append(start)

    while stack:
        r, c = stack[-1]
        nbrs = [n for n in neighbors(r, c) if maze[n[0]][n[1]] == 1]
        if nbrs:
            nr, nc = random.choice(nbrs)
            # knock down wall between
            wall_r, wall_c = (r + nr) // 2, (c + nc) // 2
            maze[wall_r][wall_c] = 0
            maze[nr][nc] = 0
            stack.append((nr, nc))
        else:
            stack.pop()

    # carve extra random passages to increase complexity/loops
    for _ in range(extra_passages):
        r = random.randrange(1, rows - 1, 2)
        c = random.randrange(1, cols - 1, 2)
        dir = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        wr, wc = r + dir[0], c + dir[1]
        if 0 < wr < rows and 0 < wc < cols:
            maze[wr][wc] = 0

    return maze


def find_farthest(maze, start=(1, 1)):
    rows, cols = len(maze), len(maze[0])
    dist = [[-1] * cols for _ in range(rows)]
    q = deque()
    q.append(start)
    dist[start[0]][start[1]] = 0
    far = start
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < rows and 0 <= cc < cols and maze[rr][cc] == 0 and dist[rr][cc] == -1:
                dist[rr][cc] = dist[r][c] + 1
                q.append((rr, cc))
                if dist[rr][cc] > dist[far[0]][far[1]]:
                    far = (rr, cc)
    return far


def to_display_coords(cell):
    r, c = cell
    # apply vertical offset so UI bar doesn't cover the maze
    return c * TILE_SIZE, r * TILE_SIZE + OFFSET_Y


def draw_maze(screen, maze):
    rows, cols = len(maze), len(maze[0])
    for r in range(rows):
        for c in range(cols):
            rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE + OFFSET_Y, TILE_SIZE, TILE_SIZE)
            if maze[r][c] == 1:
                # textured wall
                if SHOW_TEXTURE and wall_tex:
                    screen.blit(wall_tex, (c * TILE_SIZE, r * TILE_SIZE + OFFSET_Y))
                else:
                    pygame.draw.rect(screen, (40, 40, 40), rect)
                # subtle shadow at bottom-right
                shadow = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                pygame.draw.polygon(shadow, (0, 0, 0, 40), [(TILE_SIZE, TILE_SIZE*0.6), (TILE_SIZE, TILE_SIZE), (TILE_SIZE*0.6, TILE_SIZE)])
                screen.blit(shadow, (c * TILE_SIZE, r * TILE_SIZE + OFFSET_Y))
            else:
                pygame.draw.rect(screen, (230, 230, 230), rect)


def draw_player(screen, pos):
    x, y = to_display_coords(pos)
    
    # 如果有玩家贴图，使用贴图
    if player_tex:
        screen.blit(player_tex, (x + 2, y + 2))
    else:
        # 否则使用默认的红色方块
        rect = pygame.Rect(x + 3, y + 3, TILE_SIZE - 6, TILE_SIZE - 6)
        color = (200, 30, 30)
        pygame.draw.rect(screen, color, rect)

# Enemy/Chaser class
class Enemy:
    def __init__(self, maze, player_pos):
        self.pos = self.get_spawn_position(maze, player_pos)
        self.move_cooldown = 300  # Slower than player
        self.last_move_time = pygame.time.get_ticks()
    
    def get_spawn_position(self, maze, player_pos):
        # Spawn enemy far from player
        rows, cols = len(maze), len(maze[0])
        max_dist = 0
        best_pos = None
        for _ in range(50):  # Try 50 random positions
            r = random.randrange(1, rows, 2)
            c = random.randrange(1, cols, 2)
            if maze[r][c] == 0:
                dist = abs(r - player_pos[0]) + abs(c - player_pos[1])
                if dist > max_dist:
                    max_dist = dist
                    best_pos = (r, c)
        return best_pos if best_pos else (1, 1)
    
    def can_move(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time >= self.move_cooldown:
            self.last_move_time = current_time
            return True
        return False
    
    def chase_player(self, maze, player_pos):
        # Simple BFS pathfinding toward player
        if not self.can_move():
            return
        
        rows, cols = len(maze), len(maze[0])
        queue = deque([(self.pos, [])])
        visited = {self.pos}
        
        while queue:
            (r, c), path = queue.popleft()
            
            if (r, c) == player_pos:
                if path:  # Move one step toward player
                    self.pos = path[0]
                return
            
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and maze[nr][nc] == 0 and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append(((nr, nc), path + [(nr, nc)]))
    
    def draw(self, screen):
        x, y = to_display_coords(self.pos)
        
        # 如果有敌人贴图，使用贴图
        if enemy_tex:
            screen.blit(enemy_tex, (x + 2, y + 2))
        else:
            # 否则使用默认的紫色方块
            rect = pygame.Rect(x + 3, y + 3, TILE_SIZE - 6, TILE_SIZE - 6)
            pygame.draw.rect(screen, (100, 0, 150), rect)


def draw_goal(screen, goal_pos):
    x, y = to_display_coords(goal_pos)
    
    # 如果有终点贴图，使用贴图
    if goal_tex:
        screen.blit(goal_tex, (x + 2, y + 2))
    else:
        # 否则使用默认的黄色椭圆
        pygame.draw.ellipse(screen, (255, 255, 0), (x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4))


def generate_and_setup(rows=31, cols=31, extra_passages=60):
    maze = make_maze(rows, cols, extra_passages)
    # find an exit far from the start
    exit_cell = find_farthest(maze, (1, 1))
    er, ec = exit_cell
    maze[er][ec] = 2
    
    return maze, [1, 1], (er, ec)


def main():
    pygame.init()
    global OFFSET_Y, SHOW_TEXTURE, SHOW_FOG
    load_wall_texture()
    load_player_texture()
    load_enemy_texture()
    load_goal_texture()
    
    # 初始化迷宫
    rows, cols = 31, 41
    maze, player_pos, exit_cell = generate_and_setup(rows, cols, extra_passages=120)
    ROWS, COLS = len(maze), len(maze[0])
    WIDTH, HEIGHT = COLS * TILE_SIZE, ROWS * TILE_SIZE
    OFFSET_Y = UI_BAR_HEIGHT
    
    # 设置显示
    screen = pygame.display.set_mode((WIDTH, HEIGHT + UI_BAR_HEIGHT))
    pygame.display.set_caption("追杀迷宫 - 逃生游戏 🎮")
    clock = pygame.time.Clock()
    
    # 优化字体设置 - 使用更合适的大小
    try:
        font = pygame.font.SysFont("microsoftyahei", 36)
    except:
        try:
            font = pygame.font.SysFont("simsun", 36)
        except:
            font = pygame.font.Font(None, 36)
    
    try:
        btn_font = pygame.font.SysFont("microsoftyahei", 20)
    except:
        try:
            btn_font = pygame.font.SysFont("simsun", 20)
        except:
            btn_font = pygame.font.Font(None, 20)
    
    try:
        info_font = pygame.font.SysFont("microsoftyahei", 18)
    except:
        try:
            info_font = pygame.font.SysFont("simsun", 18)
        except:
            info_font = pygame.font.Font(None, 18)
    
    # 初始化游戏状态
    steps = 0
    win = False
    game_over = False
    move_cooldown = 150
    start_time = pygame.time.get_ticks()
    last_move_time = 0
    
    # 创建追踪者
    enemy = Enemy(maze, tuple(player_pos))
    
    # UI元素
    hint_text = ""
    hint_until = 0
    new_btn_rect = pygame.Rect(10, 8, 100, 34)
    reset_btn_rect = pygame.Rect(120, 8, 100, 34)

    print("游戏启动!使用方向键移动逃离追踪者,N键生成新迷宫,R键重置")

    while True:
        current_time = pygame.time.get_ticks()
        
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                print(f"按键: {pygame.key.name(event.key)}")
                
                if event.key == pygame.K_n:
                    print("生成新迷宫...")
                    maze, player_pos, exit_cell = generate_and_setup(rows, cols, extra_passages=120)
                    ROWS, COLS = len(maze), len(maze[0])
                    steps = 0
                    start_time = current_time
                    win = False
                    game_over = False
                    enemy = Enemy(maze, tuple(player_pos))
                    hint_text = "新的迷宫!"
                    hint_until = current_time + 2000
                    
                elif event.key == pygame.K_r:
                    print("重置玩家位置...")
                    player_pos = [1, 1]
                    steps = 0
                    start_time = current_time
                    win = False
                    game_over = False
                    enemy = Enemy(maze, tuple(player_pos))
                    hint_text = "重新开始!"
                    hint_until = current_time + 2000
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if new_btn_rect.collidepoint((mx, my)):
                    maze, player_pos, exit_cell = generate_and_setup(rows, cols, extra_passages=120)
                    ROWS, COLS = len(maze), len(maze[0])
                    steps = 0
                    start_time = current_time
                    win = False
                    game_over = False
                    enemy = Enemy(maze, tuple(player_pos))
                    hint_text = "新迷宫!"
                    hint_until = current_time + 2000
                elif reset_btn_rect.collidepoint((mx, my)):
                    player_pos = [1, 1]
                    steps = 0
                    start_time = current_time
                    win = False
                    game_over = False
                    enemy = Enemy(maze, tuple(player_pos))
                    hint_text = "重置!"
                    hint_until = current_time + 2000
        
        # 处理连续按键移动
        if not win and not game_over:
            keys = pygame.key.get_pressed()
            
            if current_time - last_move_time >= move_cooldown:
                new_pos = player_pos.copy()
                moved = False
                
                if keys[pygame.K_UP]: 
                    new_pos[0] -= 1
                    moved = True
                elif keys[pygame.K_DOWN]: 
                    new_pos[0] += 1
                    moved = True
                elif keys[pygame.K_LEFT]: 
                    new_pos[1] -= 1
                    moved = True
                elif keys[pygame.K_RIGHT]: 
                    new_pos[1] += 1
                    moved = True
                
                # 检查移动是否有效
                if moved:
                    if 0 <= new_pos[0] < ROWS and 0 <= new_pos[1] < COLS and maze[new_pos[0]][new_pos[1]] != 1:
                        last_move_time = current_time
                        player_pos = new_pos
                        steps += 1
                        
                        # 检查是否到达出口
                        if maze[player_pos[0]][player_pos[1]] == 2:
                            win = True
                            hint_text = "恭喜通关!"
                            hint_until = current_time + 5000
        
            # 敌人追踪玩家
            enemy.chase_player(maze, tuple(player_pos))
            
            # 检查是否被追上
            if tuple(player_pos) == enemy.pos:
                game_over = True
                hint_text = "被追上了!游戏结束!"
                hint_until = current_time + 5000
        
        # 绘制场景 - 先绘制迷宫
        screen.fill((20, 20, 20))
        
        # 绘制迷宫
        draw_maze(screen, maze)
        
        # 绘制出口 - 使用draw_goal函数
        draw_goal(screen, exit_cell)
        
        # 绘制敌人
        enemy.draw(screen)
        
        # 绘制玩家
        draw_player(screen, player_pos)
        
        # 绘制迷雾效果 (在UI之前绘制,使UI可见)
        if SHOW_FOG and not win and not game_over:
            fog = pygame.Surface((WIDTH, HEIGHT + UI_BAR_HEIGHT), pygame.SRCALPHA)
            fog.fill((0, 0, 0, 180))
            px, py = to_display_coords(tuple(player_pos))
            pygame.draw.circle(fog, (0, 0, 0, 0), (px + TILE_SIZE // 2, py + TILE_SIZE // 2), VISION_RADIUS)
            screen.blit(fog, (0, 0))
        
        # 绘制UI栏 (在迷雾之后,确保可见)
        pygame.draw.rect(screen, (50, 50, 50), (0, 0, WIDTH, UI_BAR_HEIGHT))
        
        # 绘制UI按钮 - 优化按钮大小和文字
        pygame.draw.rect(screen, (200, 200, 200), new_btn_rect)
        pygame.draw.rect(screen, (200, 200, 200), reset_btn_rect)
        pygame.draw.rect(screen, (100, 100, 100), new_btn_rect, 2)  # 添加边框
        pygame.draw.rect(screen, (100, 100, 100), reset_btn_rect, 2)
        
        new_text = btn_font.render("新迷宫(N)", True, (0, 0, 0))
        reset_text = btn_font.render("重置(R)", True, (0, 0, 0))
        # 居中显示按钮文字
        screen.blit(new_text, (new_btn_rect.x + (new_btn_rect.width - new_text.get_width()) // 2, 
                               new_btn_rect.y + (new_btn_rect.height - new_text.get_height()) // 2))
        screen.blit(reset_text, (reset_btn_rect.x + (reset_btn_rect.width - reset_text.get_width()) // 2, 
                                 reset_btn_rect.y + (reset_btn_rect.height - reset_text.get_height()) // 2))
        
        # 绘制计时器和步数 - 使用更小的字体
        elapsed_s = (current_time - start_time) // 1000
        info = f"时间: {elapsed_s}s  步数: {steps}"
        info_surf = info_font.render(info, True, (255, 255, 255))
        screen.blit(info_surf, (WIDTH - info_surf.get_width() - 10, 20))
        
        # 绘制提示文本 - 优化位置
        if hint_text and current_time < hint_until:
            hint_surf = btn_font.render(hint_text, True, (255, 255, 100))
            screen.blit(hint_surf, (WIDTH // 2 - hint_surf.get_width() // 2, 20))
        
        # 绘制胜利或失败文本 - 优化大小和背景
        if win:
            win_text = font.render("成功逃脱!", True, (255, 255, 0))
            text_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + OFFSET_Y))
            # 绘制半透明背景
            bg_rect = pygame.Rect(text_rect.x - 20, text_rect.y - 15, text_rect.width + 40, text_rect.height + 30)
            bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg_surf.fill((0, 0, 0, 200))
            screen.blit(bg_surf, bg_rect)
            screen.blit(win_text, text_rect)
            # 添加表情符号
            emoji_text = font.render("🎉", True, (255, 255, 255))
            screen.blit(emoji_text, (text_rect.x - 40, text_rect.y))
            screen.blit(emoji_text, (text_rect.x + text_rect.width + 10, text_rect.y))
        elif game_over:
            lose_text = font.render("被追上了!", True, (255, 0, 0))
            text_rect = lose_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + OFFSET_Y))
            # 绘制半透明背景
            bg_rect = pygame.Rect(text_rect.x - 20, text_rect.y - 15, text_rect.width + 40, text_rect.height + 30)
            bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg_surf.fill((0, 0, 0, 200))
            screen.blit(bg_surf, bg_rect)
            screen.blit(lose_text, text_rect)
            # 添加表情符号
            emoji_text = font.render("💀", True, (255, 255, 255))
            screen.blit(emoji_text, (text_rect.x - 40, text_rect.y))
            screen.blit(emoji_text, (text_rect.x + text_rect.width + 10, text_rect.y))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
