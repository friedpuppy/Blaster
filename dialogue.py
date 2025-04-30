# dialogue.py
import pygame
from config import * # Assuming config defines colors like WHITE, BLACK, DARK_GRAY etc.
# from sprites import * # Assuming sprites isn't strictly needed for DialogueBox itself

# --- TextRectException and render_textrect remain the same ---
class TextRectException(Exception): # Inherit from Exception for better practice
    def __init__(self, message=None):
        self.message = message
        super().__init__(self.message) # Call parent constructor
    def __str__(self):
        return self.message if self.message else "TextRectException"

def render_textrect(string, font, rect, text_color, background_color, justification=0):
    """
    Returns a surface containing the passed text string, reformatted
    to fit within the given rect, word-wrapped as necessary. The text
    will be anti-aliased.

    Takes the following arguments:

    string - the text you wish to render. \n begins a new line.
    font - a Font object
    rect - a rect object that the text will be drawn into.
    text_color - a color tuple (ex (255, 0, 0) for red)
    background_color - a color tuple (ex (0, 0, 0) for black)
    justification - 0 (default) left-justified
                    1 centered
                    2 right-justified

    Returns
        Surface object with the text drawn onto it.

    Raises
        TextRectException if the text cannot fit.
    """
    final_lines = []
    requested_lines = string.splitlines()

    # --- Word Wrapping Logic ---
    for requested_line in requested_lines:
        if font.size(requested_line)[0] > rect.width:
            words = requested_line.split(' ')
            # Check for words longer than the line width
            for word in words:
                if font.size(word)[0] >= rect.width:
                    raise TextRectException(
                        f"The word '{word}' is too long ({font.size(word)[0]}px) to fit in the rect width ({rect.width}px)."
                    )
            # Wrap words to fit the line
            accumulated_line = ""
            for word in words:
                test_line = accumulated_line + word + " "
                # Check if the test line fits within the width
                if font.size(test_line)[0] < rect.width:
                    accumulated_line = test_line
                else:
                    final_lines.append(accumulated_line.rstrip()) # Add the previous line
                    accumulated_line = word + " " # Start a new line
            final_lines.append(accumulated_line.rstrip()) # Add the last accumulated line
        else:
            final_lines.append(requested_line) # Line fits without wrapping

    # --- Surface Creation and Text Rendering ---
    surface = pygame.Surface(rect.size, pygame.SRCALPHA) # Use SRCALPHA for transparency
    surface.fill(background_color) # Fill background

    accumulated_height = 0
    line_spacing = font.get_linesize() # Use font's line spacing

    for i, line in enumerate(final_lines):
        if accumulated_height + line_spacing > rect.height:
            # Optional: Add an indicator like "..." if text overflows vertically
            # if i > 0: # Check if there was at least one previous line
            #     prev_line_surf = surface.copy() # Keep previous state
            #     ellipsis_surf = font.render("...", True, text_color)
            #     ellipsis_rect = ellipsis_surf.get_rect(bottomright=(rect.width, accumulated_height))
            #     # Blit ellipsis slightly overlapping the last visible line's bottom
            #     surface.blit(ellipsis_surf, ellipsis_rect)

            print(f"Warning: Text truncated. Content height ({accumulated_height + line_spacing}px) exceeds rect height ({rect.height}px).")
            break # Stop rendering lines that won't fit

        if line != "":
            try:
                tempsurface = font.render(line, True, text_color) # Render with anti-aliasing
            except pygame.error as e:
                 raise TextRectException(f"Pygame font rendering error: {e}")

            text_width = tempsurface.get_width()
            blit_pos_x = 0 # Default to left justification

            # --- Justification Logic ---
            if justification == 1: # Centered
                blit_pos_x = (rect.width - text_width) // 2
            elif justification == 2: # Right
                blit_pos_x = rect.width - text_width
            elif justification != 0: # Invalid justification
                raise TextRectException(f"Invalid justification argument: {justification}")

            surface.blit(tempsurface, (blit_pos_x, accumulated_height))

        accumulated_height += line_spacing # Move down for the next line

    return surface
# --- End of TextRect ---


