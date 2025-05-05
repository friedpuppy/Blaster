# ui.py
# Author: Callum Donnelly
# Date: 2025-05-05 (or update to current date)
# Description: Contains UI element classes like Buttons.

import pygame
import os
from typing import Tuple, Optional

# Assuming config.py defines colors like WHITE, BLACK etc.
import config

class Button:
    """A clickable button UI element."""

    def __init__(self, x: int, y: int, width: int, height: int,
                 fg_color: Tuple[int, int, int], bg_color: Tuple[int, int, int],
                 text: str, font: pygame.font.Font, border_radius: int = 5):
        """
        Initializes the Button.

        Args:
            x (int): Top-left x-coordinate.
            y (int): Top-left y-coordinate.
            width (int): Button width.
            height (int): Button height.
            fg_color (Tuple[int, int, int]): Text color (RGB).
            bg_color (Tuple[int, int, int]): Background color (RGB).
            text (str): Text displayed on the button.
            font (pygame.font.Font): Pygame font object for the text.
            border_radius (int): Radius for rounded corners.
        """
        # --- Existing __init__ code ---
        self.font = font
        self.text_content = text
        # Store initial position relative to the container it might be placed in
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.border_radius = border_radius

        # Create the button surface (transparent initially)
        # This surface represents the button's visual appearance.
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Draw the rounded rectangle background onto the image
        pygame.draw.rect(self.image, self.bg_color, self.image.get_rect(), border_radius=self.border_radius)

        # This rect represents the button's position *on the surface it's drawn onto*.
        # It's initially set using x, y but might be adjusted by the draw offset.
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

        # Render text and center it on the button image
        self.text_surf = self.font.render(self.text_content, True, self.fg_color)
        self.text_rect = self.text_surf.get_rect(center=(self.width / 2, self.height / 2))
        self.image.blit(self.text_surf, self.text_rect)

    def is_pressed(self, mouse_pos: Tuple[int, int], mouse_pressed: Tuple[bool, bool, bool]) -> bool:
        """Checks if the button is clicked."""
        # mouse_pressed[0] corresponds to the left mouse button
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]

    def draw(self, surface: pygame.Surface, offset: Optional[Tuple[int, int]] = None):
        """
        Draws the button onto the given surface, applying an optional offset.
        """
        draw_pos = self.rect.topleft
        if offset:
            # Adjust the drawing position by the offset
            draw_pos = (draw_pos[0] + offset[0], draw_pos[1] + offset[1])
        surface.blit(self.image, draw_pos) # Draw at the potentially offset position