import pygame
from config import CANVAS_WIDTH, CANVAS_HEIGHT, CANVAS_TITLE


class DrawingCanvas:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((CANVAS_WIDTH, CANVAS_HEIGHT))
        pygame.display.set_caption(CANVAS_TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("segoeui", 18)
        self.surface = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))
        self.surface.fill((250, 250, 250))
        self.previous_point = None
        self.brush_color = (25, 25, 25)
        self.brush_size = 5
        self.running = True

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    self.clear()
                elif event.key == pygame.K_1:
                    self.brush_color = (25, 25, 25)
                elif event.key == pygame.K_2:
                    self.brush_color = (30, 110, 220)
                elif event.key == pygame.K_3:
                    self.brush_color = (220, 70, 70)
                elif event.key == pygame.K_4:
                    self.brush_color = (30, 160, 100)
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    self.brush_size = min(24, self.brush_size + 1)
                elif event.key == pygame.K_MINUS:
                    self.brush_size = max(1, self.brush_size - 1)

    def draw_from_normalized(self, x, y):
        point = (
            max(0, min(CANVAS_WIDTH - 1, int(x * CANVAS_WIDTH))),
            max(0, min(CANVAS_HEIGHT - 1, int(y * CANVAS_HEIGHT))),
        )
        if self.previous_point is not None:
            pygame.draw.line(
                self.surface, self.brush_color,
                self.previous_point, point, self.brush_size
            )
            pygame.draw.circle(
                self.surface, self.brush_color, point, max(1, self.brush_size // 2)
            )
        self.previous_point = point

    def stop_stroke(self):
        self.previous_point = None

    def clear(self):
        self.surface.fill((250, 250, 250))
        self.stop_stroke()

    def render(self, gesture):
        self.screen.blit(self.surface, (0, 0))
        hint = "DRAW: raise index + middle | C: clear | 1-4: colours | +/-: brush"
        label = self.font.render(hint, True, (90, 90, 90))
        self.screen.blit(label, (12, 10))
        status = self.font.render(f"Gesture: {gesture}", True, (30, 30, 30))
        self.screen.blit(status, (12, 34))
        pygame.display.flip()
        self.clock.tick(60)

    def close(self):
        pygame.quit()