class DialogueBox(pygame.sprite.Sprite):
    # --- DialogueBox class remains the same ---
    def __init__(self, game, text, x, y, width=600, height=200, font_size=30, font_name='monofonto rg.otf'):
        super().__init__()
        self.game = game
        self._text = text # Use property for text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        try:
            self.font = pygame.font.Font(font_name, font_size)
        except FileNotFoundError:
            print(f"Warning: Font '{font_name}' not found. Using default Pygame font.")
            self.font = pygame.font.Font(None, font_size) # Use default font if specified one fails

        self.text_color = BLACK # Use constants from config
        self.background_color = WHITE
        self.border_color = DARK_GRAY
        self.border_width = 2
        self.padding = 10
        self.active = False # Start inactive

        # Internal surfaces
        self.image = None # Main surface for the box background + border
        self.rect = None  # Rect for the main surface position/size
        self.text_surface = None # Surface with the rendered text
        self.text_rect = None # Rect for positioning text *within* the box

        self._create_base_surface() # Create background/border surface
        self.update_text(self._text) # Render initial text

    def _create_base_surface(self):
        """Creates the background and border surface."""
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(self.background_color)
        # Draw border onto the image surface
        pygame.draw.rect(self.image, self.border_color, self.image.get_rect(), self.border_width)
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

    def _render_text(self):
        """Renders the current text onto self.text_surface."""
        # Calculate the area available for text inside padding
        text_area_width = self.width - (self.padding * 2)
        text_area_height = self.height - (self.padding * 2)

        if text_area_width <= 0 or text_area_height <= 0:
             print("Warning: DialogueBox padding is too large for its dimensions.")
             # Create a small dummy surface to avoid errors
             self.text_surface = pygame.Surface((1, 1), pygame.SRCALPHA)
             self.text_rect = self.text_surface.get_rect(topleft=(self.padding, self.padding))
             return

        text_render_rect = pygame.Rect(0, 0, text_area_width, text_area_height)

        try:
            # Render text using the utility function. Pass SRCALPHA for transparency.
            self.text_surface = render_textrect(
                self._text,
                self.font,
                text_render_rect,
                self.text_color,
                (0, 0, 0, 0), # Transparent background for the text surface itself
                justification=0
            )
            # Position the text surface inside the padding
            self.text_rect = self.text_surface.get_rect(topleft=(self.padding, self.padding))

        except TextRectException as e:
            print(f"Error rendering text: {e}")
            # Fallback: Render an error message
            error_text = "Error: Text too long or invalid."
            self.text_surface = self.font.render(error_text, True, self.text_color)
            # Still position it within padding
            self.text_rect = self.text_surface.get_rect(topleft=(self.padding, self.padding))
        except Exception as e: # Catch other potential errors
             print(f"An unexpected error occurred during text rendering: {e}")
             # Fallback: Render a generic error message
             error_text = "Error rendering text."
             self.text_surface = self.font.render(error_text, True, self.text_color)
             self.text_rect = self.text_surface.get_rect(topleft=(self.padding, self.padding))


    def update_text(self, new_text):
        """Updates the text displayed in the box and re-renders it."""
        self._text = new_text
        self._render_text() # Re-render the text surface

    def draw(self, surface):
        """Draws the dialogue box onto the target surface if active."""
        if self.active and self.image and self.text_surface:
            # 1. Draw the background/border image
            surface.blit(self.image, self.rect.topleft)
            # 2. Draw the text surface onto the target surface,
            #    offsetting by the box's position and the text's internal padding position.
            text_screen_pos = (self.rect.x + self.text_rect.x, self.rect.y + self.text_rect.y)
            surface.blit(self.text_surface, text_screen_pos)

    def show(self):
        """Activates the dialogue box."""
        self.active = True

    def hide(self):
        """Deactivates the dialogue box."""
        self.active = False

    def toggle(self):
        """Toggles the visibility of the dialogue box."""
        self.active = not self.active

    @property
    def text(self):
        """Getter for the text content."""
        return self._text

    @text.setter
    def text(self, value):
        """Setter for the text content that automatically updates the surface."""
        self.update_text(value)

