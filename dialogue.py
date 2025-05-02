# dialogue.py
import pygame
from config import * # Assuming config defines colors like WHITE, BLACK, DARK_GRAY etc.
# from sprites import * # Assuming sprites isn't strictly needed for DialogueBox itself
import os # Import os for path joining

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
    # print(f"--- render_textrect received font: {font}") # Debug print removed
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
    def __init__(self, game, text, x, y, width=600, height=200, font_size=30, font_name='White On Black.ttf'):
        super().__init__()
        self.game = game
        self._text = text # Use property for text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        try:
            # Try loading from assets/fonts if it exists, otherwise use the name directly
            # Ensure font_name includes the extension
            font_path = os.path.abspath(os.path.join(ASSETS_DIR, 'Fonts', font_name)) # Get absolute path for clarity
            if os.path.exists(font_path):
                 # print(f"Attempting to load font from path: {font_path}") # Debug print removed
                 self.font = pygame.font.Font(font_path, font_size) # Attempt load
                 # print(f"Successfully created font object from path: {self.font}") # Debug print removed
            else:
                 print(f"Font file not found at: {font_path}. Attempting system font: {font_name}")
                 # Fallback to system font or just the name if it's a system font
                 self.font = pygame.font.Font(font_name, font_size)
                 # print(f"Successfully created font object from system/name: {self.font}") # Debug print removed
        except FileNotFoundError:
            # This specific error is less likely now with the os.path.exists check, but good to keep
            print(f"ERROR (FileNotFoundError): Font '{font_name}' not found. Using default Pygame font.")
            self.font = pygame.font.Font(None, font_size) # Use default font if specified one fails
        except pygame.error as e:
             print(f"ERROR (pygame.error): Failed to load font '{font_name}' from path '{font_path if 'font_path' in locals() else 'N/A'}': {e}. Using default Pygame font.")
             self.font = pygame.font.Font(None, font_size)

        self.text_color = BLACK # Use constants from config
        # Ensure background_color is RGB before adding alpha
        if len(WHITE) == 4: # Check if WHITE from config is RGBA
             self.background_color = WHITE[:3] # Take only RGB
        else:
             self.background_color = WHITE # Assume it's RGB

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
        # Use SRCALPHA for transparency support
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Fill with background color + alpha value (e.g., 200 for semi-transparent)
        alpha_value = 200 # Adjust 0-255 as needed
        self.image.fill((*self.background_color, alpha_value))

        # Draw border onto the image surface using the same alpha value
        # Note: draw.rect doesn't directly support alpha on the surface it draws *to*,
        # but the color itself can have alpha which affects how it blends if the
        # target surface (self.image) has SRCALPHA.
        pygame.draw.rect(self.image, (*self.border_color, alpha_value), self.image.get_rect(), self.border_width)

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
            # print(f"--- DialogueBox._render_text using font: {self.font}") # Debug print removed
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

# --- Updated Cutscene class ---
class Cutscene:
    """Represents a sequence of images, corresponding text lines, and optional background music for a cutscene."""
    def __init__(self, image_paths: list[str | None], sentences: list[str], music_path: str | None = None):
        """
        Args:
            image_paths (list[str | None]): A list of file paths to the images for each slide.
                                            Use None for slides with no image (e.g., black screen).
            sentences (list[str]): A list of text strings for each slide.
                                   Should have the same length as image_paths.
            music_path (str | None, optional): File path to the background music for this cutscene.
                                               Defaults to None (no music).
        """
        if len(image_paths) != len(sentences):
            raise ValueError("Cutscene image_paths and sentences lists must have the same length.")
        self.image_paths = image_paths
        self.sentences = sentences
        self.music_path = music_path # Store the music path
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

