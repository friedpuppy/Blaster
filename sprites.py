# sprites.py
# Author: Callum Donnelly
# Date: 2025-05-05
# Description: Contains sprite classes for the game, including the Player and NPCs.

import pygame
import config  # Import the configuration for constants like image paths and speeds

class Player(pygame.sprite.Sprite):
    """
    Represents the player character.
    Handles loading the player image, setting up the initial position and hitbox,
    and processing movement based on keyboard input.
    """

    def __init__(self, x: int, y: int) -> None:
        """
        Initializes the Player sprite.

        Args:
            x (int): The initial x-coordinate for the player's top-left corner.
            y (int): The initial y-coordinate for the player's top-left corner.
        """
        super().__init__()  # Initialize the parent Sprite class

        # Load the player image from the path specified in the config file
        try:
            # .convert_alpha() helps optimize rendering with transparency
            self.image = pygame.image.load(config.PLAYER_IMAGE).convert_alpha()
        except pygame.error as e:
            # Handle potential errors during image loading (e.g., file not found)
            print(f"Error loading player image: {config.PLAYER_IMAGE} - {e}")
            # Provide a fallback visual representation if the image fails to load
            self.image = pygame.Surface((config.TILE_SIZE, config.TILE_SIZE))
            self.image.fill((255, 0, 0)) # Red square as a visual indicator of the error
            # Optionally, re-raise the exception if the image is critical for the game
            # raise

        # Get the rectangular area of the image and set its top-left corner
        self.rect = self.image.get_rect(topleft=(x, y))

        # Create a hitbox for collision detection, slightly smaller than the visual rect
        # Uses inflation values from the config file
        self.hitbox = self.rect.inflate(config.PLAYER_HITBOX_INFLATE_X,
                                         config.PLAYER_HITBOX_INFLATE_Y)

        # Set the player's movement speed from the config file
        self.speed = config.PLAYER_SPEED

    def update(self, *args, **kwargs) -> None:
        """
        Updates the player's state each frame.
        Currently handles movement based on arrow key presses.
        Normalizes diagonal movement speed to prevent faster diagonal movement.
        """
        # Get the state of all keyboard keys
        keys = pygame.key.get_pressed()
        # Initialize movement vectors (delta x, delta y) as floats for precision
        dx, dy = 0.0, 0.0

        # --- Calculate movement direction based on pressed keys ---
        if keys[pygame.K_RIGHT]:
            dx += 1 # Move right
        if keys[pygame.K_LEFT]:
            dx -= 1 # Move left
        if keys[pygame.K_DOWN]:
            dy += 1 # Move down
        if keys[pygame.K_UP]:
            dy -= 1 # Move up

        # --- Normalize diagonal movement ---
        # If moving both horizontally and vertically, reduce speed along each axis
        if dx != 0 and dy != 0:
            # Multiply by the diagonal factor (1/sqrt(2)) from config
            dx *= config.PLAYER_DIAGONAL_SPEED_FACTOR
            dy *= config.PLAYER_DIAGONAL_SPEED_FACTOR

        # --- Apply speed and update position ---
        # Calculate the final movement amount for this frame
        move_x = round(dx * self.speed)
        move_y = round(dy * self.speed)

        # Move the player's main rectangle (visual representation) in place
        # round() converts the potentially fractional movement back to integer pixels
        self.rect.move_ip(move_x, move_y)

        # Keep the hitbox centered on the player's visual rectangle after moving
        self.hitbox.center = self.rect.center

        # Note: Collision detection logic would typically go here or be called from here
        # self.check_collisions(move_x, move_y, collision_sprites)