# --- Dialogue class remains the same ---
class Dialogue:
    """Represents a sequence of text lines for an NPC."""
    def __init__(self, name: str, lines: list[str]):
        """
        Args:
            name (str): The name of the speaker (e.g., "Mayor", "Resident").
            lines (list[str]): A list of text strings for the dialogue.
        """
        self.name = name
        self.lines = lines
        self.current_line = 0 # Index of the currently displayed line

    def get_current_line(self) -> str | None:
        """Returns the current line without advancing."""
        if 0 <= self.current_line < len(self.lines):
            return self.lines[self.current_line]
        return None # Should not happen if reset correctly

    def next_line(self) -> str | None:
        """Advances to the next line and returns it. Returns None if at the end."""
        self.current_line += 1
        if self.current_line < len(self.lines):
            return self.lines[self.current_line]
        else:
            # self.current_line = len(self.lines) # Stay at end index?
            return None # Signal end of dialogue

    def is_finished(self) -> bool:
        """Checks if the dialogue has reached the end."""
        return self.current_line >= len(self.lines)

    def reset(self) -> None:
        """Resets the dialogue back to the first line."""
        self.current_line = 0

# --- Cutscene class remains largely the same, ensure it takes lists ---
class Cutscene:
    # ... (Cutscene class definition) ...
    """Represents a sequence of images and corresponding text lines for a cutscene."""
    def __init__(self, image_paths: list[str | None], sentences: list[str]):
        """
        Args:
            image_paths (list[str | None]): A list of file paths to the images for each slide.
                                            Use None for slides with no image (e.g., black screen).
            sentences (list[str]): A list of text strings for each slide.
                                   Should have the same length as image_paths.
        """
        if len(image_paths) != len(sentences):
            raise ValueError("Cutscene image_paths and sentences lists must have the same length.")
        self.image_paths = image_paths
        self.sentences = sentences
        self.num_slides = len(sentences) # Store the total number of slides

# --- Cleaned dialogues dictionary ---
dialogues = {
    # Keeping simple dialogues
    "door_1_npc": Dialogue("Door1NPC", ["Hello! I live here."]), # Example if used by a tile
    "rude_npc": Dialogue("RudeNPC", ["Go away! I don't have time for you.", "Leave me alone!"]),

    # --- Dialogue Keys for NPCs (Make sure these match keys used in main.py) ---
    "pierkeeper_generic": Dialogue("Pierkeeper", ["The pier needs fixing... it's a tragedy."]),
    "mayor_greeting": Dialogue("Mayor", ["Ah, hello there!", "Terrible business with the pier, isn't it?"]),
    "houseowner0_generic": Dialogue("Resident", ["Just admiring the view.", "Shame about the pier."]),
    "houseowner1_generic": Dialogue("Resident", ["It was such a lovely pier before the storm."]),
    "houseowner2_generic": Dialogue("Resident", ["I hope they can repair it soon."]),
    "houseowner3_generic": Dialogue("Resident", ["The town needs that pier."]),

    # --- Add your NEW stories/dialogues here! ---
    "new_story_npc_1": Dialogue("Mysterious Figure", ["Have you seen the state of the pier?", "Something doesn't feel right about that storm..."]),
    "shopkeeper_intro": Dialogue("Shopkeeper", ["Welcome!", "Looking for supplies?", "Can't offer much with the pier out of commission."]),
    # Add more as needed...
}

