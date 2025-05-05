# config.py
import sys
import os

# --- Determine the base path for resources ---
# PyInstaller creates a temp folder and stores path in _MEIPASS (one-file)
# Otherwise, get the directory of the executable (one-folder) or script
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running in a PyInstaller bundle (one-file)
    base_path = sys._MEIPASS
    print(f"Running frozen (one-file), base path: {base_path}")
elif getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle (one-folder)
    base_path = os.path.dirname(sys.executable)
    print(f"Running frozen (one-folder), base path: {base_path}")
else:
    # Running as a normal Python script
    base_path = os.path.dirname(os.path.abspath(__file__))
    print(f"Running as script, base path: {base_path}")

# Game Constants
SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 800
FPS: int = 60
ZOOM_LEVEL: float = 1.0  # Use float for zoom
DEFAULT_LAYER: int = 1
TILE_SIZE: int = 32


# Colours
WHITE = (255,255,255)
BLACK = (0,0,0)
DARK_GRAY = (96,89,88)
LIGHT_BLUE = (173, 216, 230) # For interaction prompt

# --- Define asset paths relative to the base path ---
ASSETS_DIR = os.path.join(base_path, 'Assets')
print(f"ASSETS_DIR resolved to: {ASSETS_DIR}")

IMAGES_DIR = os.path.join(ASSETS_DIR, 'Images')
MAPS_DIR = os.path.join(ASSETS_DIR, 'Maps')
MUSIC_DIR = os.path.join(ASSETS_DIR, 'Sounds')
FONTS_DIR = os.path.join(ASSETS_DIR, 'Fonts') # Define Fonts dir explicitly

# --- Specific File Paths using os.path.join ---
PIERMASTER_IMAGE: str = os.path.join(IMAGES_DIR, 'piermaster.png')
PLAYER_IMAGE: str = os.path.join(IMAGES_DIR, 'gentleman.png')
MAYOR_IMAGE: str = os.path.join(IMAGES_DIR, 'mayor.png')
HOUSEOWNER_IMAGE: str = os.path.join(IMAGES_DIR, 'houseowner0.png') # Default if needed by Houseowner class

HOUSEOWNER_DEFAULT_IMAGE: str = os.path.join(IMAGES_DIR, 'houseowner0.png')
HOUSEOWNER_ONE_IMAGE: str = os.path.join(IMAGES_DIR, 'houseowner1.png')
HOUSEOWNER_TWO_IMAGE: str = os.path.join(IMAGES_DIR, 'houseowner2.png')
HOUSEOWNER_THREE_IMAGE: str = os.path.join(IMAGES_DIR, 'houseowner3.png')

INTRO_BACKGROUND_IMAGE: str = os.path.join(IMAGES_DIR, 'intro_background.png')
# ENDING_BACKGROUND_IMAGE: str = os.path.join(IMAGES_DIR, 'story1.jpg') # Still unused

MAP_PATHS: dict[str, str] = {
    'pier': os.path.join(MAPS_DIR, "pier_map.tmx"),
    'palace': os.path.join(MAPS_DIR, "palace_map.tmx"),
    'streets': os.path.join(MAPS_DIR, "streets_map.tmx"),
    'pier_repaired': os.path.join(MAPS_DIR, "pier_map_repaired.tmx")
}


# Map Specific Music Settings
MAP_MUSIC_PATHS: dict[str, str | None] = {
    'pier': os.path.join(MUSIC_DIR, 'ReachingOut.mp3'),
    'palace': os.path.join(MUSIC_DIR, 'Autumn Day.mp3'),
    'streets': os.path.join(MUSIC_DIR, 'When The Wind Blows.mp3'),
    'pier_repaired': os.path.join(MUSIC_DIR, 'Bright Wish.mp3')
    # Add other maps here if they have music, or None if they don't
}
MAP_MUSIC_FADE_MS: int = 1000 # Fade duration for map music (in/out)


# Player Settings
PLAYER_SPEED: int = 5
PLAYER_HITBOX_INFLATE_X: int = -8
PLAYER_HITBOX_INFLATE_Y: int = -8
PLAYER_DIAGONAL_SPEED_FACTOR: float = 0.7071 # 1 / sqrt(2)

# Interaction Settings
INTERACTION_DISTANCE: int = 50 # Max distance in pixels to interact with NPCs

# Map Transition Settings
MAP_TRANSITION_BUFFER: int = 30 # Pixels from edge to trigger transition

# --- NPC Starting Positions per Map ---
# Defines the center (x, y) coordinates for NPCs on specific maps.
# Keys are map names (matching MAP_PATHS keys).
# Values are dictionaries where keys are NPC identifiers (e.g., 'piermaster', 'mayor', 'houseowner_0')
# and values are (x, y) tuples.
NPC_POSITIONS: dict[str, dict[str, tuple[int, int]]] = {
    'pier': {
        'piermaster': (500, 400), # Original position
    },
    'palace': {
        'mayor': (650, 450), # Original position
    },
    'streets': {
        # Use 'houseowner_INDEX' as the key
        'houseowner_0': (100, 105), # Original positions
        'houseowner_1': (350, 105),
        'houseowner_2': (650, 105),
        'houseowner_3': (920, 105),
    },
    'pier_repaired': {
        'piermaster': (350, 600), # New position for repaired pier
        'mayor': (450, 600),      # New position for repaired pier
        'houseowner_0': (650, 600), # Reposition existing houseowner 0
        'houseowner_1': (750, 600), # Reposition existing houseowner 1
        'houseowner_2': (850, 600), # Reposition existing houseowner 2
        'houseowner_3': (950, 600), # Reposition existing houseowner 3
    }
    # Add other maps here if NPCs appear on them
}