class Piermaster(pygame.sprite.Sprite):
    """
    Represents the Piermaster NPC (Non-Player Character).
    Currently a static sprite with a fixed position.
    """

    def __init__(self, x: int, y: int) -> None:
        """
        Initializes the Piermaster sprite.

        Args:
            x (int): The x-coordinate for the center of the Piermaster.
            y (int): The y-coordinate for the center of the Piermaster.
        """
        super().__init__() # Initialize the parent Sprite class

        # Load the Piermaster image from the path specified in the config file
        try:
            self.image = pygame.image.load(config.PIERMASTER_IMAGE).convert_alpha()
        except pygame.error as e:
            # Handle potential errors during image loading
            print(f"Error loading piermaster image: {config.PIERMASTER_IMAGE} - {e}")
            # Provide a fallback visual representation
            self.image = pygame.Surface((config.TILE_SIZE, config.TILE_SIZE))
            self.image.fill((0, 0, 255)) # Blue square as fallback
            # Optionally, re-raise the exception
            # raise

        # Get the rectangular area of the image and set its center position
        self.rect = self.image.get_rect(center=(x, y))

        self.dialogue_key = "pierkeeper_generic" # Link to dialogue dictionary
    # No update method is needed for a static NPC unless it needs animation,
    # pathfinding, or other dynamic behavior later.
    # def update(self, *args, **kwargs) -> None:
    #     pass # Placeholder if update logic is added later

# --- Add other sprite classes below this line ---
# Example structure for another NPC:
# class Mayor(pygame.sprite.Sprite):
#     """Represents the Mayor NPC."""
#     def __init__(self, x: int, y: int) -> None:
#         super().__init__()
#         try:
#             self.image = pygame.image.load(config.MAYOR_IMAGE).convert_alpha()
#         except pygame.error as e:
#             print(f"Error loading mayor image: {config.MAYOR_IMAGE} - {e}")
#             self.image = pygame.Surface((config.TILE_SIZE, config.TILE_SIZE))
#             self.image.fill((0, 255, 0)) # Green square fallback
#         self.rect = self.image.get_rect(center=(x, y))
#     # Add update method if the Mayor needs to move or animate
#     # def update(self, *args, **kwargs) -> None:
#     #     pass

class Mayor(pygame.sprite.Sprite):
     """Represents the Mayor NPC."""
     def __init__(self, x: int, y: int) -> None:
         super().__init__()
         try:
             # 1. load the image file specified in config.py
             self.image = pygame.image.load(config.MAYOR_IMAGE).convert_alpha()
         except pygame.error as e:
             # 3. fallback: if loading fails, create a surface with TILE_SIZE dimensions
             print(f"Error loading mayor image: {config.MAYOR_IMAGE} - {e}")
             self.image = pygame.Surface((config.TILE_SIZE, config.TILE_SIZE))
             self.image.fill((0, 255, 0)) # Green square fallback
         # 2. get a rect whose dimensions match the loaded images (self.image)    
         self.rect = self.image.get_rect(center=(x, y))

         self.dialogue_key = "mayor_greeting" # Link to dialogue dictionary
     # Add update method if the Mayor needs to move or animate
     # def update(self, *args, **kwargs) -> None:
     #     pass

class Houseowner(pygame.sprite.Sprite):
     """
     Represents a generic Houseowner NPC.
     Can be instantiated with different images and positions.
     """
     # Add image_path parameter with a default fallback (optional)
     def __init__(self, x: int, y: int, image_path: str = config.HOUSEOWNER_IMAGE, dialogue_key: str = "houseowner0_generic") -> None:
         super().__init__()
         try:
             # Load the image file specified by the image_path parameter
             self.image = pygame.image.load(image_path).convert_alpha()
         except pygame.error as e:
             # Fallback: if loading fails, create a surface with TILE_SIZE dimensions
             print(f"Error loading Houseowner image: {image_path} - {e}")
             self.image = pygame.Surface((config.TILE_SIZE, config.TILE_SIZE))
             # Use a different fallback color to distinguish from Mayor, e.g., purple
             self.image.fill((128, 0, 128)) # Purple square fallback
         # Get a rect whose dimensions match the loaded image (self.image)
         self.rect = self.image.get_rect(center=(x, y))

         self.dialogue_key = dialogue_key # Assign the provided dialogue key

     # Add update method if Houseowner needs to move or animate later
     # def update(self, *args, **kwargs) -> None:
     #     pass