# main.py
# Author: Callum Donnelly
# Date: 2025-04-19 (or update to current date)
# Description: Main entry point for the game. Initializes Pygame,
#              manages the game loop, handles map loading and transitions,
#              and coordinates updates and drawing of game elements.
#
# References Local Files:
#   - config.py: Loads game settings, constants, and file paths.
#   - sprites.py: Uses Player and NPC sprite classes defined therein.

import pygame
import pytmx # For loading Tiled map files (.tmx)
import pyscroll # For rendering Tiled maps efficiently
from pytmx.util_pygame import load_pygame # Pygame-specific Tiled loader utility
from typing import Optional # Used for type hinting optional attributes

# Import from our custom modules
import config  # Game configuration variables
import sprites # Game sprite classes (Player, NPCs, etc.)

class Game:
    """
    Main game controller class.
    Handles the overall game state, including map loading, transitions between maps,
    the main game loop, event handling, updates, and rendering.
    """

    def __init__(self, screen: pygame.Surface) -> None:
        """
        Initializes the Game object.

        Args:
            screen (pygame.Surface): The main display surface provided by Pygame.
        """
        self.screen = screen  # Store the display surface
        self.clock = pygame.time.Clock() # Create a clock object for controlling FPS
        self.running = True # Flag to keep the main game loop active
        self.current_map_key: Optional[str] = None # Key (e.g., 'pier') of the currently loaded map
        self.tmx_data: Optional[pytmx.TiledMap] = None # Holds the loaded Tiled map data
        self.map_layer: Optional[pyscroll.BufferedRenderer] = None # Renderer for the map visuals
        self.group: Optional[pyscroll.PyscrollGroup] = None # Sprite group managed by pyscroll

        # --- Player Initialization ---
        # Define the player's starting position (could be loaded from map data later)
        player_start_x = 700
        player_start_y = 200
        # Create the player instance using the Player class from sprites.py
        self.player = sprites.Player(player_start_x, player_start_y)

        # --- NPC Initialization ---
        # Example: Define Piermaster's starting position
        # These coordinates might eventually come from the Tiled map object layer
        piermaster_start_x = 500
        piermaster_start_y = 400
        # Create the Piermaster instance using the Piermaster class from sprites.py
        self.piermaster = sprites.Piermaster(piermaster_start_x, piermaster_start_y)

        # Note: Other NPCs like the Mayor would be initialized similarly, perhaps
        # conditionally based on the starting map.
        # initialize the mayor's starting position
        mayor_start_x = 550
        mayor_start_y = 450
        self.mayor = sprites.Mayor(mayor_start_x, mayor_start_y)

        # --- Initialize Multiple Houseowner Instances ---
        # Use different coordinates and potentially different image paths from config
        # Make sure the image files referenced in config (e.g., houseowner_type1.png) exist!
        # If they don't exist yet, you can point them all to config.HOUSEOWNER_DEFAULT_IMAGE for now.
        try:
            self.houseowner = sprites.Houseowner(800, 350, config.HOUSEOWNER_DEFAULT_IMAGE)
            self.houseowner1 = sprites.Houseowner(600, 300, config.HOUSEOWNER_ONE_IMAGE)
            self.houseowner2 = sprites.Houseowner(750, 500, config.HOUSEOWNER_TWO_IMAGE)
            # Add more instances as needed
            # self.houseowner3 = sprites.Houseowner(800, 350, config.HOUSEOWNER_THREE_IMAGE)
        except AttributeError as e:
             print(f"Error initializing Houseowners: Make sure image constants like "
                   f"'HOUSEOWNER_ONE_IMAGE' are defined in config.py. Details: {e}")
             # Handle this error appropriately, maybe set them to None or stop the game
             self.houseowner1 = None
             self.houseowner2 = None
             # self.houseowner3 = None



        # --- Initial Map Load ---
        # Load the starting map using its key from the config file
        self.load_map('pier') # Start the game on the 'pier' map

    def load_map(self, map_key: str) -> None:
        """
        Loads and configures a new map based on its key defined in config.py.
        Initializes the Tiled map data, the pyscroll renderer, and the sprite group.

        Args:
            map_key (str): The key identifying the map to load (e.g., 'pier', 'palace').
        """
        print(f"Loading map: {map_key}")
        try:
            # Validate that the map key exists in the configuration
            if map_key not in config.MAP_PATHS:
                raise ValueError(f"Map key '{map_key}' not found in config.MAP_PATHS")

            # --- Load Tiled Map Data ---
            map_path = config.MAP_PATHS[map_key]
            # Use pytmx utility to load the .tmx file into a Pygame-compatible format
            self.tmx_data = load_pygame(map_path)
            # Create map data suitable for pyscroll from the loaded Tiled data
            map_data = pyscroll.TiledMapData(self.tmx_data)

            # --- Configure Pyscroll Renderer ---
            # Create a buffered renderer for efficient map drawing
            self.map_layer = pyscroll.BufferedRenderer(
                map_data,               # The map data to render
                self.screen.get_size(), # The size of the viewable area (screen)
                clamp_camera=True,      # Prevent camera from going outside map boundaries
                alpha=True              # Enable transparency support
            )
            # Set the initial zoom level from the config
            self.map_layer.zoom = config.ZOOM_LEVEL

            # --- Create Pyscroll Sprite Group ---
            # This group handles drawing sprites relative to the scrolling map
            self.group = pyscroll.PyscrollGroup(
                map_layer=self.map_layer,       # Associate with our map renderer
                default_layer=config.DEFAULT_LAYER # Default rendering layer for sprites
            )

            # --- Add Sprites to the Group for the New Map ---
            # Clear previous sprites (except persistent ones like player if needed,
            # but here we re-add player each time). A more complex setup might
            # preserve the player instance across loads.
            self.group.empty() # Ensure the group is clear before adding new sprites

            # Add the player sprite to the group (always present)
            self.group.add(self.player)

            # Conditionally add NPCs based on the loaded map
            if map_key == 'pier':
                 # Only add the Piermaster if the current map is 'pier'
                 # Ensure the piermaster instance exists (it should from __init__)
                 if hasattr(self, 'piermaster'):
                     self.group.add(self.piermaster)
                 else:
                     # Fallback/Error case: Log if piermaster wasn't created earlier
                     print(f"Warning: Piermaster object not found when loading map '{map_key}'")

            elif map_key == 'palace':
                 # Only add the Mayor if the current map is 'palace'
                 # Ensure the mayor instance exists (it should from __init__)
                 if hasattr(self, 'mayor'):
                     # Optional: Set a specific position for the mayor in the palace
                     # self.mayor.rect.center = (config.MAYOR_PALACE_X, config.MAYOR_PALACE_Y) # Example
                     self.group.add(self.mayor)
                 else:
                     # Fallback/Error case: Log if mayor wasn't created earlier
                     print(f"Warning: Mayor object not found when loading map '{map_key}'")

            elif map_key == 'streets':
                 # Add the specific houseowner instances you want on the streets map
                 print(f"Checking for houseowners on map '{map_key}'...") # Debug print
                 if hasattr(self, 'houseowner1') and self.houseowner1:
                     print("Adding houseowner1 to streets map.") # Debug print
                     self.group.add(self.houseowner1)
                 else:
                     print(f"Warning: Houseowner1 object not found or not initialized when loading map '{map_key}'")

                 if hasattr(self, 'houseowner2') and self.houseowner2:
                     print("Adding houseowner2 to streets map.") # Debug print
                     self.group.add(self.houseowner2)
                 else:
                     print(f"Warning: Houseowner2 object not found or not initialized when loading map '{map_key}'")

                 if hasattr(self, 'houseowner') and self.houseowner:
                     print("Adding houseowner to streets map.") # Debug print
                     self.group.add(self.houseowner)
                 else:
                     print(f"Warning: Houseowner object not found or not initialized when loading map '{map_key}'")

            # Update the tracking variable
            self.current_map_key = map_key
            print(f"Map '{map_key}' loaded successfully.")

        # --- Robust Error Handling ---
        except (KeyError, FileNotFoundError, ValueError, pygame.error, Exception) as e:
            print(f"Error loading map '{map_key}': {type(e).__name__} - {e}")
            self.running = False




            # Example: Add other map-specific sprites
            # elif map_key == 'palace':
            #    # Assuming a Mayor sprite exists and its position is known/loaded
            #    # mayor_x, mayor_y = self.get_npc_start_pos('mayor', self.tmx_data)
            #    # self.mayor = sprites.Mayor(mayor_x, mayor_y)
            #    # self.group.add(self.mayor)
            #    pass # Placeholder for palace-specific sprites
            # elif map_key == 'streets':
            #    pass # Placeholder for street-specific sprites

            # Update the tracking variable for the currently loaded map
            self.current_map_key = map_key
            print(f"Map '{map_key}' loaded successfully.")

        # --- Robust Error Handling for Map Loading ---
        except (KeyError, FileNotFoundError, ValueError, pygame.error, Exception) as e: # Removed pytmx.TmxMapError
            # Catch specific expected errors (file not found, invalid key, Tiled issues)
            # and general exceptions during the complex loading process.
            print(f"Error loading map '{map_key}': {type(e).__name__} - {e}")
            # Provide more context for debugging if needed
            # import traceback
            # traceback.print_exc()
            # Stop the game if a map fails to load, as it's likely critical
            self.running = False


    def handle_map_transitions(self) -> None:
        """
        Checks if the player has reached the edge of the current map
        and triggers loading the adjacent map if necessary.
        Also repositions the player appropriately in the new map.
        """
        # Ensure player and map data are available before checking transitions
        if not self.player or not self.current_map_key or not self.group:
             return # Cannot transition without player, map key, or sprite group

        player_rect = self.player.rect
        # Use a buffer zone from the edge to trigger the transition (from config)
        buffer = config.MAP_TRANSITION_BUFFER

        new_map_key: Optional[str] = None
        new_player_pos: Optional[tuple[str, int]] = None # ('side', coordinate)

        # --- Define Transition Logic Based on Current Map and Player Position ---
        # Example: Transition from Pier (Left Edge) to Palace
        if self.current_map_key == 'pier' and player_rect.left <= 0 + buffer: # Check left edge
            print("Transition Trigger: Pier (Left) -> Palace")
            new_map_key = 'palace'
            # Position player near the right edge of the new map
            new_player_pos = ('right', config.SCREEN_WIDTH - buffer)

        # Example: Transition from Palace (Right Edge) back to Pier
        elif self.current_map_key == 'palace' and player_rect.right >= config.SCREEN_WIDTH - buffer: # Check right edge
             print("Transition Trigger: Palace (Right) -> Pier")
             new_map_key = 'pier'
             # Position player near the left edge of the new map
             new_player_pos = ('left', buffer)

        # Example: Transition from Palace (Left Edge) to Streets
        elif self.current_map_key == 'palace' and player_rect.left <= 0 + buffer: # Check left edge
            print("Transition Trigger: Palace (Left) -> Streets")
            new_map_key = 'streets' # Ensure 'streets' key exists in config.MAP_PATHS
            # Position player near the right edge of the new 'streets' map
            new_player_pos = ('right', config.SCREEN_WIDTH - buffer)

        # Example: Transition from Streets (Right Edge) back to Palace
        elif self.current_map_key == 'streets' and player_rect.right >= config.SCREEN_WIDTH - buffer: # Check right edge
            print("Transition Trigger: Streets (Right) -> Palace")
            new_map_key = 'palace'
            # Position player near the left edge of the new 'palace' map
            new_player_pos = ('left', buffer)

        # --- Execute Transition if Triggered ---
        if new_map_key and new_player_pos:
            self.load_map(new_map_key) # Load the new map data and sprites
            # Reposition the player in the newly loaded map
            side, coordinate = new_player_pos
            if side == 'left':
                self.player.rect.left = coordinate
            elif side == 'right':
                self.player.rect.right = coordinate
            elif side == 'top': # Example for vertical transitions
                 self.player.rect.top = coordinate
            elif side == 'bottom': # Example for vertical transitions
                 self.player.rect.bottom = coordinate

            # Crucially, update the hitbox position after moving the main rect
            self.player.hitbox.center = self.player.rect.center
            print(f"Player repositioned at {side}={coordinate} in map '{new_map_key}'")


    def run(self) -> None:
        """Contains the main game loop."""
        print("Starting game loop...")
        while self.running:
            # Calculate delta time (time since last frame) for frame-rate independent movement/physics
            # dt is crucial for smooth updates regardless of FPS fluctuations
            dt = self.clock.tick(config.FPS) / 1000.0 # Convert milliseconds to seconds

            # --- Game Loop Stages ---
            # 1. Handle Events: Process user input (keyboard, mouse, quit)
            self.handle_events()

            # 2. Update State: Update sprite positions, animations, game logic
            self.update(dt) # Pass delta time to the update method

            # 3. Check Transitions: See if map change is needed after updates
            self.handle_map_transitions()

            # 4. Draw Frame: Render the current scene to the screen
            self.draw()

        print("Exiting game loop.") # Message indicating the loop has ended normally

    def handle_events(self) -> None:
        """Processes all events from Pygame's event queue."""
        for event in pygame.event.get():
            # Handle the window close button
            if event.type == pygame.QUIT:
                print("QUIT event detected.")
                self.running = False # Signal the main loop to exit

            # --- Add other event handling as needed ---
            # Example: Handling key presses for actions other than movement
            # elif event.type == pygame.KEYDOWN:
            #     if event.key == pygame.K_SPACE:
            #         print("Action key (Space) pressed!")
            #         # Trigger interaction, attack, jump, etc.
            #     elif event.key == pygame.K_ESCAPE:
            #         print("Escape key pressed.")
            #         # Could open a menu or quit
            #         # self.running = False
            # Example: Mouse clicks
            # elif event.type == pygame.MOUSEBUTTONDOWN:
            #     if event.button == 1: # Left mouse button
            #         print(f"Left mouse click at {event.pos}")

    def update(self, dt: float) -> None:
        """
        Updates the state of all active game objects for the current frame.
        This includes updating sprites and centering the camera.

        Args:
            dt (float): Delta time (time since the last frame in seconds).
                        Used for frame-rate independent calculations.
        """
        # Only perform updates if a map and sprite group are loaded
        if self.group:
            # Update all sprites within the pyscroll group.
            # This calls the 'update' method of each sprite in the group (e.g., Player.update).
            # Pass delta time (dt) to sprite update methods if they need it for physics/timing.
            self.group.update(dt)

            # Center the map view (camera) on the player's current position.
            # pyscroll handles the scrolling based on this center point.
            self.group.center(self.player.rect.center)

    def draw(self) -> None:
        """Renders the current game scene to the screen."""
        # Ensure the map renderer and sprite group are ready
        if self.group and self.map_layer:
            # --- Drawing Order ---
            # 1. Optional: Fill background (usually not needed if map covers screen)
            # self.screen.fill(config.BACKGROUND_COLOR) # Example if needed

            # 2. Draw the map and all sprites within the group.
            # pyscroll's group.draw() handles drawing the map layer scrolled
            # correctly and then drawing each sprite at its position relative
            # to the map.
            self.group.draw(self.screen)

            # 3. Optional: Draw UI elements (HUD, menus, debug info) on top.
            # These are drawn after the map/sprites so they appear over them.
            # Example:
            # font = pygame.font.Font(None, 30)
            # fps_text = font.render(f"FPS: {self.clock.get_fps():.1f}", True, (255, 255, 255))
            # self.screen.blit(fps_text, (10, 10))

            # 4. Update the full display surface to show the newly drawn frame.
            pygame.display.flip()

        elif not self.running:
             # Optional: If the game stopped due to an error during loading,
             # you might want to display an error message on the screen here.
             # font = pygame.font.Font(None, 50)
             # error_text = font.render("Error loading game assets!", True, (255, 0, 0))
             # text_rect = error_text.get_rect(center=self.screen.get_rect().center)
             # self.screen.fill((0, 0, 0)) # Black background
             # self.screen.blit(error_text, text_rect)
             # pygame.display.flip() # Show the error message
             pass # Currently does nothing if not running and draw is called


