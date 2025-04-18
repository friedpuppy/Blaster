"""
main.py - 2D Tile-based Game using Pygame and Pytmx (Modified for left-edge transitions)

Features:
- Tilemap loading and rendering using pyscroll
- Player movement with arrow keys
- Left-edge map transitions
- Camera following player
- Sprite management for player and NPC

Author: Ron
Date: 2025-04-08
Modified: 2025-04-08 (Added transitions between maps)
"""

import pygame
import pytmx
import pyscroll
from pytmx.util_pygame import load_pygame
from typing import Optional, List

# Game Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
ZOOM_LEVEL = 1
DEFAULT_LAYER = 1
TILE_SIZE = 32

# File paths (consider using relative paths or config file)
PIERMASTER_IMAGE = './Assets/Images/piermaster.png'
PLAYER_IMAGE = './Assets/Images/gentleman.png'
MAYOR_IMAGE = './Assets/Images/mayor.png'
MAP_PATHS = {
    'pier': "./Assets/Maps/pier_map.tmx",
    'palace': "./Assets/Maps/palace_map.tmx",
    'streets': "./Assets/Maps/streets_map.tmx"
}

class Player(pygame.sprite.Sprite):
    """Player character controlled by arrow keys with collision-aware movement."""
    
    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image = pygame.image.load(PLAYER_IMAGE).convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hitbox = self.rect.inflate(-8, -8)  # Tighter collision detection
        self.speed = 5

    def update(self, *args, **kwargs) -> None:
        """Update player position with normalized diagonal movement."""
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        
        dx += keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
        dy += keys[pygame.K_DOWN] - keys[pygame.K_UP]
        
        # Normalize diagonal movement
        if dx and dy:
            dx *= 0.7071  # 1/√2 approximation
            dy *= 0.7071
            
        self.rect.move_ip(dx * self.speed, dy * self.speed)
        self.hitbox.center = self.rect.center

class Piermaster(pygame.sprite.Sprite):
    """NPC character with fixed position."""
    
    def __init__(self) -> None:
        super().__init__()
        self.image = pygame.image.load(PIERMASTER_IMAGE).convert_alpha()
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH//4, SCREEN_HEIGHT//2))

class Game:
    """Main game controller handling map transitions and game loop."""
    
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_map = None  # Track current map
        
        # Initialize sprites
        self.player = Player(100, 50)
        self.piermaster = Piermaster()
        
        # Load initial map using key
        self.load_map('pier')

    def load_map(self, map_key: str) -> None:
        """Load and configure new map with error handling."""
        try:
            map_path = MAP_PATHS[map_key]
            self.tmx_data = load_pygame(map_path)
            map_data = pyscroll.TiledMapData(self.tmx_data)
            
            # Configure rendering
            self.map_layer = pyscroll.BufferedRenderer(
                map_data, 
                self.screen.get_size(),
                clamp_camera=True
            )
            self.map_layer.zoom = ZOOM_LEVEL
            
            # Create sprite group
            self.group = pyscroll.PyscrollGroup(
                map_layer=self.map_layer,
                default_layer=DEFAULT_LAYER
            )
            self.group.add(self.player, self.piermaster)
            
            self.current_map = map_key  # Update current map
            
        except (KeyError, FileNotFoundError, pytmx.exceptions.TmxException) as e:
            print(f"Map loading error: {str(e)}")
            self.running = False

    def run(self) -> None:
        """Main game loop with frame rate control."""
        while self.running:
            self.handle_events()
            self.update()
            
            # Handle map transitions
            if self.current_map == 'pier' and self.player.rect.x <= 0:
                # Transition to palace on left edge
                self.load_map('palace')
                self.player.rect.x = SCREEN_WIDTH - 30  # Right side of palace
            elif self.current_map == 'palace' and self.player.rect.x >= SCREEN_WIDTH - 30:
                # Transition back to sea on right edge
                self.load_map('pier')
                self.player.rect.x = 30  # Left side of sea
            
            self.draw()
            self.clock.tick(FPS)

    def handle_events(self) -> None:
        """Handle system events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self) -> None:
        """Update game state."""
        if self.group:
            self.group.update()
            self.group.center(self.player.rect.center)

    def draw(self) -> None:
        """Render all game elements."""
        if self.group:
            self.group.draw(self.screen)
            pygame.display.flip()

def main() -> None:
    """Initialize and run the game."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pier to the Past Game")
    Game(screen).run()
    pygame.quit()

if __name__ == "__main__":
    main()