# --- Updated Dictionary for Collision-Triggered Cutscenes ---
# The keys (e.g., "story1") MUST match the 'CutsceneTrigger' property values set in Tiled.
# Added the music_path argument to each Cutscene instance.
# Replace placeholder paths with your actual music file paths.
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
        ],
        music_path=f'{ASSETS_DIR}/Music/intro_theme.ogg' # Example music path
    ),
    "another_story": Cutscene( # Example for a second trigger
         image_paths=[
             f'{IMAGES_DIR}/cutscenes/another_1.png',
             f'{IMAGES_DIR}/cutscenes/another_2.png',
         ],
         sentences=[
             "This is the first part of another story, triggered by a different collision.",
             "And this is the concluding slide for that story. Press Enter to return to the game.",
         ],
         music_path=f'{ASSETS_DIR}/Music/another_story_music.ogg' # Example music path
    ),

    # --- STORY1 STORY ONE STORY 1 ---
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
            "Brighton's storms were no strangers—grey, thrashing things that rolled off the Channel like clockwork. But this one, the one they'd later call the Birthday Storm, had teeth.",
            # Slide 2
            "The Chain Pier, fresh as a painted toy, shuddered under the waves. My father, drowned in his oilskin coat, barked at sightseers to clear off. They lingered, clutching hats and laughing like it was all a lark.",
            # Slide 3
            "Then the lightning. No grand omen—just rotten luck. The bolt ripped into the third tower, splintering wood, snapping chains. Planks tore free, skidding into the churn. The crowd's laughter turned to shrieks.",
            # Slide 4
            "Father lunged for a man trapped under the wreckage. A beam gave way. It caught his leg, crushing it flat. I still see it: his knuckles white on the timber, the blood thin and quick in the rain.",
            # Slide 5
            "They dragged him home, boot sloshing. The doctor stitched him up, but he walked crooked ever after. The pier? A few gaps in the deck, scorch marks on the towers. Engineers called it a “miracle,” muttered about lightning rods.",
            # Slide 6
            "Father snorted. “Birthday Storm,” he'd grumble, kneading his knee when the air turned salt-thick. “Sea's just remindin' us who’s boss.” Brighton patched the planks, slapped on fresh paint. Tourists flocked back.",
            # Slide 7
            "But whenever the wind snapped, Father's face went taut, his hand gripping the cane like it was the only thing holding him upright. We build. The sea undoes it."
        ],
        music_path=f'{ASSETS_DIR}/Music/story1_theme.ogg' # Example music path for story 1
    ),
    # -------------------------

    # --- STORY2 STORY TWO STORY 2 ---
    "houseowner2_cutscene": Cutscene(
        image_paths=[
            f'{IMAGES_DIR}/story2.jpg', # Slide 1
            f'{IMAGES_DIR}/story2.jpg', # Slide 2
            f'{IMAGES_DIR}/story2.jpg', # Slide 3
            f'{IMAGES_DIR}/story2.jpg', # Slide 4
            f'{IMAGES_DIR}/story2.jpg', # Slide 5
            f'{IMAGES_DIR}/story2.jpg', # Slide 6
            f'{IMAGES_DIR}/story2.jpg', # Slide 7
            f'{IMAGES_DIR}/story2.jpg', # Slide 8
        ],
        sentences=[
            # Slide 1
            "The woman taps the watercolour above her mantel. “That's *Brighthelmston* by Turner—1824, just after the pier opened. Come, look closer.”",
            # Slide 2
            "She points to the foreground, where a small boat battles the waves. “See how he paints the crew? Just smudges of ochre and white, but you *feel* them fighting the swell. Not heroes, just fools in the wrong place. Like most of us.”",
            # Slide 3
            "You squint. The boat's sails twist like crumpled paper.",
            # Slide 4
            "“Now follow the pier.” Her finger trails the iron chains, stark against the storm. “Brown’s design—all geometry and pride. But Turner *mocks* it. See the rainbow?” A spectral arc glows above the chaos.",
            # Slide 5
            "“Pretty, isn't it? A lie. That's the sublime—beauty that could kill you. The pier's man's answer to the sea. Turner paints the *argument*.”",
            # Slide 6
            "You mutter something about the buildings onshore. “Ah, the Pavilion!” She laughs. “He cheated, turned it sideways to fit the composition. *Picturesque* nonsense. But the details!”",
            # Slide 7
            "She plucks a magnifying glass from her desk. “St. Nicholas’s spire, the Duke of York’s Hotel… all here. Even the half-built Marine Parade. History in a storm.”",
            # Slide 8
            "Her tone softens. “The rainbow’s the joke, though. We build piers, ships, promenades. Nature builds tempests. Turner knew which’d last.” She hands you the glass. “Keep looking. That boat’s still sinking.”"
        ],
        music_path=f'{ASSETS_DIR}/Music/story2_theme.ogg' # Example music path for story 2
    ),

      # --- STORY 3 STORY THREE STORY3 ---
    "houseowner3_cutscene": Cutscene(
        image_paths=[
            f'{IMAGES_DIR}/story3.jpg', # Slide 1
            f'{IMAGES_DIR}/story3.jpg', # Slide 2
            f'{IMAGES_DIR}/story3.jpg', # Slide 3
            f'{IMAGES_DIR}/story3.jpg', # Slide 4
        ],
        sentences=[
            # Slide 1
            "Ever read Porden’s diary from 1802? Crossed to Dieppe on the Eliza—cramped boxes stacked like coffins, he called the cabins. No portholes. Want light? Open your door to the dining room’s chaos. Privacy meant sitting in the dark or burning your own candle. Bedding? Haul it yourself—part of your 400-pound allowance. At least officers shared their table, though the return trip made you pack your own food, even after they gouged your coin.",
            # Slide 2
            "Porden sketched the layout—‘cabinetts stretched too large,’ he scribbled. Took 18 hours. Just boarding was a farce: Eleanor, his daughter, green-faced, hauled into a cot while waves tossed their rowboat. Cabins had curtains for decency, but nothing stifled the stench. Boys swapped sick basins like ghosts.",
            # Slide 3
            "Miss Appleton, though—poor soul. Puked from Brighton till Dieppe, left forgotten on the ship. Porden called her ‘courageous’—a tall, sharp-tongued bluestocking, fluent in French, traveling alone. Carried ashore on a sailor’s back, insensible.",
            # Slide 4
            "Customs cleared, they limped to the English Hotel. Charged London prices for slop, Porden griped. Imagine it—eighteen hours of retching, then overpaying for gristle. Chain Pier’s cushy ferries? Saints’ work compared to this.\" Her smirk was sharp as she jabbed the diary. \"Romantic age, my arse.\""
        ],
        music_path=f'{ASSETS_DIR}/Music/story3_theme.ogg' # Example music path for story 3
    ),

          # --- GO AWAY ---
    "houseowner4_cutscene": Cutscene(
        image_paths=[
            None,
        ],
        sentences=[
            # Updated sentence to match image
            "Go away."
        ],
        music_path=None # No music for this one
    ),
    # Add more entries here for each 'CutsceneTrigger' value you defined in Tiled
    # "story_trigger_3": Cutscene(...)
}
