# main.py

import pygame
import pytmx # Keep this import
import pyscroll
from pytmx.util_pygame import load_pygame
from typing import Optional # Keep if needed, maybe not directly now

# Import from our new modules
import config
import sprites

class Game:
    """Main game controller handling map loading, transitions, and game loop."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_map_key: Optional[str] = None # Track current map key
        self.tmx_data: Optional[pytmx.TiledMap] = None
        self.map_layer: Optional[pyscroll.BufferedRenderer] = None
        self.group: Optional[pyscroll.PyscrollGroup] = None

        # Initialize sprites using classes from sprites.py
        # Define starting positions (could also come from map data later)
        player_start_x = 100
        player_start_y = 50
        self.player = sprites.Player(player_start_x, player_start_y)

        # Example: Place Piermaster based on config or map data later
        piermaster_start_x = config.SCREEN_WIDTH // 4
        piermaster_start_y = config.SCREEN_HEIGHT // 2
        self.piermaster = sprites.Piermaster(piermaster_start_x, piermaster_start_y)

        # Load initial map using key from config
        self.load_map('pier') # Start with the pier map

    def load_map(self, map_key: str) -> None:
        """Load and configure a new map based on its key."""
        print(f"Loading map: {map_key}")
        try:
            if map_key not in config.MAP_PATHS:
                raise ValueError(f"Map key '{map_key}' not found in config.MAP_PATHS")

            map_path = config.MAP_PATHS[map_key]
            self.tmx_data = load_pygame(map_path)
            map_data = pyscroll.TiledMapData(self.tmx_data)

            # Configure rendering using constants from config
            self.map_layer = pyscroll.BufferedRenderer(
                map_data,
                self.screen.get_size(),
                clamp_camera=True,
                alpha=True # Enable alpha for potential transparency effects
            )
            self.map_layer.zoom = config.ZOOM_LEVEL

            # Create sprite group for the new map
            self.group = pyscroll.PyscrollGroup(
                map_layer=self.map_layer,
                default_layer=config.DEFAULT_LAYER
            )

            # --- Important: Add sprites to the group ---
            # Decide which sprites belong on which map
            self.group.add(self.player) # Player is usually on all maps

            if map_key == 'pier':
                 # Only add piermaster if the current map is 'pier'
                 # Make sure piermaster instance exists if needed here
                 if not hasattr(self, 'piermaster'):
                      # Or load/create it based on map data
                      piermaster_start_x = config.SCREEN_WIDTH // 4
                      piermaster_start_y = config.SCREEN_HEIGHT // 2
                      self.piermaster = sprites.Piermaster(piermaster_start_x, piermaster_start_y)
                 self.group.add(self.piermaster)
            # Add other map-specific sprites here
            # elif map_key == 'palace':
            #    self.group.add(sprites.Mayor(x, y)) # Example

            self.current_map_key = map_key  # Update current map key

        # Catch specific expected errors and general exceptions during loading
        except (KeyError, FileNotFoundError, ValueError, pytmx.TmxMapError, pygame.error, Exception) as e:
            # Note: Changed pytmx.exceptions.TmxException based on previous discussion
            # Using pytmx.TmxMapError might be more specific if available and desired
            # Added ValueError for the explicit check
            # Added pygame.error for potential image loading issues within pytmx/pyscroll
            # Added base Exception to catch unexpected issues during complex loading
            print(f"Error loading map '{map_key}': {type(e).__name__} - {e}")
            # Optionally, provide more context or traceback here
            # import traceback
            # traceback.print_exc()
            self.running = False # Stop game on critical loading error

    def handle_map_transitions(self) -> None:
        """Check for and execute map transitions based on player position."""
        if not self.player or not self.current_map_key:
             return # Cannot transition without player or current map

        player_rect = self.player.rect
        buffer = config.MAP_TRANSITION_BUFFER # Use constant

        # --- Define transitions based on current map ---
        if self.current_map_key == 'pier' and player_rect.left <= 0:
            print("Transitioning from pier (left) to palace")
            self.load_map('palace')
            # Position player on the right side of the new map
            self.player.rect.right = config.SCREEN_WIDTH - buffer
            self.player.hitbox.center = self.player.rect.center # Update hitbox pos

        elif self.current_map_key == 'palace' and player_rect.right >= config.SCREEN_WIDTH:
             print("Transitioning from palace (right) to pier")
             self.load_map('pier')
             # Position player on the left side of the new map
             self.player.rect.left = buffer
             self.player.hitbox.center = self.player.rect.center # Update hitbox pos

        # Add more transitions here (e.g., palace <-> streets)
        # elif self.current_map_key == 'palace' and player_rect.left <= 0:
        #     print("Transitioning from palace (left) to streets")
        #     self.load_map('streets')
        #     self.player.rect.right = config.SCREEN_WIDTH - buffer
        #     self.player.hitbox.center = self.player.rect.center

        # elif self.current_map_key == 'streets' and player_rect.right >= config.SCREEN_WIDTH:
        #     print("Transitioning from streets (right) to palace")
        #     self.load_map('palace')
        #     self.player.rect.left = buffer
        #     self.player.hitbox.center = self.player.rect.center


    def run(self) -> None:
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0 # Delta time in seconds

            self.handle_events()
            self.update(dt) # Pass delta time to update if needed for physics later
            self.handle_map_transitions() # Check transitions after update
            self.draw()

        print("Exiting game.") # Add a message when the loop ends

    def handle_events(self) -> None:
        """Handle user input and system events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            # Add other event handling (e.g., key presses for actions) here
            # elif event.type == pygame.KEYDOWN:
            #     if event.key == pygame.K_SPACE:
            #         print("Action key pressed!")

    def update(self, dt: float) -> None:
        """Update game state (sprites, camera)."""
        # Only update if a map/group is loaded
        if self.group:
            self.group.update(dt) # Pass dt to sprites' update methods
            self.group.center(self.player.rect.center) # Keep camera centered

    def draw(self) -> None:
        """Render the current scene."""
        if self.group and self.map_layer:
            # A common pattern is:
            # 1. Fill background (optional, map usually covers it)
            # self.screen.fill((0, 0, 0)) # Black background if map has gaps

            # 2. Draw the map layer
            self.group.draw(self.screen)

            # 3. Draw UI elements on top (if any)
            # Example: draw_debug_info(self.screen, self.player)

            # 4. Flip the display
            pygame.display.flip()
        elif not self.running:
             # Maybe show an error screen if running is false due to load error
             pass


def main() -> None:
    """Initialize Pygame, create Game instance, and run the game."""
    pygame.init()
    print("Pygame initialized.")

    # Use constants from config for screen dimensions
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Pier to the Past Game") # Keep caption

    try:
        print("Starting game...")
        game = Game(screen)
        game.run()
    except Exception as e:
        print(f"\n--- An unexpected error occurred during game execution ---")
        print(f"{type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        print("----------------------------------------------------------")
    finally:
        print("Quitting Pygame.")
        pygame.quit()
        # import sys
        # sys.exit() # Ensure exit if error occurred

if __name__ == "__main__":
    main()
