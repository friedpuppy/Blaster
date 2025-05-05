# \\synology\sharedDrive\CALLUM\EDUCATION\2022-2025 Brighton University\3-YEAR THREE\CI601 The Computing Project\GAME DEVELOPMENT\Master\sharedDrive\CALLUM\EDUCATION\2022-2025 Brighton University\3-YEAR THREE\CI601 The Computing Project\GAME DEVELOPMENT\Master\main.py
# Author: Callum Donnelly
# Date: 2025-05-05 (or update to current date)
# Description: Main entry point for the game. Initializes Pygame,
#              manages the game loop, handles map loading and transitions,
#              and coordinates updates and drawing of game elements.
#              Includes cutscene handling with background music.
#
# References Local Files:
#   - config.py: Loads game settings, constants, and file paths (including MAP_MUSIC_PATHS).
#   - sprites.py: Uses Player and NPC sprite classes defined therein.
#   - dialogue.py: Uses Cutscene class and collision_cutscenes data.

import pygame
import pytmx # For loading Tiled map files (.tmx)
import pyscroll # For rendering Tiled maps efficiently
from pytmx.util_pygame import load_pygame # Pygame-specific Tiled loader utility
from typing import Optional, Dict, List # Used for type hinting
import os # Needed for checking music file existence
import traceback # For better error reporting


# Import necessary classes/data from dialogue.py
from dialogue import Dialogue, DialogueBox, dialogues, Cutscene, collision_cutscenes, render_textrect, TextRectException

# Import from our custom modules
import config  # Game configuration variables
import sprites # Game sprite classes (Player, NPCs, etc.)
from ui import Button # Import the Button class

