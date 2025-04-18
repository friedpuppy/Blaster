# sprites.py

import pygame
import config  # Import the configuration

class Player(pygame.sprite.Sprite):
    """Player character controlled by arrow keys with collision-aware movement."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        try:
            self.image = pygame.image.load(config.PLAYER_IMAGE).convert_alpha()
        except pygame.error as e:
            print(f"Error loading player image: {config.PLAYER_IMAGE} - {e}")
            # Provide a fallback surface or raise the error
            self.image = pygame.Surface((config.TILE_SIZE, config.TILE_SIZE))
            self.image.fill((255, 0, 0)) # Red square as fallback
            # raise # Or re-raise the exception if loading is critical

        self.rect = self.image.get_rect(topleft=(x, y))
        # Use constants from config for hitbox inflation
        self.hitbox = self.rect.inflate(config.PLAYER_HITBOX_INFLATE_X,
                                         config.PLAYER_HITBOX_INFLATE_Y)
        self.speed = config.PLAYER_SPEED

    def update(self, *args, **kwargs) -> None:
        """Update player position based on key presses with normalized diagonal movement."""
        keys = pygame.key.get_pressed()
        dx, dy = 0.0, 0.0 # Use floats for potentially fractional movement

        # Calculate movement direction
        if keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_UP]:
            dy -= 1

        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= config.PLAYER_DIAGONAL_SPEED_FACTOR
            dy *= config.PLAYER_DIAGONAL_SPEED_FACTOR

        # Apply speed and move
        # Use round() to convert back to integer pixel coordinates for move_ip
        self.rect.move_ip(round(dx * self.speed), round(dy * self.speed))
        self.hitbox.center = self.rect.center # Keep hitbox centered on the visual rect

class Piermaster(pygame.sprite.Sprite):
    """NPC character with fixed position."""

    def __init__(self, x: int, y: int) -> None: # Allow specifying position
        super().__init__()
        try:
            self.image = pygame.image.load(config.PIERMASTER_IMAGE).convert_alpha()
        except pygame.error as e:
            print(f"Error loading piermaster image: {config.PIERMASTER_IMAGE} - {e}")
            self.image = pygame.Surface((config.TILE_SIZE, config.TILE_SIZE))
            self.image.fill((0, 0, 255)) # Blue square as fallback
            # raise

        self.rect = self.image.get_rect(center=(x, y)) # Use passed coordinates

    # No update needed for a static NPC unless it animates or moves later
    # def update(self, *args, **kwargs) -> None:
    #     pass

# --- Add other sprite classes here (e.g., Mayor) ---
# class Mayor(pygame.sprite.Sprite):
#     def __init__(self, x: int, y: int) -> None:
#         super().__init__()
#         # ... load image using config.MAYOR_IMAGE ...
#         self.rect = self.image.get_rect(center=(x, y))