# --- NEW: Dictionary for Collision-Triggered Cutscenes ---
# The keys (e.g., "story1") MUST match the 'CutsceneTrigger' property values set in Tiled.
collision_cutscenes: dict[str, Cutscene] = {
    "intro_story": Cutscene( # Example key, replace with your Tiled value
        image_paths=[
            # Note: Corrected path assuming 'cutscenes' subfolder
            f'{IMAGES_DIR}/cutscenes/intro_slide_1.png',
            f'{IMAGES_DIR}/cutscenes/intro_slide_2.png',
            f'{IMAGES_DIR}/cutscenes/intro_slide_3.png',
            None, # Example: A slide with just text on black background
        ],
        sentences=[
            "It is the morning of October 16th in the year of our Lord 1833. A most terrible and violent storm the night prior has left the mighty Chain Pier in a ruinous state.",
            "The second bridge is hanging down almost touching the sea, a testament to the storm's fury.",
            "Only the twisted ropes of the third bridge remain, dangling uselessly over the churning waves.",
            "Work to repair it must be commenced as soon as possible, for without the Pier, the town's lifeline to the sea is severed!"
        ]
    ),
    "another_story": Cutscene( # Example for a second trigger
         image_paths=[
             f'{IMAGES_DIR}/cutscenes/another_1.png',
             f'{IMAGES_DIR}/cutscenes/another_2.png',
         ],
         sentences=[
             "This is the first part of another story, triggered by a different collision.",
             "And this is the concluding slide for that story. Press Enter to return to the game.",
         ]
    ),

    # --- UPDATED ENTRY ---
    "houseowner1_cutscene": Cutscene(
        image_paths=[
            f'{IMAGES_DIR}/story1.jpg', # Slide 1
            f'{IMAGES_DIR}/story1.jpg', # Slide 2
            f'{IMAGES_DIR}/story1.jpg', # Slide 3
            f'{IMAGES_DIR}/story1.jpg', # Slide 4
            f'{IMAGES_DIR}/story1.jpg', # Slide 5
            f'{IMAGES_DIR}/story1.jpg', # Slide 6
            f'{IMAGES_DIR}/story1.jpg'  # Slide 7
        ],
        sentences=[
            # Slide 1
            "Brighton’s storms were no strangers—grey, thrashing things that rolled off the Channel like clockwork. But this one, the one they’d later call the Birthday Storm, had teeth.",
            # Slide 2
            "The Chain Pier, fresh as a painted toy, shuddered under the waves. My father, drowned in his oilskin coat, barked at sightseers to clear off. They lingered, clutching hats and laughing like it was all a lark.",
            # Slide 3
            "Then the lightning. No grand omen—just rotten luck. The bolt ripped into the third tower, splintering wood, snapping chains. Planks tore free, skidding into the churn. The crowd’s laughter turned to shrieks.",
            # Slide 4
            "Father lunged for a man trapped under the wreckage. A beam gave way. It caught his leg, crushing it flat. I still see it: his knuckles white on the timber, the blood thin and quick in the rain.",
            # Slide 5
            "They dragged him home, boot sloshing. The doctor stitched him up, but he walked crooked ever after. The pier? A few gaps in the deck, scorch marks on the towers. Engineers called it a “miracle,” muttered about lightning rods.",
            # Slide 6
            "Father snorted. “Birthday Storm,” he’d grumble, kneading his knee when the air turned salt-thick. “Sea’s just remindin’ us who’s boss.” Brighton patched the planks, slapped on fresh paint. Tourists flocked back.",
            # Slide 7
            "But whenever the wind snapped, Father’s face went taut, his hand gripping the cane like it was the only thing holding him upright. We build. The sea undoes it."

        ]
        
    ),
    # -------------------------

    # --- UPDATED ENTRY ---
    "houseowner2_cutscene": Cutscene(
        image_paths=[
            f'{IMAGES_DIR}/story2.jpg' # Updated path
        ],
        sentences=[
            # Updated sentence to match image
            "A depiction of the terrible storm of 1824. Press Enter to close."
        ]
    ),

      # --- UPDATED ENTRY ---
    "houseowner3_cutscene": Cutscene(
        image_paths=[
            f'{IMAGES_DIR}/story3.jpg' # Updated path
        ],
        sentences=[
            # Updated sentence to match image
            "A depiction of the terrible storm of 1824. Press Enter to close."
        ]
    ),  

          # --- UPDATED ENTRY ---
    "houseowner4_cutscene": Cutscene(
        image_paths=[
            f'{IMAGES_DIR}/story4.jpg' # Updated path
        ],
        sentences=[
            # Updated sentence to match image
            "A depiction of the terrible storm of 1824. Press Enter to close."
        ]
    ),  
    # Add more entries here for each 'CutsceneTrigger' value you defined in Tiled
    # "story_trigger_3": Cutscene(...)
}

# --- Cutscene class (from original file, now potentially redundant if using collision_cutscenes) ---
# You can keep this if you use it elsewhere, or remove it if collision_cutscenes replaces its use case.
# class Cutscene:
#     def __init__(self, sentences, images):
#         self.sentences = sentences
#         self.images = images

# --- cutscenes dictionary (from original file, now potentially redundant) ---
# Keep or remove based on whether you still need the 'intro' cutscene triggered differently.
# cutscenes = {
#     "intro": Cutscene(
#         sentences=[ ... ], images=[ ... ]
#     )
# }
