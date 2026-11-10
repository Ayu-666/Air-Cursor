import os
import pygame

from config import (
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    CANVAS_TITLE,
    CANVAS_RESIZABLE,
    DRAWING_MODE_ENABLED,
)


class DrawingCanvas:
    """Practical, resizable floating drawing canvas.

    Can be enabled/disabled dynamically without terminating the main application.
    """

    def __init__(
        self,
        width: int = CANVAS_WIDTH,
        height: int = CANVAS_HEIGHT,
        title: str = CANVAS_TITLE,
        enabled_at_start: bool = DRAWING_MODE_ENABLED,
    ):
        self.width = width
        self.height = height
        self.title = title
        self.is_active = False
        self.screen = None
        self.font = None
        self.surface = None

        self.previous_point = None
        self.brush_color = (25, 25, 25)
        self.brush_size = 5

        # Initialize pygame core
        pygame.init()

        if enabled_at_start:
            self.activate()

    def activate(self):
        """Open or show the drawing canvas window."""
        if self.is_active and self.screen is not None:
            return

        flags = pygame.RESIZABLE if CANVAS_RESIZABLE else 0
        self.screen = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption(self.title)

        if self.font is None:
            self.font = pygame.font.SysFont("segoeui", 16)

        if self.surface is None:
            self.surface = pygame.Surface((self.width, self.height))
            self.surface.fill((250, 250, 250))
        elif self.surface.get_size() != (self.width, self.height):
            new_surface = pygame.Surface((self.width, self.height))
            new_surface.fill((250, 250, 250))
            new_surface.blit(self.surface, (0, 0))
            self.surface = new_surface

        self.is_active = True

    def deactivate(self):
        """Hide/close the drawing canvas window without quitting the application."""
        if not self.is_active:
            return
        self.is_active = False
        self.stop_stroke()
        try:
            pygame.display.quit()
        except Exception:
            pass

    def toggle(self) -> bool:
        """Toggle drawing canvas visibility."""
        if self.is_active:
            self.deactivate()
        else:
            self.activate()
        return self.is_active

    def process_events(self):
        """Handle Pygame events when the canvas window is active."""
        if not self.is_active or self.screen is None:
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Closing canvas window only disables drawing mode, does NOT quit app
                self.deactivate()
                return

            elif event.type == pygame.VIDEORESIZE:
                # Handle window resizing
                self.width, self.height = event.w, event.h
                flags = pygame.RESIZABLE if CANVAS_RESIZABLE else 0
                self.screen = pygame.display.set_mode((self.width, self.height), flags)
                new_surface = pygame.Surface((self.width, self.height))
                new_surface.fill((250, 250, 250))
                new_surface.blit(self.surface, (0, 0))
                self.surface = new_surface

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
                elif event.key == pygame.K_d:
                    self.deactivate()
                    return

    def draw_from_normalized(self, x: float, y: float):
        """Draw onto canvas using normalized hand coordinates."""
        if not self.is_active or self.surface is None:
            return

        point = (
            max(0, min(self.width - 1, int(x * self.width))),
            max(0, min(self.height - 1, int(y * self.height))),
        )
        if self.previous_point is not None:
            pygame.draw.line(
                self.surface,
                self.brush_color,
                self.previous_point,
                point,
                self.brush_size,
            )
            pygame.draw.circle(
                self.surface,
                self.brush_color,
                point,
                max(1, self.brush_size // 2),
            )
        self.previous_point = point

    def stop_stroke(self):
        """Reset current line stroke."""
        self.previous_point = None

    def clear(self):
        """Clear canvas surface."""
        if self.surface is not None:
            self.surface.fill((250, 250, 250))
        self.stop_stroke()

    def render(self, gesture: str):
        """Render canvas contents and status HUD."""
        if not self.is_active or self.screen is None or self.surface is None:
            return

        self.screen.blit(self.surface, (0, 0))

        # Instructions banner
        hint = "DRAW: index+middle | C: clear | 1-4: colors | +/-: size | D: close canvas"
        label = self.font.render(hint, True, (80, 80, 80))
        self.screen.blit(label, (12, 10))

        status = self.font.render(f"Gesture: {gesture}", True, (30, 30, 30))
        self.screen.blit(status, (12, 32))

        pygame.display.flip()

    def close(self):
        """Clean shutdown of pygame."""
        self.deactivate()
        try:
            pygame.quit()
        except Exception:
            pass