def main() -> None:
    """
    Main function to initialize Pygame, set up the screen,
    create the Game instance, and start the game execution.
    Includes error handling for the main game run.
    """
    print("Initializing Pygame...")
    pygame.init() # Initialize all Pygame modules
    print("Pygame initialized successfully.")

    # Set up the display window using dimensions from the config file
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    # Set the title of the window
    pygame.display.set_caption("Pier to the Past Game") # Keep your game title

    try:
        print("Creating Game instance...")
        game = Game(screen) # Create the main game object
        print("Starting game run...")
        game.run() # Start the main game loop

    except Exception as e:
        # Catch any unexpected errors that occur during game initialization or run
        print(f"\n--- An unexpected error occurred during game execution ---")
        print(f"{type(e).__name__}: {e}")
        # Print the full traceback for detailed debugging
        import traceback
        traceback.print_exc()
        print("----------------------------------------------------------")

    finally:
        # This block ensures Pygame is quit properly, even if errors occurred
        print("Quitting Pygame...")
        pygame.quit()
        print("Pygame quit successfully.")
        # Optional: Force exit the script, especially useful if Pygame hangs on quit
        # import sys
        # sys.exit()

# Standard Python entry point check:
# Ensures that the main() function is called only when the script is executed directly
if __name__ == "__main__":
    main()
