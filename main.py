# main.py
# Author: Callum Donnelly
# Date: 2025-04-30 (or update to current date)
# Description: Main entry point for the game. Initializes Pygame,
#              manages the game loop, handles map loading and transitions,
#              and coordinates updates and drawing of game elements.
#
# References Local Files:
#   - config.py: Loads game settings, constants, and file paths.
#   - sprites.py: Uses Player and NPC sprite classes defined therein.
#   - dialogue.py: Uses Cutscene class and collision_cutscenes data.

import pygame
import pytmx # For loading Tiled map files (.tmx)
import pyscroll # For rendering Tiled maps efficiently
from pytmx.util_pygame import load_pygame # Pygame-specific Tiled loader utility
from typing import Optional, Dict, List # Used for type hinting
# Import necessary classes/data from dialogue.py
from dialogue import DialogueBox, dialogues, Cutscene, collision_cutscenes, render_textrect, TextRectException


# Import from our custom modules
import config  # Game configuration variables
import sprites # Game sprite classes (Player, NPCs, etc.)

# --- TriggerSprite class is removed as it's no longer needed ---

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
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_map_key: Optional[str] = None
        self.tmx_data: Optional[pytmx.TiledMap] = None
        self.map_layer: Optional[pyscroll.BufferedRenderer] = None
        self.group: Optional[pyscroll.PyscrollGroup] = None
        # Keep track of the last tile's properties for event triggering
        self.last_event_tile_properties: Optional[Dict] = None

        # --- Game State ---
        self.game_state: str = 'playing' # 'playing', 'cutscene', 'paused', etc.

        # --- Cutscene State Variables ---
        self.active_cutscene: Optional[Cutscene] = None
        self.current_cutscene_slide: int = 0
        self.cutscene_image_surface: Optional[pygame.Surface] = None
        self.cutscene_text_surface: Optional[pygame.Surface] = None
        # Removed the cutscene_triggers group
        self.triggered_cutscenes = set() # Keep track of which cutscenes have been played (per map load)

        # --- Font Initialization ---
        try:
            # Font for general UI (like FPS counter)
            self.ui_font = pygame.font.Font(None, 30)
            # Font specifically for cutscene text (can be different)
            self.cutscene_font = pygame.font.Font(None, 28) # Example size
            print("UI and Cutscene Fonts initialized.")
        except pygame.error as e:
            print(f"Error initializing fonts: {e}")
            self.ui_font = None
            self.cutscene_font = None
            self.running = False # Stop if fonts fail

        # --- Player Initialization ---
        player_start_x = 700
        player_start_y = 200
        self.player = sprites.Player(player_start_x, player_start_y)

        # --- NPC Initialization ---
        piermaster_start_x = 500
        piermaster_start_y = 400
        self.piermaster = sprites.Piermaster(piermaster_start_x, piermaster_start_y)
        mayor_start_x = 550
        mayor_start_y = 450
        self.mayor = sprites.Mayor(mayor_start_x, mayor_start_y)
        try:
            self.houseowner0 = sprites.Houseowner(100, 105, config.HOUSEOWNER_DEFAULT_IMAGE)
            self.houseowner1 = sprites.Houseowner(350, 105, config.HOUSEOWNER_ONE_IMAGE)
            self.houseowner2 = sprites.Houseowner(650, 105, config.HOUSEOWNER_TWO_IMAGE)
            self.houseowner3 = sprites.Houseowner(920, 105, config.HOUSEOWNER_THREE_IMAGE)
        except AttributeError as e:
             print(f"Error initializing Houseowners: {e}")
             self.houseowner0 = self.houseowner1 = self.houseowner2 = self.houseowner3 = None

        # --- Dialogue Box Initialization (for testing/other uses) ---
        dialogue_box_x = (config.SCREEN_WIDTH / 2) - 300
        dialogue_box_y = config.SCREEN_HEIGHT - 250
        test_message = "Test Dialogue Box (Press T)"
        self.test_dialogue_box = DialogueBox(self, test_message, dialogue_box_x, dialogue_box_y)

        # --- Initial Map Load ---
        self.load_map('pier') # Start on the pier map

    def load_map(self, map_key: str) -> None:
        """Loads and configures a new map."""
        print(f"Loading map: {map_key}")
        try:
            if map_key not in config.MAP_PATHS:
                raise ValueError(f"Map key '{map_key}' not found in config.MAP_PATHS")

            map_path = config.MAP_PATHS[map_key]
            self.tmx_data = load_pygame(map_path)
            map_data = pyscroll.TiledMapData(self.tmx_data)

            self.map_layer = pyscroll.BufferedRenderer(
                map_data, self.screen.get_size(), clamp_camera=True, alpha=True
            )
            self.map_layer.zoom = config.ZOOM_LEVEL

            self.group = pyscroll.PyscrollGroup(
                map_layer=self.map_layer, default_layer=config.DEFAULT_LAYER
            )

            # --- Clear Previous Sprites ---
            self.group.empty()
            # Reset triggered cutscenes for the new map
            self.triggered_cutscenes.clear()
            # Reset last tile properties
            self.last_event_tile_properties = None

            # --- Add Player ---
            self.group.add(self.player)

            # --- Add NPCs Based on Map ---
            if map_key == 'pier' and hasattr(self, 'piermaster'):
                self.group.add(self.piermaster)
            elif map_key == 'palace' and hasattr(self, 'mayor'):
                self.group.add(self.mayor)
            elif map_key == 'streets':
                # Add houseowners if they exist
                for ho in [self.houseowner0, self.houseowner1, self.houseowner2, self.houseowner3]:
                    if ho: self.group.add(ho)

                # --- Object Trigger Loading is Removed ---

            self.current_map_key = map_key
            print(f"Map '{map_key}' loaded successfully.")

        except (KeyError, FileNotFoundError, ValueError, pygame.error, Exception) as e:
            print(f"Error loading map '{map_key}': {type(e).__name__} - {e}")
            import traceback
            traceback.print_exc()
            self.running = False

    def check_tile_events(self) -> None:
        """
        Checks the tile the player is standing on in the 'EventsMap' layer
        for custom properties like 'Door' or 'CutsceneTrigger'.
        Triggers events or cutscenes based on these properties.
        """
        if not self.tmx_data or not self.player or self.game_state != 'playing':
            # Only check when playing and map/player are loaded
            return

        current_tile_properties: Optional[Dict] = None
        event_layer_name = "EventsMap" # Make sure this layer exists in your TMX

        # Initialize tile coordinates before the try block
        tile_x, tile_y = -1, -1 # Use placeholder values

        try:
            event_layer = self.tmx_data.get_layer_by_name(event_layer_name)
            event_layer_index = self.tmx_data.layers.index(event_layer)

            # Use player's hitbox center for tile checking
            tile_x = self.player.hitbox.centerx // self.tmx_data.tilewidth
            tile_y = self.player.hitbox.centery // self.tmx_data.tileheight

            # Ensure coordinates are within map bounds
            if 0 <= tile_x < self.tmx_data.width and 0 <= tile_y < self.tmx_data.height:
                 current_tile_properties = self.tmx_data.get_tile_properties(
                     tile_x, tile_y, event_layer_index
                 )
                 # If get_tile_properties returns None (empty tile), treat as empty dict
                 if current_tile_properties is None:
                     current_tile_properties = {}
            else:
                 # Player is outside map bounds for tile checking
                 current_tile_properties = {}


        except (ValueError, AttributeError, IndexError) as e: # Catch specific exceptions
             # Layer not found, player not ready, index error, or other issues getting properties
             # The print statement can now safely use tile_x and tile_y (even if they are -1)
             print(f"Warning: Could not get tile properties at ({tile_x},{tile_y}) on layer '{event_layer_name}'. Error: {e}")
             current_tile_properties = {} # Treat as no properties found

        # --- Compare current tile properties with the last frame's ---
        if current_tile_properties != self.last_event_tile_properties:
            # --- Handle 'Door' Property (Example) ---
            current_door = current_tile_properties.get('Door')
            last_door = self.last_event_tile_properties.get('Door') if self.last_event_tile_properties else None
            if current_door is not None and current_door != last_door:
                print(f"Player entered event tile with Door: {current_door}")
                # Add logic for door interaction if needed

            # --- Handle 'CutsceneTrigger' Property ---
            current_trigger_key = current_tile_properties.get('CutsceneTrigger')
            last_trigger_key = self.last_event_tile_properties.get('CutsceneTrigger') if self.last_event_tile_properties else None

            # Check if we stepped onto a NEW tile with a CutsceneTrigger
            if current_trigger_key is not None and current_trigger_key != last_trigger_key:
                print(f"Player entered tile with CutsceneTrigger: {current_trigger_key}")
                # Check if the cutscene exists and hasn't been played on this map load
                if current_trigger_key in collision_cutscenes and current_trigger_key not in self.triggered_cutscenes:
                    self.start_cutscene(current_trigger_key)
                elif current_trigger_key in self.triggered_cutscenes:
                     print(f"  Cutscene '{current_trigger_key}' already triggered on this map load.")
                elif current_trigger_key not in collision_cutscenes:
                     print(f"  Warning: Tile has CutsceneTrigger '{current_trigger_key}', but no matching cutscene found in dialogue.py.")

            # --- Update the last known properties for the next frame ---
            self.last_event_tile_properties = current_tile_properties


    def handle_map_transitions(self) -> None:
        """Checks for map transitions."""
        if not self.player or not self.current_map_key or not self.group:
             return

        player_rect = self.player.rect
        buffer = config.MAP_TRANSITION_BUFFER
        new_map_key: Optional[str] = None
        new_player_pos: Optional[tuple[str, int]] = None

        # --- Transition Logic ---
        if self.current_map_key == 'pier' and player_rect.left <= 0 + buffer:
            new_map_key = 'palace'
            new_player_pos = ('right', config.SCREEN_WIDTH - buffer)
        elif self.current_map_key == 'palace' and player_rect.right >= config.SCREEN_WIDTH - buffer:
             new_map_key = 'pier'
             new_player_pos = ('left', buffer)
        elif self.current_map_key == 'palace' and player_rect.left <= 0 + buffer:
            new_map_key = 'streets'
            new_player_pos = ('right', config.SCREEN_WIDTH - buffer)
        elif self.current_map_key == 'streets' and player_rect.right >= config.SCREEN_WIDTH - buffer:
            new_map_key = 'palace'
            new_player_pos = ('left', buffer)
        # Add other transitions (e.g., top/bottom) if needed

        # --- Execute Transition ---
        if new_map_key and new_player_pos:
            print(f"Transition Trigger: {self.current_map_key} -> {new_map_key}")
            self.load_map(new_map_key) # This will reset triggered_cutscenes and last_event_tile_properties
            side, coordinate = new_player_pos
            if side == 'left': self.player.rect.left = coordinate
            elif side == 'right': self.player.rect.right = coordinate
            elif side == 'top': self.player.rect.top = coordinate
            elif side == 'bottom': self.player.rect.bottom = coordinate
            self.player.hitbox.center = self.player.rect.center
            print(f"Player repositioned at {side}={coordinate} in map '{new_map_key}'")

    # --- Cutscene Methods ---

    def start_cutscene(self, cutscene_key: str) -> None:
        """Initiates a cutscene based on the provided key."""
        if self.game_state == 'cutscene':
            print("Warning: Tried to start a cutscene while one is already active.")
            return # Don't start a new one if already in a cutscene

        if cutscene_key in collision_cutscenes:
            print(f"Starting cutscene: {cutscene_key}")
            self.active_cutscene = collision_cutscenes[cutscene_key]
            self.current_cutscene_slide = 0
            self.game_state = 'cutscene'
            self.triggered_cutscenes.add(cutscene_key) # Mark as played for this map load
            self._load_cutscene_slide() # Load the first slide's assets
        else:
            # This case should be less likely now as the check happens in check_tile_events
            print(f"Error: Attempted to start unknown cutscene key: {cutscene_key}")

    def _load_cutscene_slide(self) -> None:
        """Loads the image and renders the text for the current cutscene slide."""
        if not self.active_cutscene or not self.cutscene_font:
            self._end_cutscene()
            return

        slide_index = self.current_cutscene_slide
        if 0 <= slide_index < self.active_cutscene.num_slides:
            # --- Load and Scale Image to Fullscreen ---
            image_path = self.active_cutscene.image_paths[slide_index]
            self.cutscene_image_surface = None # Reset previous image
            if image_path:
                try:
                    loaded_image = pygame.image.load(image_path).convert() # Use convert() if no alpha needed for background
                    # Scale the image to fit the entire screen
                    self.cutscene_image_surface = pygame.transform.smoothscale(
                        loaded_image, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
                    )
                except pygame.error as e:
                    print(f"Error loading/scaling cutscene image '{image_path}': {e}")
                    # Optional: Create a fallback black surface if loading fails
                    self.cutscene_image_surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
                    self.cutscene_image_surface.fill(config.BLACK)
                except FileNotFoundError:
                    print(f"Error: Cutscene image file not found: '{image_path}'")
                    # Optional: Create a fallback black surface if file not found
                    self.cutscene_image_surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
                    self.cutscene_image_surface.fill(config.BLACK)
            else:
                 # If image_path is None, create a black background surface
                 self.cutscene_image_surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
                 self.cutscene_image_surface.fill(config.BLACK)


            # --- Render Text (remains the same) ---
            text = self.active_cutscene.sentences[slide_index]
            self.cutscene_text_surface = None # Reset previous text
            if text:
                text_margin = 50
                text_box_height = 150
                text_rect = pygame.Rect(
                    text_margin,
                    self.screen.get_height() - text_box_height - text_margin,
                    self.screen.get_width() - (text_margin * 2),
                    text_box_height
                )
                try:
                    self.cutscene_text_surface = render_textrect(
                        text,
                        self.cutscene_font,
                        text_rect,
                        config.WHITE,
                        config.DARK_GRAY, # Background for the text box itself
                        justification=0
                    )
                except TextRectException as e:
                    print(f"Error rendering cutscene text: {e}")
                    self.cutscene_text_surface = self.cutscene_font.render("Text Error", True, config.WHITE, config.DARK_GRAY)
                except Exception as e:
                     print(f"Unexpected error rendering cutscene text: {e}")
                     self.cutscene_text_surface = self.cutscene_font.render("Render Error", True, config.WHITE, config.DARK_GRAY)

        else:
            print(f"Warning: Invalid slide index ({slide_index}) requested.")
            self._end_cutscene()


    def _advance_cutscene_slide(self) -> None:
        """Moves to the next slide or ends the cutscene."""
        if not self.active_cutscene: return

        self.current_cutscene_slide += 1
        if self.current_cutscene_slide >= self.active_cutscene.num_slides:
            self._end_cutscene()
        else:
            self._load_cutscene_slide() # Load the next slide

    def _end_cutscene(self) -> None:
        """Cleans up after a cutscene finishes and returns to gameplay."""
        print("Ending cutscene.")
        self.game_state = 'playing'
        self.active_cutscene = None
        self.current_cutscene_slide = 0
        self.cutscene_image_surface = None
        self.cutscene_text_surface = None
        # Optional: Add a small delay before player can move again?
        # pygame.time.wait(200) # e.g., 200ms pause

    # --- Main Game Loop Methods ---

    def run(self) -> None:
        """Contains the main game loop."""
        print("Starting game loop...")
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0

            # --- Game Loop Stages ---
            self.handle_events()
            self.update(dt)
            self.draw()

        print("Exiting game loop.")

    def handle_events(self) -> None:
        """Processes all events from Pygame's event queue."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.game_state == 'playing':
                # Handle gameplay input (movement is handled in Player.update)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t: # Toggle test dialogue
                        print("T key pressed - Toggling test dialogue box.")
                        self.test_dialogue_box.toggle()
                    # Add other gameplay keybinds here (e.g., interaction key)

            elif self.game_state == 'cutscene':
                # Handle cutscene input (only Enter key)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN: # ENTER key
                        print("Enter pressed - Advancing cutscene.")
                        self._advance_cutscene_slide()
                    elif event.key == pygame.K_ESCAPE: # Optional: Allow skipping cutscene
                        print("Escape pressed - Ending cutscene early.")
                        self._end_cutscene()

    def update(self, dt: float) -> None:
        """Updates the game state based on the current game_state."""
        if self.game_state == 'playing':
            if self.group:
                # Update sprites (includes player movement)
                self.group.update(dt)
                # Center camera on player
                self.group.center(self.player.rect.center)
                # Check for tile-based events (including cutscene triggers)
                self.check_tile_events() # <--- This now handles cutscene triggers
                # Check for map transitions
                self.handle_map_transitions()

                # --- Collision check for triggers is removed ---

        elif self.game_state == 'cutscene':
            # No game world updates happen during a cutscene
            pass

    def draw(self) -> None:
        """Renders the current game scene based on the game_state."""
        if self.game_state == 'playing':
            # --- Draw Gameplay Scene (remains the same) ---
            if self.group and self.map_layer:
                self.group.draw(self.screen)

                # --- Draw UI Elements ---
                #if self.ui_font:
                #    fps_text = f"FPS: {self.clock.get_fps():.1f}"
                #    fps_surf = self.ui_font.render(fps_text, True, config.WHITE)
                #    self.screen.blit(fps_surf, (10, 10))

                # Draw test dialogue box if active
                if hasattr(self, 'test_dialogue_box'):
                    self.test_dialogue_box.draw(self.screen)

                # --- DEBUG: Draw Player Hitbox ---
                # pygame.draw.rect(self.screen, (255, 0, 0), self.player.hitbox, 1)


        elif self.game_state == 'cutscene':
            # --- Draw Cutscene Scene ---

            # 1. Draw the fullscreen background image first
            if self.cutscene_image_surface:
                self.screen.blit(self.cutscene_image_surface, (0, 0))
            else:
                # Fallback if image surface somehow wasn't created
                self.screen.fill(config.BLACK)

            # 2. Draw Text Box on top of the image
            if self.cutscene_text_surface:
                 # Calculate position for the text box (same as before)
                text_margin = 50
                text_box_height = 150
                text_rect = pygame.Rect(
                    text_margin,
                    self.screen.get_height() - text_box_height - text_margin,
                    self.screen.get_width() - (text_margin * 2),
                    text_box_height
                )
                # Blit the rendered text surface onto the screen
                self.screen.blit(self.cutscene_text_surface, text_rect.topleft)

            # 3. Draw "Press Enter" prompt on top
            if self.ui_font:
                 prompt_text = "Press ENTER to continue..."
                 prompt_surf = self.ui_font.render(prompt_text, True, config.WHITE)
                 # Position prompt at the bottom-center
                 prompt_rect = prompt_surf.get_rect(centerx=self.screen.get_width() // 2, bottom=self.screen.get_height() - 20)
                 # Optional: Add a slight shadow/background for better visibility on complex images
                 # shadow_surf = self.ui_font.render(prompt_text, True, config.BLACK)
                 # self.screen.blit(shadow_surf, prompt_rect.move(1,1)) # Offset shadow slightly
                 self.screen.blit(prompt_surf, prompt_rect)


        # Update the display regardless of state
        pygame.display.flip()


def main() -> None:
    """Main function to initialize and run the game."""
    print("Initializing Pygame...")
    pygame.init()
    print("Pygame initialized successfully.")

    # --- Set the Window Icon ---
    try:
        # Construct the full path to the icon using config
        icon_path = f"{config.IMAGES_DIR}/game_icon.png" # Or your actual icon filename
        icon_surface = pygame.image.load(icon_path)
        pygame.display.set_icon(icon_surface)
        print(f"Window icon set from: {icon_path}")
    except pygame.error as e:
        print(f"Warning: Could not load or set window icon: {e}")
    except FileNotFoundError:
        print(f"Warning: Icon file not found at: {icon_path}")
    # --------------------------

    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Pier to the Past Game") # Caption is set here

    try:
        print("Creating Game instance...")
        game = Game(screen)
        print("Starting game run...")
        game.run()

    except Exception as e:
        print(f"\n--- An unexpected error occurred during game execution ---")
        print(f"{type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        print("----------------------------------------------------------")

    finally:
        print("Quitting Pygame...")
        pygame.quit()
        print("Pygame quit successfully.")

if __name__ == "__main__":
    main()
