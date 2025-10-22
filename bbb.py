import pygame
import sys
import random
import os
import math
from collections import deque


# Maze generation using recursive backtracker on an odd-sized grid
TILE_SIZE = 20
UI_BAR_HEIGHT = 50
OFFSET_Y = 0
VISION_RADIUS = 120
# load or generate wall texture
wall_tex = None
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


def draw_player(screen, pos, effect=None):
    x, y = to_display_coords(pos)
    
    if effect == "big":
        size = int(TILE_SIZE * 1.5)
        rect = pygame.Rect(x - size//4, y - size//4, size, size)
    elif effect == "small":
        size = int(TILE_SIZE * 0.6)
        rect = pygame.Rect(x + TILE_SIZE//3, y + TILE_SIZE//3, size, size)
    else:
        rect = pygame.Rect(x + 3, y + 3, TILE_SIZE - 6, TILE_SIZE - 6)
    
    color = (200, 30, 30)
    if effect == "speed":
        color = (255, 165, 0)  # 加速时显示为橙色
    elif effect == "confused":
        color = (147, 112, 219)  # 混乱时显示为紫色
        
    pygame.draw.rect(screen, color, rect)


def draw_special_tile(screen, pos, tile_type):
    x, y = to_display_coords(pos)
    if tile_type == 3:  # 传送门
        pygame.draw.circle(screen, (147, 112, 219), (x + TILE_SIZE//2, y + TILE_SIZE//2), TILE_SIZE//3)
    elif tile_type == 4:  # 弹簧
        pygame.draw.rect(screen, (255, 165, 0), (x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4))
    elif tile_type == 5:  # 香蕉皮
        pygame.draw.ellipse(screen, (255, 255, 0), (x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4))


def generate_and_setup(rows=31, cols=31, extra_passages=60):
    maze = make_maze(rows, cols, extra_passages)
    # find an exit far from the start
    exit_cell = find_farthest(maze, (1, 1))
    er, ec = exit_cell
    maze[er][ec] = 2
    
    # 添加一些随机特殊格子
    special_tiles = []
    for _ in range(8):  # 添加8个特殊格子
        r = random.randrange(1, rows - 1)
        c = random.randrange(1, cols - 1)
        if maze[r][c] == 0 and (r, c) != (1, 1) and (r, c) != exit_cell:
            maze[r][c] = random.choice([3, 4, 5])  # 3=传送门, 4=弹簧, 5=香蕉皮
            special_tiles.append((r, c))
    
    return maze, [1, 1], (er, ec), special_tiles


def main():
    pygame.init()
    global OFFSET_Y, SHOW_TEXTURE, SHOW_FOG
    load_wall_texture()
    
    # 初始化迷宫
    rows, cols = 31, 41
    maze, player_pos, exit_cell, special_tiles = generate_and_setup(rows, cols, extra_passages=120)
    ROWS, COLS = len(maze), len(maze[0])
    WIDTH, HEIGHT = COLS * TILE_SIZE, ROWS * TILE_SIZE
    OFFSET_Y = UI_BAR_HEIGHT
    
    # 设置显示
    screen = pygame.display.set_mode((WIDTH, HEIGHT + UI_BAR_HEIGHT))
    pygame.display.set_caption("疯狂迷宫大冒险 🎮")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 48)
    btn_font = pygame.font.SysFont(None, 24)
    
    # 初始化游戏状态
    steps = 0
    win = False
    player_effect = None
    effect_end_time = 0
    move_cooldown = 150
    random_event_cooldown = 8000
    start_time = pygame.time.get_ticks()
    last_move_time = 0
    last_random_event = pygame.time.get_ticks()
    
    # UI元素
    hint_text = ""
    hint_until = 0
    new_btn_rect = pygame.Rect(10, 8, 100, 34)
    reset_btn_rect = pygame.Rect(120, 8, 100, 34)

    print("游戏启动！使用方向键移动，N键生成新迷宫，R键重置")

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
                    maze, player_pos, exit_cell, special_tiles = generate_and_setup(rows, cols, extra_passages=120)
                    ROWS, COLS = len(maze), len(maze[0])
                    steps = 0
                    start_time = current_time
                    win = False
                    player_effect = None
                    hint_text = "新的迷宫！"
                    hint_until = current_time + 2000
                    
                elif event.key == pygame.K_r:
                    print("重置玩家位置...")
                    player_pos = [1, 1]
                    steps = 0
                    start_time = current_time
                    win = False
                    hint_text = "重新开始！"
                    hint_until = current_time + 2000
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if new_btn_rect.collidepoint((mx, my)):
                    maze, player_pos, exit_cell, special_tiles = generate_and_setup(rows, cols, extra_passages=120)
                    ROWS, COLS = len(maze), len(maze[0])
                    steps = 0
                    start_time = current_time
                    win = False
                    hint_text = "新迷宫！"
                    hint_until = current_time + 2000
                elif reset_btn_rect.collidepoint((mx, my)):
                    player_pos = [1, 1]
                    steps = 0
                    start_time = current_time
                    win = False
                    hint_text = "重置！"
                    hint_until = current_time + 2000
        
        # 处理连续按键移动
        if not win:
            keys = pygame.key.get_pressed()
            effective_cooldown = move_cooldown // 2 if player_effect == "speed" else move_cooldown
            
            if current_time - last_move_time >= effective_cooldown:
                new_pos = player_pos.copy()
                moved = False
                
                # 根据效果处理移动方向
                if player_effect == "confused":
                    if keys[pygame.K_UP]: 
                        new_pos[0] += 1
                        moved = True
                    elif keys[pygame.K_DOWN]: 
                        new_pos[0] -= 1
                        moved = True
                    elif keys[pygame.K_LEFT]: 
                        new_pos[1] += 1
                        moved = True
                    elif keys[pygame.K_RIGHT]: 
                        new_pos[1] -= 1
                        moved = True
                else:
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
                        cell_type = maze[new_pos[0]][new_pos[1]]
                        
                        # 处理特殊格子
                        if cell_type == 3:  # 传送门
                            attempts = 0
                            while attempts < 100:
                                r = random.randint(1, ROWS-2)
                                c = random.randint(1, COLS-2)
                                if maze[r][c] in [0, 2]:
                                    new_pos = [r, c]
                                    hint_text = "嗖！传送了！✨"
                                    hint_until = current_time + 1500
                                    break
                                attempts += 1
                                
                        elif cell_type == 4:  # 弹簧
                            bounce_dist = random.randint(2, 4)
                            dr = new_pos[0] - player_pos[0]
                            dc = new_pos[1] - player_pos[1]
                            for i in range(bounce_dist, 0, -1):
                                test_pos = [new_pos[0] + dr * i, new_pos[1] + dc * i]
                                if 0 <= test_pos[0] < ROWS and 0 <= test_pos[1] < COLS and maze[test_pos[0]][test_pos[1]] != 1:
                                    new_pos = test_pos
                                    break
                            hint_text = "弹！🔥"
                            hint_until = current_time + 1500
                            
                        elif cell_type == 5:  # 香蕉皮
                            new_pos = [1, 1]
                            hint_text = "啊！滑倒了！🍌"
                            hint_until = current_time + 1500
                        
                        player_pos[:] = new_pos
                        steps += 1
                        
                        # 检查是否到达出口
                        if maze[player_pos[0]][player_pos[1]] == 2:
                            win = True
                            hint_text = "恭喜通关！🎉"
                            hint_until = current_time + 5000
        
        # 处理随机事件
        if current_time - last_random_event > random_event_cooldown and not win:
            last_random_event = current_time
            if random.random() < 0.4:  # 40%概率触发
                event_type = random.choice(["big", "small", "speed", "confused", "maze_shuffle"])
                effect_duration = random.randint(5000, 8000)
                effect_end_time = current_time + effect_duration
                
                if event_type == "maze_shuffle":
                    # 随机修改部分迷宫
                    for _ in range(15):
                        r, c = random.randint(2, ROWS-3), random.randint(2, COLS-3)
                        if (r, c) != tuple(player_pos) and (r, c) != exit_cell:
                            if maze[r][c] == 1:
                                maze[r][c] = 0
                            elif maze[r][c] == 0:
                                maze[r][c] = 1
                    hint_text = "迷宫重组了！🌀"
                    hint_until = current_time + 2000
                else:
                    player_effect = event_type
                    effect_messages = {
                        "big": "你变大了！🔍",
                        "small": "你变小了！🔬",
                        "speed": "加速！⚡",
                        "confused": "方向混乱！😵"
                    }
                    hint_text = effect_messages[event_type]
                    hint_until = current_time + 2000
        
        # 处理效果结束
        if current_time > effect_end_time:
            if player_effect:
                player_effect = None
                hint_text = "效果消失了"
                hint_until = current_time + 1000

        # === 绘制 ===
        screen.fill((20, 20, 20))
        
        # 绘制UI栏
        pygame.draw.rect(screen, (50, 50, 50), (0, 0, WIDTH, UI_BAR_HEIGHT))
        
        # 绘制迷宫
        draw_maze(screen, maze)
        
        # 绘制特殊格子
        for r in range(ROWS):
            for c in range(COLS):
                if maze[r][c] in [3, 4, 5]:
                    draw_special_tile(screen, (r, c), maze[r][c])
        
        # 绘制出口
        er, ec = exit_cell
        exit_rect = pygame.Rect(ec * TILE_SIZE, er * TILE_SIZE + OFFSET_Y, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(screen, (30, 200, 30), exit_rect)
        
        # 绘制玩家
        draw_player(screen, player_pos, player_effect)
        
        # 绘制UI按钮
        pygame.draw.rect(screen, (200, 200, 200), new_btn_rect)
        pygame.draw.rect(screen, (200, 200, 200), reset_btn_rect)
        screen.blit(btn_font.render("新迷宫(N)", True, (0, 0, 0)), (new_btn_rect.x + 8, new_btn_rect.y + 8))
        screen.blit(btn_font.render("重置(R)", True, (0, 0, 0)), (reset_btn_rect.x + 12, reset_btn_rect.y + 8))
        
        # 绘制提示文本
        if hint_text and current_time < hint_until:
            hint_surf = btn_font.render(hint_text, True, (255, 255, 100))
            screen.blit(hint_surf, (240, 15))
        
        # 绘制效果状态
        if player_effect:
            effect_text = f"状态: {player_effect}"
            effect_surf = btn_font.render(effect_text, True, (255, 200, 0))
            screen.blit(effect_surf, (240, 35))
        
        # 绘制胜利文本
        if win:
            win_text = font.render("🎉 You Win! 🎉", True, (255, 255, 0))
            text_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + OFFSET_Y))
            # 绘制背景
            bg_rect = pygame.Rect(text_rect.x - 10, text_rect.y - 10, text_rect.width + 20, text_rect.height + 20)
            pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect)
            screen.blit(win_text, text_rect)
        
        # 绘制计时器和步数
        elapsed_s = (current_time - start_time) // 1000
        info = f"时间: {elapsed_s}s  步数: {steps}"
        info_surf = btn_font.render(info, True, (255, 255, 255))
        screen.blit(info_surf, (WIDTH - 200, 15))
        
        # 绘制迷雾效果
        if SHOW_FOG and not win:
            fog = pygame.Surface((WIDTH, HEIGHT + UI_BAR_HEIGHT), pygame.SRCALPHA)
            fog.fill((0, 0, 0, 180))
            px, py = to_display_coords(tuple(player_pos))
            pygame.draw.circle(fog, (0, 0, 0, 0), (px + TILE_SIZE // 2, py + TILE_SIZE // 2), VISION_RADIUS)
            screen.blit(fog, (0, 0))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