# --- Global Variables ---
accumulator: int = 0 # Example global variable

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

        # --- Music State ---
        self.current_background_music_path: Optional[str] = None # Track currently playing BGM

        # --- Game State ---
        self.game_state: str = 'intro' # 'intro', 'playing', 'dialogue', 'cutscene', 'ending', 'confirm_quit'

        # --- Cutscene State Variables ---
        self.active_cutscene: Optional[Cutscene] = None
        self.current_cutscene_slide: int = 0
        self.cutscene_image_surface: Optional[pygame.Surface] = None
        self.cutscene_text_surface: Optional[pygame.Surface] = None
        self.cutscene_text_bg_rect: Optional[pygame.Rect] = None # Rect for the text background box
        self.cutscene_text_padding: int = 15 # Pixels of padding inside the text box
        # Removed the cutscene_triggers group
        self.show_player_coords: bool = False # Flag to control coordinate display
        self.triggered_cutscenes = set() # Keep track of which cutscenes have been played (per map load)
        self.cutscene_music_fadeout_time = 500 # Milliseconds for music fade-out

        # --- Dialogue State Variables ---
        self.active_dialogue: Optional[Dialogue] = None
        self.dialogue_box: Optional[DialogueBox] = None # Use a single box, update its text
        self.interact_prompt_surf: Optional[pygame.Surface] = None # Surface for "Press E"

        # --- Pier Repair State Variables Removed ---
        # --- Font Initialization ---
        try:
            # Font for general UI (like FPS counter)
            self.ui_font = pygame.font.Font(None, 30)
            self.title_font = pygame.font.Font(None, 60) # Font for the intro title
            # Font for the funds display (using your custom font)
            funds_font_name = 'White On Black.ttf'
            funds_font_size = 30 # Or adjust as needed
            funds_font_path = os.path.abspath(os.path.join(config.ASSETS_DIR, 'Fonts', funds_font_name))
            if os.path.exists(funds_font_path):
                print(f"Attempting to load funds font from path: {funds_font_path}")
                self.funds_font = pygame.font.Font(funds_font_path, funds_font_size)
                print(f"Successfully created funds font object: {self.funds_font}")
            else:
                print(f"Funds font file not found at: {funds_font_path}. Using default UI font for funds.")
                self.funds_font = self.ui_font # Fallback to the default UI font

            # Font specifically for cutscene text (can be different)
            self.cutscene_font = pygame.font.Font(None, 28) # Example size
            self.epilogue_font = pygame.font.Font(None, 36) # <-- New: Larger font for epilogue body
            self.epilogue_title_font = pygame.font.Font(None, 72) # <-- New: Larger font for epilogue title
            print("UI and Cutscene Fonts initialized.")

        except pygame.error as e:
            print(f"Error initializing funds font '{funds_font_name}': {e}. Using default UI font.")
            self.funds_font = pygame.font.Font(None, 30) # Ensure fallback on error
        except Exception as e: # Catch other potential font loading errors
            print(f"Error initializing fonts: {e}")
            self.ui_font = None
            self.cutscene_font = None
            self.epilogue_font = None # Ensure it's None on error
            self.epilogue_title_font = None # Ensure it's None on error
            self.title_font = None
            self.running = False # Stop if fonts fail

        # --- Player Initialization ---
        player_start_x = 700
        player_start_y = 200
        self.player = sprites.Player(player_start_x, player_start_y)

        # --- NPC Initialization ---
        # Initialize NPCs with placeholder positions (0, 0).
        # Their actual positions will be set in load_map based on config.NPC_POSITIONS.
        self.piermaster = sprites.Piermaster(0, 0)
        self.mayor = sprites.Mayor(0, 0)

        # Store houseowner image paths (positions are now handled by NPC_POSITIONS)
        # Use tuples: (image_path, dialogue_key)
        houseowner_data = [
            (config.HOUSEOWNER_DEFAULT_IMAGE, "houseowner0_generic"), # Use default key for the first one
            (config.HOUSEOWNER_ONE_IMAGE, "houseowner1_dialogue"), # Tuple: (image_path, dialogue_key)
            (config.HOUSEOWNER_TWO_IMAGE, "houseowner2_dialogue"),
            (config.HOUSEOWNER_THREE_IMAGE, "houseowner3_dialogue"),
            (config.HOUSEOWNER_THREE_IMAGE, "houseowner4_dialogue"), # Reuse image for 4th, different dialogue
        ]
        self.houseowners: List[sprites.Houseowner | None] = [] # Use a list
        # --- Corrected Houseowner Initialization Loop ---
        try:
            for item in houseowner_data:
                if isinstance(item, tuple):
                    img_path, dialogue_key = item
                else: # Assume it's just an image path string
                    img_path = item
                    dialogue_key = "houseowner_generic" # Fallback dialogue key if only path provided
                # Pass 0, 0 as initial coords, the image path, and the dialogue key
                self.houseowners.append(sprites.Houseowner(0, 0, img_path, dialogue_key))
            print(f"Initialized {len(self.houseowners)} Houseowner instances.")
        except Exception as e: # Catch other potential errors during init
             print(f"Unexpected error initializing Houseowners: {e}")
             self.houseowners = [] # Clear list on error


        # --- Dialogue Box Initialization (reusable) ---
        dialogue_box_x = (config.SCREEN_WIDTH / 2) - 300
        dialogue_box_y = config.SCREEN_HEIGHT - 250
        # Initialize with empty text, it will be updated when dialogue starts
        # Pass the already loaded ui_font instead of font name/size
        if self.ui_font:
            self.dialogue_box = DialogueBox(self, "", dialogue_box_x, dialogue_box_y, font=self.ui_font)
        else:
            print("CRITICAL: Cannot create DialogueBox because ui_font failed to load.")
            self.running = False # Stop if font is missing

        # --- Intro Screen Assets ---
        self.intro_background: Optional[pygame.Surface] = None
        self.title_surf: Optional[pygame.Surface] = None
        self.title_rect: Optional[pygame.Rect] = None
        self.play_button: Optional[Button] = None

        try:
            # Load intro background
            self.intro_background = pygame.image.load(config.INTRO_BACKGROUND_IMAGE).convert()
            # Scale if necessary to fit screen
            self.intro_background = pygame.transform.smoothscale(self.intro_background, self.screen.get_size())

            # Render title text
            if self.title_font:
                self.title_surf = self.title_font.render('A Pier to the Past', True, config.BLACK)
                self.title_rect = self.title_surf.get_rect(centerx=config.SCREEN_WIDTH / 2, y=100) # Position title

            # Create Play Button (ensure ui_font is loaded)
            if self.ui_font:
                button_width, button_height = 150, 60
                button_x = (config.SCREEN_WIDTH - button_width) / 2
                button_y = config.SCREEN_HEIGHT / 2 # Position button
                self.play_button = Button(button_x, button_y, button_width, button_height, config.WHITE, config.DARK_GRAY, 'Play', self.ui_font)
        except (pygame.error, FileNotFoundError) as e:
            print(f"Error loading intro assets: {e}")
            # Potentially set game state to error or quit
            self.running = False

        # --- Quit Confirmation Dialog Assets ---
        self.confirm_quit_box_surf: Optional[pygame.Surface] = None
        self.confirm_quit_text_surf: Optional[pygame.Surface] = None
        self.confirm_quit_text_rect: Optional[pygame.Rect] = None
        self.yes_button: Optional[Button] = None
        self.no_button: Optional[Button] = None
        self._prepare_quit_confirmation_assets() # Create surfaces and buttons

        # --- Fullscreen / Scaling Setup ---
        self.native_screen_width = screen.get_width()
        self.native_screen_height = screen.get_height()
        # Create the surface where the actual game rendering happens at the fixed resolution
        self.game_surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

        # Calculate integer scaling factor
        scale_w = self.native_screen_width // config.SCREEN_WIDTH
        scale_h = self.native_screen_height // config.SCREEN_HEIGHT
        self.scale_factor = max(1, min(scale_w, scale_h)) # Ensure scale is at least 1

        self.scaled_width = config.SCREEN_WIDTH * self.scale_factor
        self.scaled_height = config.SCREEN_HEIGHT * self.scale_factor

        # Calculate offset to center the scaled surface on the native screen
        self.blit_offset_x = (self.native_screen_width - self.scaled_width) // 2
        self.blit_offset_y = (self.native_screen_height - self.scaled_height) // 2
        # --- Ending Screen Assets ---
        self.ending_background: Optional[pygame.Surface] = None
        self.ending_title_surf: Optional[pygame.Surface] = None
        self.ending_title_rect: Optional[pygame.Rect] = None
        self.ending_text_surf: Optional[pygame.Surface] = None
        self.ending_text_rect: Optional[pygame.Rect] = None
        # --- Modified for two images ---
        self.ending_image1_surf: Optional[pygame.Surface] = None
        self.ending_image1_rect: Optional[pygame.Rect] = None
        self.ending_image2_surf: Optional[pygame.Surface] = None
        self.ending_image2_rect: Optional[pygame.Rect] = None

        try:
            # --- Ending Background Removed ---
            # We'll use a black screen and draw the specific ending image on top.
            # self.ending_background = pygame.image.load(config.ENDING_BACKGROUND_IMAGE).convert()
            # self.ending_background = pygame.transform.smoothscale(self.ending_background, self.screen.get_size())
            self.ending_background = None # Explicitly set to None

            # --- Load Ending Images (Side-by-Side) ---
            image_paths = [
                f"{config.IMAGES_DIR}/ending_background1.jpeg",
                f"{config.IMAGES_DIR}/ending_background2.jpg"
            ]
            image_surfaces = [None, None] # To store loaded/scaled surfaces
            image_rects = [None, None]   # To store final positions

            max_image_height = 0 # Keep track of the tallest image after scaling

            # Define the total width available and padding
            total_available_width = config.SCREEN_WIDTH * 0.8 # Use 80% of screen width for images
            padding_between = 20 # Pixels between images
            target_image_width = (total_available_width - padding_between) / 2

            for i, path in enumerate(image_paths):
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path).convert()
                        # Scale based on target width, maintaining aspect ratio
                        aspect_ratio = img.get_height() / img.get_width()
                        target_height = int(target_image_width * aspect_ratio)
                        image_surfaces[i] = pygame.transform.smoothscale(img, (int(target_image_width), target_height))
                        max_image_height = max(max_image_height, target_height) # Update max height
                    except pygame.error as e:
                        print(f"Error loading or scaling ending image {i+1} ('{path}'): {e}")
                else:
                    print(f"Warning: Ending image {i+1} not found at {path}")

            # Position the images side-by-side, centered horizontally, near the top
            start_x = (config.SCREEN_WIDTH - total_available_width) / 2
            image_y = 60 # Vertical position from the top
            if image_surfaces[0]:
                image_rects[0] = image_surfaces[0].get_rect(topleft=(start_x, image_y))
            if image_surfaces[1]:
                image_rects[1] = image_surfaces[1].get_rect(topleft=(start_x + target_image_width + padding_between, image_y))

            self.ending_image1_surf, self.ending_image2_surf = image_surfaces
            self.ending_image1_rect, self.ending_image2_rect = image_rects

            # Pre-render ending text AFTER loading image, so positions can be based on it
            self._prepare_ending_screen_text()
        except (pygame.error, FileNotFoundError) as e:
            print(f"Error loading ending assets: {e}")
            # Decide how to handle this - maybe a fallback screen?
        # --- Map Loading Deferred ---
        # Map will be loaded when transitioning from 'intro' to 'playing' state
        #self.load_map('streets') # Start on the streets map

    def _prepare_quit_confirmation_assets(self):
        """Creates the surfaces and buttons for the quit confirmation dialog."""
        if not self.ui_font:
            print("Error: Cannot prepare quit confirmation assets - UI font not loaded.")
            return

        box_width = 400
        box_height = 150
        box_x = (config.SCREEN_WIDTH - box_width) // 2 # Center on game_surface
        box_y = (config.SCREEN_HEIGHT - box_height) // 2

        # Create the background box surface (semi-transparent dark gray)
        self.confirm_quit_box_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        self.confirm_quit_box_surf.fill((*config.DARK_GRAY, 220)) # Use RGBA with alpha
        pygame.draw.rect(self.confirm_quit_box_surf, config.WHITE, self.confirm_quit_box_surf.get_rect(), 2) # White border
        self.confirm_quit_box_rect = self.confirm_quit_box_surf.get_rect(topleft=(box_x, box_y))

        # Render the confirmation text
        text = "Are you sure you want to quit?"
        self.confirm_quit_text_surf = self.ui_font.render(text, True, config.WHITE)
        self.confirm_quit_text_rect = self.confirm_quit_text_surf.get_rect(centerx=box_width // 2, y=20) # Position text inside the box

        # Create Yes/No buttons
        button_width, button_height = 100, 40
        button_y = box_height - button_height - 20 # Position buttons near bottom
        button_padding = 30 # Space between buttons

        yes_button_x = (box_width // 2) - button_width - (button_padding // 2)
        no_button_x = (box_width // 2) + (button_padding // 2)

        # Note: Button coordinates are relative to the confirm_quit_box_surf
        self.yes_button = Button(yes_button_x, button_y, button_width, button_height, config.WHITE, config.DARK_GRAY, 'Yes (Y)', self.ui_font)
        self.no_button = Button(no_button_x, button_y, button_width, button_height, config.WHITE, config.DARK_GRAY, 'No (N)', self.ui_font)


    def load_map(self, map_key: str) -> None:
        """Loads and configures a new map, including background music."""
        print(f"Loading map: {map_key}")
        try:
            if map_key not in config.MAP_PATHS:
                raise ValueError(f"Map key '{map_key}' not found in config.MAP_PATHS")

            map_path = config.MAP_PATHS[map_key]
            self.tmx_data = load_pygame(map_path)
            map_data = pyscroll.TiledMapData(self.tmx_data)

            self.map_layer = pyscroll.BufferedRenderer(
                map_data, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), clamp_camera=True, alpha=True # Use game_surface size
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

            # --- Recreate Renderer (No special pier logic needed here anymore) ---
            self.map_layer = pyscroll.BufferedRenderer(map_data, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), clamp_camera=True, alpha=True) # Use game_surface size
            self.map_layer.zoom = config.ZOOM_LEVEL

            # --- Add Player ---
            self.group.add(self.player)

            # --- Add NPCs Based on Map using config.NPC_POSITIONS ---
            npc_positions_for_map = config.NPC_POSITIONS.get(map_key, {}) # Get positions for current map, default to empty dict
            print(f"NPC positions for map '{map_key}': {npc_positions_for_map}")

            # Add Piermaster if defined for this map
            if 'piermaster' in npc_positions_for_map and hasattr(self, 'piermaster') and self.piermaster:
                pos = npc_positions_for_map['piermaster']
                self.piermaster.rect.center = pos
                self.group.add(self.piermaster)
                # SPECIAL CASE: Assign ending dialogue only on repaired pier
                if map_key == 'pier_repaired':
                    self.piermaster.dialogue_key = "piermaster_ending"
                    print("  Piermaster assigned ENDING dialogue.")
                print(f"  Added Piermaster at {pos}")

            # Add Mayor if defined for this map
            if 'mayor' in npc_positions_for_map and hasattr(self, 'mayor') and self.mayor:
                pos = npc_positions_for_map['mayor']
                self.mayor.rect.center = pos
                self.group.add(self.mayor)
                print(f"  Added Mayor at {pos}")

            # Add Houseowners if defined for this map
            for i in range(len(self.houseowners)):
                houseowner_key = f'houseowner_{i}'
                if houseowner_key in npc_positions_for_map and self.houseowners[i]:
                    # Assign specific dialogue key based on index (matches houseowner_data in __init__)
                    dialogue_key = f"houseowner{i}_dialogue" # Assumes keys like 'houseowner0_dialogue', etc. exist
                    pos = npc_positions_for_map[houseowner_key]
                    self.houseowners[i].rect.center = pos # Set position
                    self.group.add(self.houseowners[i])
                    print(f"  Added Houseowner {i} at {pos}")

            # Update the group's map layer reference
            self.group.map_layer = self.map_layer

            self.current_map_key = map_key
            print(f"Map '{map_key}' loaded successfully.")

            # --- Start Map Specific Background Music ---
            # Check if MAP_MUSIC_PATHS exists in config, otherwise default to empty dict
            map_music_config = getattr(config, 'MAP_MUSIC_PATHS', {})
            target_music_path = map_music_config.get(map_key) # Get path from config, defaults to None

            if target_music_path:
                # Check if the target music isn't already playing
                if self.current_background_music_path != target_music_path:
                    if os.path.exists(target_music_path):
                        try:
                            pygame.mixer.music.load(target_music_path)
                            pygame.mixer.music.play(loops=-1, fade_ms=config.MAP_MUSIC_FADE_MS)
                            self.current_background_music_path = target_music_path
                            print(f"Playing map music: {target_music_path}")
                        except pygame.error as e:
                            print(f"Error loading/playing map music '{target_music_path}': {e}")
                            self.current_background_music_path = None # Ensure state is correct on error
                    else:
                        print(f"Warning: Map music file not found: {target_music_path}")
                        self.current_background_music_path = None # Ensure state is correct
            else:
                # If map has no music defined (target_music_path is None), fade out whatever was playing
                if self.current_background_music_path is not None:
                    print(f"Fading out previous music for map '{map_key}' (no new music defined).")
                    pygame.mixer.music.fadeout(config.MAP_MUSIC_FADE_MS)
                    self.current_background_music_path = None

        except (KeyError, FileNotFoundError, ValueError, pygame.error, Exception) as e:
            print(f"Error loading map '{map_key}': {type(e).__name__} - {e}")
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
                # --- Access and modify the GLOBAL accumulator ---
                global accumulator # Declare intent to modify the global variable
                accumulator = accumulator + 100
                print(f"Global Accumulator is now: {accumulator}")
                # -------------------------------------------------

                # Check if the cutscene exists and hasn't been played on this map load
                if current_trigger_key in collision_cutscenes and current_trigger_key not in self.triggered_cutscenes:
                    self.start_cutscene(current_trigger_key) # Start the cutscene
                # ... rest of the logic ...

                elif current_trigger_key in self.triggered_cutscenes:
                     print(f"  Cutscene '{current_trigger_key}' already triggered on this map load.")
                elif current_trigger_key not in collision_cutscenes:
                     print(f"  Warning: Tile has CutsceneTrigger '{current_trigger_key}', but no matching cutscene found in dialogue.py.")

            # --- Update the last known properties for the next frame ---
            self.last_event_tile_properties = current_tile_properties

    def find_nearby_interactable_npc(self) -> Optional[pygame.sprite.Sprite]:
        """Finds the closest NPC within interaction range that has a dialogue key."""
        if not self.player or not self.group:
            return None

        player_pos = pygame.Vector2(self.player.hitbox.center)
        closest_npc = None
        min_dist_sq = config.INTERACTION_DISTANCE ** 2 # Use squared distance for efficiency

        # Iterate through sprites in the group that are NPCs and have dialogue
        for sprite in self.group.sprites():
            # Check if it's an NPC instance we care about and has a dialogue key
            if isinstance(sprite, (sprites.Piermaster, sprites.Mayor, sprites.Houseowner)) and hasattr(sprite, 'dialogue_key'):
                npc_pos = pygame.Vector2(sprite.rect.center)
                dist_sq = player_pos.distance_squared_to(npc_pos)

                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    closest_npc = sprite

        return closest_npc

    def start_dialogue(self, npc: pygame.sprite.Sprite) -> None:
        """Starts a dialogue sequence with the given NPC."""
        if self.game_state != 'playing' or not hasattr(npc, 'dialogue_key'):
            return # Can only start dialogue from playing state with a valid NPC

        dialogue_key = npc.dialogue_key
        if dialogue_key in dialogues:
            self.active_dialogue = dialogues[dialogue_key]
            self.active_dialogue.reset() # Start from the first line
            first_line = self.active_dialogue.get_current_line()
            if first_line and self.dialogue_box:
                self.dialogue_box.update_text(f"{self.active_dialogue.name}: {first_line}")
                self.dialogue_box.show()
                self.game_state = 'dialogue' # Change game state
                print(f"Starting dialogue: {dialogue_key}")
            else:
                print(f"Warning: Dialogue '{dialogue_key}' has no lines.")
                self.active_dialogue = None # Ensure no active dialogue if empty
        else:
            print(f"Warning: Dialogue key '{dialogue_key}' not found for NPC.")

    def advance_dialogue(self) -> None:
        """Advances to the next line or ends the dialogue."""
        if self.game_state != 'dialogue' or not self.active_dialogue or not self.dialogue_box:
            return

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
        elif self.current_map_key == 'pier_repaired' and player_rect.left <= 0 + buffer: # Transition FROM repaired pier
            new_map_key = 'palace'
            new_player_pos = ('right', config.SCREEN_WIDTH - buffer)
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

    # --- check_pier_repair_status method is removed ---

    # --- Cutscene Methods ---

    def start_cutscene(self, cutscene_key: str) -> None:
        """Initiates a cutscene based on the provided key, including music."""
        if self.game_state == 'cutscene':
            print("Warning: Tried to start a cutscene while one is already active.")
            return # Don't start a new one if already in a cutscene

        if cutscene_key in collision_cutscenes:
            print(f"Starting cutscene: {cutscene_key}")
            self.active_cutscene = collision_cutscenes[cutscene_key]
            self.current_cutscene_slide = 0
            self.game_state = 'cutscene'
            self.triggered_cutscenes.add(cutscene_key) # Mark as played for this map load

            # --- Music Handling ---
            # Fade out any currently playing music (e.g., map music)
            pygame.mixer.music.fadeout(self.cutscene_music_fadeout_time)
            self.current_background_music_path = None # Clear tracker as map music stopped

            # Load and play the cutscene-specific music if available
            if self.active_cutscene.music_path:
                music_path = self.active_cutscene.music_path
                if os.path.exists(music_path):
                    try:
                        pygame.mixer.music.load(music_path)
                        # Play looping, start immediately (no fade-in here, but possible)
                        pygame.mixer.music.play(loops=-1)
                        print(f"Playing cutscene music: {music_path}")
                    except pygame.error as e:
                        print(f"Error loading or playing cutscene music '{music_path}': {e}")
                else:
                    print(f"Warning: Cutscene music file not found: '{music_path}'")
            else:
                print("Cutscene has no associated music.")
            # --------------------

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
            self.cutscene_text_bg_rect = None # Reset background rect
            if text:
                text_margin = 50
                text_box_height = 150
                # 1. Define the visual background box rectangle
                self.cutscene_text_bg_rect = pygame.Rect(
                    text_margin, # Position relative to game_surface
                    config.SCREEN_HEIGHT - text_box_height - text_margin,
                    config.SCREEN_WIDTH - (text_margin * 2),
                    text_box_height # Use config dimensions
                )

                # 2. Define the area *inside* the box for text rendering
                text_render_area_width = self.cutscene_text_bg_rect.width - (self.cutscene_text_padding * 2)
                text_render_area_height = self.cutscene_text_bg_rect.height - (self.cutscene_text_padding * 2)
                text_render_rect = pygame.Rect(0, 0, text_render_area_width, text_render_area_height)

                try:
                    # 3. Render *only* the text with a transparent background
                    self.cutscene_text_surface = render_textrect(
                        text,
                        self.cutscene_font, # Font object
                        text_render_rect,   # The rectangle for the text area
                        config.WHITE,
                        (0, 0, 0, 0), # Transparent background for the text surface
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
        """Cleans up after a cutscene finishes, fades out music, and returns to gameplay."""
        print("Ending cutscene.")

        # --- Music Handling ---
        # Fade out the cutscene music
        pygame.mixer.music.fadeout(self.cutscene_music_fadeout_time) # Fade out cutscene track
        # Optional: Add a small delay to allow fadeout before potentially starting map music
        # pygame.time.wait(self.cutscene_music_fadeout_time)

        # --- Resume Map Specific Music if Applicable ---
        # Check if MAP_MUSIC_PATHS exists in config, otherwise default to empty dict
        map_music_config = getattr(config, 'MAP_MUSIC_PATHS', {})
        target_music_path = map_music_config.get(self.current_map_key) # Get path for current map

        if target_music_path:
            if os.path.exists(target_music_path):
                try:
                    pygame.mixer.music.load(target_music_path)
                    pygame.mixer.music.play(loops=-1, fade_ms=config.MAP_MUSIC_FADE_MS) # Fade in map music
                    self.current_background_music_path = target_music_path
                    print(f"Resuming map music: {target_music_path}")
                except pygame.error as e:
                    print(f"Error resuming map music '{target_music_path}': {e}")
                    self.current_background_music_path = None # Ensure state is correct on error
            else:
                 print(f"Warning: Map music file not found, cannot resume: {target_music_path}")
                 self.current_background_music_path = None # Ensure state is correct
        else:
            # If the map has no music defined, ensure the tracker is cleared
            self.current_background_music_path = None
        # --------------------

        self.game_state = 'playing'
        self.active_cutscene = None
        self.current_cutscene_slide = 0
        self.cutscene_image_surface = None
        self.cutscene_text_surface = None
        self.cutscene_text_bg_rect = None # Clear the background rect too
        # Optional: Add a small delay before player can move again?
        # pygame.time.wait(200) # e.g., 200ms pause

    def _prepare_ending_screen_text(self):
        """Renders the text surfaces for the ending screen."""
        if self.epilogue_title_font and self.epilogue_font: # Check for the new epilogue fonts
            try:
                # Ending Title
                # Calculate Y position based on the bottom of the images area
                images_bottom_y = 60 # Default Y if no images loaded
                if self.ending_image1_rect or self.ending_image2_rect: # These rects are already relative to game_surface
                     images_bottom_y = max(r.bottom for r in [self.ending_image1_rect, self.ending_image2_rect] if r is not None)
                title_y_pos = images_bottom_y + 50 # Position title below the images area (adjust spacing as needed)
                self.ending_title_surf = self.title_font.render("A Pier to the Past", True, config.WHITE)
                self.ending_title_rect = self.ending_title_surf.get_rect(centerx=config.SCREEN_WIDTH / 2, y=title_y_pos)

                # Ending Body Text (using render_textrect for wrapping)
                ending_message = ("The Pier was quickly repaired, and would last another six decades of use. "
                                  "Despite suffering more damage over time, it was always repaired. "
                                  "The West Pier opened in 1866, specifically designed for amusements. "
                                  "Combined with the opening of the Aquarium, crowds began to lose interest in the dated Chain Pier. "
                                  "The Chain Pier finally collapsed in 1896, derelict and dangerously out of askew. "
                                  "But for a brief moment in time, Brighton was the only town in England to have three piers at once.\n\n"
                                  "THE END.")
                text_box_width = config.SCREEN_WIDTH - 200 # Make text box wider
                text_box_height = 350 # Increase height slightly to accommodate larger font
                text_render_rect = pygame.Rect(0, 0, text_box_width, text_box_height) # Rect for text rendering area
                self.ending_text_surf = render_textrect(ending_message, self.epilogue_font, text_render_rect, config.WHITE, (0,0,0,0), justification=1) # Centered text, use epilogue_font
                text_y_pos = self.ending_title_rect.bottom + 20 # Position text below the title
                self.ending_text_rect = self.ending_text_surf.get_rect(centerx=config.SCREEN_WIDTH / 2, top=text_y_pos) # Center on game_surface
            except Exception as e:
                print(f"Error preparing ending screen text: {e}")
    # --- Main Game Loop Methods ---

    def run(self) -> None:
        """Contains the main game loop."""
        print("Starting game loop...")
        while self.running:
            # Calculate delta time for frame-rate independent movement/updates
            dt = self.clock.tick(config.FPS) / 1000.0

            # --- Game Loop Stages ---
            self.handle_events()
            self.update(dt)
            self.draw()

        print("Exiting game loop.")

    def _map_mouse_coords(self, screen_pos: tuple[int, int]) -> tuple[int, int] | None:
        """Maps mouse coordinates from the fullscreen display to the game_surface."""
        screen_x, screen_y = screen_pos
        # Translate coordinates relative to the top-left of the scaled game area
        relative_x = screen_x - self.blit_offset_x
        relative_y = screen_y - self.blit_offset_y

        # Check if the click is within the scaled game area bounds
        if 0 <= relative_x < self.scaled_width and 0 <= relative_y < self.scaled_height:
            # Scale back down to game_surface coordinates
            game_x = relative_x // self.scale_factor
            game_y = relative_y // self.scale_factor
            return game_x, game_y
        print("Exiting game loop.")

    def handle_events(self) -> None:
        """Processes all events from Pygame's event queue."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if self.game_state == 'playing':
                # Handle gameplay input (movement is handled in Player.update)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: # Quit confirmation
                        print("ESC pressed - Entering quit confirmation.")
                        self.game_state = 'confirm_quit'
                    if event.key == pygame.K_e: # Interaction key
                        nearby_npc = self.find_nearby_interactable_npc()
                        if nearby_npc:
                            print(f"E key pressed - Interacting with {type(nearby_npc).__name__}")
                            self.start_dialogue(nearby_npc)
                        else:
                            print("E key pressed - No interactable NPC nearby.")
                    elif event.key == pygame.K_q: # DEBUG: Set accumulator to 300
                        global accumulator
                        accumulator = 300
                        print(f"DEBUG: 'Q' pressed. Accumulator set to {accumulator}.")
                    elif event.key == pygame.K_c: # Toggle coordinate display
                        self.show_player_coords = not self.show_player_coords
                        print(f"Coordinate display toggled: {'ON' if self.show_player_coords else 'OFF'}")
                        # No immediate check needed, update loop will handle the transition
                    # Add other gameplay keybinds here (e.g., interaction key)

            elif self.game_state == 'dialogue':
                 if event.type == pygame.KEYDOWN:
                     if event.key == pygame.K_RETURN or event.key == pygame.K_e: # Use Enter or E to advance
                         print("Advancing dialogue...")
                         next_line = self.active_dialogue.next_line()
                         if next_line:
                             self.dialogue_box.update_text(f"{self.active_dialogue.name}: {next_line}")
                         else:
                             # Dialogue finished
                             print("Dialogue finished.")
                             self.dialogue_box.hide()
                             # Check if it was the Piermaster's ENDING dialogue
                             if self.active_dialogue == dialogues.get("piermaster_ending"):
                                 self.game_state = 'ending' # <<< TRANSITION TO ENDING
                             else:
                                 self.game_state = 'playing' # Return to gameplay
                             self.active_dialogue = None

            elif self.game_state == 'cutscene':
                # Handle cutscene input (only Enter key)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN: # ENTER key
                        print("Enter pressed - Advancing cutscene.")
                        self._advance_cutscene_slide()
                    elif event.key == pygame.K_ESCAPE: # Optional: Allow skipping cutscene
                        print("Escape pressed - Ending cutscene early.")
                        self._end_cutscene()

            elif self.game_state == 'intro':
                # Handle intro screen input
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: # Allow quitting from intro
                        self.running = False
                # Check button press
                screen_mouse_pos = pygame.mouse.get_pos()
                mouse_pressed = pygame.mouse.get_pressed()
                game_mouse_pos = self._map_mouse_coords(screen_mouse_pos)

                if game_mouse_pos and self.play_button:
                    if self.play_button.is_pressed(game_mouse_pos, mouse_pressed):
                        print("Play button pressed - Starting game.")
                        self.game_state = 'playing'
                        self.load_map('pier') # Load the initial map NOW

            elif self.game_state == 'confirm_quit':
                 if event.type == pygame.KEYDOWN:
                     if event.key == pygame.K_ESCAPE or event.key == pygame.K_n: # Cancel quit
                         print("Quit cancelled.")
                         self.game_state = 'playing'
                     elif event.key == pygame.K_y: # Confirm quit
                         print("Quit confirmed.")
                         self.running = False
                 elif event.type == pygame.MOUSEBUTTONDOWN:
                     if event.button == 1: # Left mouse button
                         screen_mouse_pos = pygame.mouse.get_pos()
                         game_mouse_pos = self._map_mouse_coords(screen_mouse_pos)

                         if game_mouse_pos and self.yes_button and self.no_button:
                             # Adjust mouse pos relative to the confirmation box for button checks
                             box_relative_mouse_pos = (game_mouse_pos[0] - self.confirm_quit_box_rect.x,
                                                       game_mouse_pos[1] - self.confirm_quit_box_rect.y)

                             # Check buttons (using box_relative_mouse_pos)
                             if self.yes_button.is_pressed(box_relative_mouse_pos, (True, False, False)):
                                 print("Quit confirmed via 'Yes' button.")
                                 self.running = False
                             elif self.no_button.is_pressed(box_relative_mouse_pos, (True, False, False)):
                                 print("Quit cancelled via 'No' button.")
                                 self.game_state = 'playing'

            elif self.game_state == 'ending':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: # Exit game from ending screen
                        self.running = False

    def update(self, dt: float) -> None:
        """Updates the game state based on the current game_state."""
        if self.game_state == 'playing':
            if self.group:
                # Update sprites (includes player movement, passing dt)
                self.group.update(dt) # Pass delta time to sprites that might need it
                # Center camera on player
                self.group.center(self.player.rect.center)
                # Check for tile-based events (including cutscene triggers)
                self.check_tile_events() # <--- This now handles cutscene triggers
                # Check for map transitions
                self.handle_map_transitions()

                # --- Check for Pier Repair Map Transition ---
                global accumulator
                if self.current_map_key == 'pier' and accumulator >= 300:
                    player_pos = self.player.rect.topleft # Store current position
                    print(f"Accumulator reached {accumulator} on pier map. Transitioning to repaired pier.")
                    self.load_map('pier_repaired')
                    # Restore player position after map load
                    if self.player: # Check if player exists after load
                        self.player.rect.topleft = player_pos
                        self.player.hitbox.center = self.player.rect.center
                        print(f"  Player position maintained at {player_pos} on repaired pier.")
                        if self.group: # Center camera on the restored position
                            self.group.center(self.player.rect.center)

                # --- Collision check for triggers is removed ---

        elif self.game_state == 'dialogue':
            # Potentially add blinking cursor or other dialogue effects here
            pass

        elif self.game_state == 'ending':
            # No game world updates needed for static ending screen
            pass

        elif self.game_state == 'cutscene':
            # No game world updates happen during a cutscene
            pass

        elif self.game_state == 'intro':
            # No game world updates needed for static intro screen
            pass

    def draw(self) -> None:
        """Renders the current game scene based on the game_state."""
        # --- Step 1: Draw everything onto the game_surface ---
        self.game_surface.fill(config.BLACK) # Start with a clear surface each frame

        if self.game_state == 'playing':
            # --- Draw Gameplay Scene ---
            if self.group and self.map_layer:
                self.group.draw(self.game_surface) # Draw to game_surface

                # --- Draw UI Elements ---
                # Example FPS counter (uncomment if needed)
                if self.ui_font:
                    ui_y_offset = 10 # Starting Y position for top-left UI elements
                    ui_x_pos = 10    # Starting X position
                    outline_offset = 2 # How many pixels to offset the black background/outline

                    # --- Draw Funds Counter (if applicable) ---
                    # Only draw funds on specific maps
                    if self.current_map_key in ['palace', 'streets']:
                        if hasattr(self, 'funds_font') and self.funds_font: # Check if funds_font loaded
                            # Define the text and position
                            acc_text = f"Pier Restoration funds: £{accumulator}" # Changed label, still accesses global accumulator

                            # 1. Render and blit the black background/outline text slightly offset
                            acc_surf_black = self.funds_font.render(acc_text, True, config.BLACK)
                            self.game_surface.blit(acc_surf_black, (ui_x_pos + outline_offset, ui_y_offset + outline_offset))
                            # 2. Render and blit the main white text on top
                            acc_surf_white = self.funds_font.render(acc_text, True, config.WHITE) # Use funds_font
                            self.game_surface.blit(acc_surf_white, (ui_x_pos, ui_y_offset))

                            # Update the Y offset for the next UI element
                            ui_y_offset += acc_surf_white.get_height() + 5 # Add 5 pixels padding

                    # --- Draw Player Coordinates (if toggled) ---
                    if self.show_player_coords and self.player:
                        px, py = self.player.rect.topleft # Get player's top-left coords
                        coords_text = f"X: {px}, Y: {py}"

                        # Use the same font and outline technique as the funds counter for consistency
                        # Render using ui_font (or funds_font if you prefer)
                        coords_surf_black = self.ui_font.render(coords_text, True, config.BLACK)
                        self.game_surface.blit(coords_surf_black, (ui_x_pos + outline_offset, ui_y_offset + outline_offset))

                        coords_surf_white = self.ui_font.render(coords_text, True, config.WHITE)
                        self.game_surface.blit(coords_surf_white, (ui_x_pos, ui_y_offset))

                        # Optional: Update ui_y_offset again if more UI elements are added below
                        # ui_y_offset += coords_surf_white.get_height() + 5

                # --- Draw Interaction Prompt ---
                nearby_npc = self.find_nearby_interactable_npc()
                if nearby_npc and self.ui_font:
                    if not self.interact_prompt_surf: # Render only once if needed
                        self.interact_prompt_surf = self.ui_font.render("Press E to talk", True, config.BLACK, config.LIGHT_BLUE)
                    prompt_rect = self.interact_prompt_surf.get_rect(midbottom=nearby_npc.rect.midtop - pygame.Vector2(0, 5)) # Position above NPC
                    self.game_surface.blit(self.interact_prompt_surf, prompt_rect)
                else:
                    self.interact_prompt_surf = None # Clear surface if no NPC nearby

                # Draw dialogue box if active (now handled by dialogue state)
                # if hasattr(self, 'test_dialogue_box'):
                #     self.test_dialogue_box.draw(self.screen)

                # --- DEBUG: Draw Player Hitbox (uncomment if needed) ---
                # pygame.draw.rect(self.screen, (255, 0, 0), self.player.hitbox, 1)


        elif self.game_state == 'cutscene':
            # --- Draw Cutscene Scene ---

            # 1. Draw the fullscreen background image first
            if self.cutscene_image_surface:
                # Scale image to game_surface size (it was previously scaled to screen size)
                scaled_cutscene_img = pygame.transform.smoothscale(self.cutscene_image_surface, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
                self.game_surface.blit(scaled_cutscene_img, (0, 0))
            else:
                # Fallback if image surface somehow wasn't created
                self.game_surface.fill(config.BLACK)

            # 2. Draw the dark gray background box if its rect exists
            if self.cutscene_text_bg_rect:
                # Draw the box onto game_surface (rect coords are already relative to it)
                pygame.draw.rect(self.game_surface, (*config.DARK_GRAY, 200), self.cutscene_text_bg_rect, border_radius=5) # Semi-transparent

                # 3. Draw the text surface (text only) on top of the background, offset by padding
                if self.cutscene_text_surface:
                    text_blit_pos = (self.cutscene_text_bg_rect.x + self.cutscene_text_padding, self.cutscene_text_bg_rect.y + self.cutscene_text_padding)
                    self.game_surface.blit(self.cutscene_text_surface, text_blit_pos)

            # 3. Draw "Press Enter" prompt on top
            if self.ui_font:
                 prompt_text = "Press ENTER to continue..."
                 prompt_surf = self.ui_font.render(prompt_text, True, config.WHITE)
                 # Position prompt at the bottom-center
                 prompt_rect = prompt_surf.get_rect(centerx=config.SCREEN_WIDTH // 2, bottom=config.SCREEN_HEIGHT - 20)
                 # Optional: Add a slight shadow/background for better visibility on complex images
                 # shadow_surf = self.ui_font.render(prompt_text, True, config.BLACK)
                 # self.game_surface.blit(shadow_surf, prompt_rect.move(1,1)) # Offset shadow slightly
                 self.game_surface.blit(prompt_surf, prompt_rect)

        elif self.game_state == 'dialogue':
            # Draw the normal game world *underneath* the dialogue box
            if self.group and self.map_layer:
                self.group.draw(self.game_surface) # Draw map and sprites to game_surface
            if self.dialogue_box:
                self.dialogue_box.draw(self.game_surface) # Draw dialogue box on top

        elif self.game_state == 'intro':
            # --- Draw Intro Screen ---
            # Draw background
            if self.intro_background:
                # Scale background to fit game_surface
                scaled_intro_bg = pygame.transform.smoothscale(self.intro_background, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
                self.game_surface.blit(scaled_intro_bg, (0, 0))
            else:
                self.game_surface.fill(config.WHITE) # Fallback background
            # Draw title
            if self.title_surf and self.title_rect:
                self.game_surface.blit(self.title_surf, self.title_rect)
            # Draw button
            if self.play_button:
                self.play_button.draw(self.game_surface)

        elif self.game_state == 'confirm_quit':
            # 1. Draw the underlying 'playing' state first
            if self.group and self.map_layer:
                self.group.draw(self.game_surface)
            # 2. Draw the confirmation box and its contents on top
            if self.confirm_quit_box_surf and self.confirm_quit_box_rect:
                self.game_surface.blit(self.confirm_quit_box_surf, self.confirm_quit_box_rect)
                # Draw text and buttons relative to the box's surface/rect
                self.game_surface.blit(self.confirm_quit_text_surf, self.confirm_quit_text_rect.move(self.confirm_quit_box_rect.topleft))
                self.yes_button.draw(self.game_surface, offset=self.confirm_quit_box_rect.topleft) # Pass offset
                self.no_button.draw(self.game_surface, offset=self.confirm_quit_box_rect.topleft) # Pass offset

        elif self.game_state == 'ending':
            # --- Draw Ending Screen ---
            # Always draw black background first
            self.screen.fill(config.BLACK)
            # --- Draw Ending Images ---
            if self.ending_image1_surf and self.ending_image1_rect:
                self.game_surface.blit(self.ending_image1_surf, self.ending_image1_rect)
            if self.ending_image2_surf and self.ending_image2_rect:
                self.game_surface.blit(self.ending_image2_surf, self.ending_image2_rect)
            if self.ending_title_surf and self.ending_title_rect:
                self.game_surface.blit(self.ending_title_surf, self.ending_title_rect)
            if self.ending_text_surf and self.ending_text_rect:
                self.game_surface.blit(self.ending_text_surf, self.ending_text_rect)
            # Add "Press ESC" prompt if not included in main text


        # --- Step 2: Scale the game_surface to the display screen ---
        # Use transform.scale for nearest-neighbor (integer) scaling
        scaled_surface = pygame.transform.scale(self.game_surface, (self.scaled_width, self.scaled_height))
        self.screen.fill(config.BLACK) # Fill native screen with black (for letter/pillarboxing)
        self.screen.blit(scaled_surface, (self.blit_offset_x, self.blit_offset_y)) # Blit centered

        pygame.display.flip()


def main() -> None:
    """Main function to initialize and run the game."""
    print("Initializing Pygame...")
    pygame.init()
    print("Pygame initialized successfully.")

    # --- Initialize the Mixer ---
    try:
        pygame.mixer.init()
        print("Pygame mixer initialized successfully.")
        # Optional: Set default music volume
        # pygame.mixer.music.set_volume(0.7) # 0.0 to 1.0
    except pygame.error as e:
        print(f"Warning: Could not initialize Pygame mixer: {e}")
        # Game can potentially continue without sound
    # ---------------------------

    # --- Set the Window Icon ---
    try:
        # Construct the full path to the icon using config
        icon_path = f"{config.IMAGES_DIR}/game_icon.png" # Or your actual icon filename
        if os.path.exists(icon_path):
            icon_surface = pygame.image.load(icon_path)
            pygame.display.set_icon(icon_surface)
            print(f"Window icon set from: {icon_path}")
        else:
            print(f"Warning: Icon file not found at: {icon_path}")
    except pygame.error as e:
        print(f"Warning: Could not load or set window icon: {e}")
    # --------------------------

    # --- Initialize in Fullscreen ---
    # Combine FULLSCREEN with DOUBLEBUF and HWSURFACE to potentially reduce tearing
    display_flags = pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE
    # screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN) # Original fullscreen call
    screen = pygame.display.set_mode((0, 0), display_flags, vsync=1)
    print(f"Display initialized in fullscreen mode: {screen.get_width()}x{screen.get_height()}")
    pygame.display.set_caption("Pier to the Past Game") # Caption is set here

    try:
        print("Creating Game instance...")
        game = Game(screen)
        print("Starting game run...")
        game.run()

    except Exception as e:
        print(f"\n--- An unexpected error occurred during game execution ---")
        print(f"{type(e).__name__}: {e}")
        traceback.print_exc()
        print("----------------------------------------------------------")

    finally:
        print("Quitting Pygame...")
        pygame.quit()
        print("Pygame quit successfully.")

if __name__ == "__main__":
    main()
