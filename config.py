# config.py

# Game Constants
SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 800
FPS: int = 60
ZOOM_LEVEL: float = 1.0  # Use float for zoom
DEFAULT_LAYER: int = 1
TILE_SIZE: int = 32

# File paths (Using relative paths is generally good practice)
ASSETS_DIR = './Assets'
IMAGES_DIR = f'{ASSETS_DIR}/Images'
MAPS_DIR = f'{ASSETS_DIR}/Maps'

PIERMASTER_IMAGE: str = f'{IMAGES_DIR}/piermaster.png'
PLAYER_IMAGE: str = f'{IMAGES_DIR}/gentleman.png'
MAYOR_IMAGE: str = f'{IMAGES_DIR}/mayor.png'
HOUSEOWNER_IMAGE: str = f'{IMAGES_DIR}/houseowner0.png'

HOUSEOWNER_DEFAULT_IMAGE: str = f'{IMAGES_DIR}/houseowner0.png' # A general one if needed
HOUSEOWNER_DEFAULT_IMAGE: str = f'{IMAGES_DIR}/houseowner0.png' # A general one if needed
HOUSEOWNER_ONE_IMAGE: str = f'{IMAGES_DIR}/houseowner1.png' # Replace with actual filename
HOUSEOWNER_TWO_IMAGE: str = f'{IMAGES_DIR}/houseowner2.png' # Replace with actual filename
HOUSEOWNER_THREE_IMAGE: str = f'{IMAGES_DIR}/houseowner3.png' # Replace with actual filename

MAP_PATHS: dict[str, str] = {
    'pier': f"{MAPS_DIR}/pier_map.tmx",
    'palace': f"{MAPS_DIR}/palace_map.tmx",
    'streets': f"{MAPS_DIR}/streets_map.tmx"
}

# Player Settings
PLAYER_SPEED: int = 5
PLAYER_HITBOX_INFLATE_X: int = -8
PLAYER_HITBOX_INFLATE_Y: int = -8
PLAYER_DIAGONAL_SPEED_FACTOR: float = 0.7071 # 1 / sqrt(2)

# Map Transition Settings
MAP_TRANSITION_BUFFER: int = 30 # Pixels from edge to trigger transition