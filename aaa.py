import pygame
import random
import sys

# 初始化 pygame
pygame.init()

# 屏幕设置
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Colorful Canvas")

# 状态变量
drawing = False
color_mode = 0  # 0: 随机色, 1: 渐变色, 2: 固定色
fixed_color = (255, 0, 0)
last_pos = None

def get_color(pos):
    if color_mode == 0:
        return (random.randint(0,255), random.randint(0,255), random.randint(0,255))
    elif color_mode == 1:
        # 根据位置生成渐变色
        x, y = pos
        return (x % 256, y % 256, (x*y) % 256)
    else:
        return fixed_color

def draw_circle(pos):
    color = get_color(pos)
    radius = random.randint(10, 30)
    pygame.draw.circle(screen, color, pos, radius)

def main():
    global drawing, color_mode, fixed_color, last_pos
    clock = pygame.time.Clock()
    screen.fill((255,255,255))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # 鼠标事件
            elif event.type == pygame.MOUSEBUTTONDOWN:
                drawing = True
                draw_circle(event.pos)
                last_pos = event.pos
            elif event.type == pygame.MOUSEBUTTONUP:
                drawing = False
                last_pos = None
            elif event.type == pygame.MOUSEMOTION and drawing:
                draw_circle(event.pos)
                last_pos = event.pos

            # 键盘事件
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    screen.fill((255,255,255))  # 清空画布
                elif event.key == pygame.K_1:
                    color_mode = 0
                elif event.key == pygame.K_2:
                    color_mode = 1
                elif event.key == pygame.K_3:
                    color_mode = 2
                elif event.key == pygame.K_r:
                    fixed_color = (255, 0, 0)
                elif event.key == pygame.K_g:
                    fixed_color = (0, 255, 0)
                elif event.key == pygame.K_b:
                    fixed_color = (0, 0, 255)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
