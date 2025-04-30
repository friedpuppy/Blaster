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

    for requested_line in requested_lines:
        if font.size(requested_line)[0] > rect.width:
            words = requested_line.split(' ')
            for word in words:
                if font.size(word)[0] >= rect.width:
                    raise TextRectException(
                        f"The word '{word}' is too long ({font.size(word)[0]}px) to fit in the rect width ({rect.width}px)."
                    )
            accumulated_line = ""
            for word in words:
                test_line = accumulated_line + word + " "
                if font.size(test_line)[0] < rect.width:
                    accumulated_line = test_line
                else:
                    final_lines.append(accumulated_line.rstrip()) # Remove trailing space
                    accumulated_line = word + " "
            final_lines.append(accumulated_line.rstrip()) # Remove trailing space
        else:
            final_lines.append(requested_line)

    surface = pygame.Surface(rect.size, pygame.SRCALPHA) # Use SRCALPHA for potential transparency
    surface.fill(background_color) # Fill only if needed, or make transparent

    accumulated_height = 0
    line_spacing = font.get_linesize() # More reliable than font.size()[1]

    for line in final_lines:
        if accumulated_height + line_spacing > rect.height: # Check before rendering
             # Allow text to be cut off instead of raising an error?
             # Or maybe render an indicator like "..."
            print(f"Warning: Text truncated. Content height ({accumulated_height + line_spacing}px) exceeds rect height ({rect.height}px).")
            break # Stop rendering lines that won't fit
            # raise TextRectException(f"Once word-wrapped, the text string was too tall ({accumulated_height + line_spacing}px) to fit in the rect height ({rect.height}px).")

        if line != "":
            try:
                # Render with anti-aliasing (True)
                tempsurface = font.render(line, True, text_color)
            except pygame.error as e:
                 raise TextRectException(f"Pygame font rendering error: {e}")

            text_width = tempsurface.get_width()

            if justification == 0: # Left
                surface.blit(tempsurface, (0, accumulated_height))
            elif justification == 1: # Centered
                surface.blit(tempsurface, ((rect.width - text_width) // 2, accumulated_height))
            elif justification == 2: # Right
                surface.blit(tempsurface, (rect.width - text_width, accumulated_height))
            else:
                raise TextRectException(f"Invalid justification argument: {justification}")

        accumulated_height += line_spacing # Use line spacing for consistent height

    return surface
# --- End of TextRect ---


class DialogueBox(pygame.sprite.Sprite):
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

        self.text_color = WHITE # Use constants from config
        self.background_color = BLACK
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

# --- Dialogue and Cutscene classes remain the same ---
class Dialogue:
    # ... (Dialogue class remains the same) ...
    def __init__(self, name, lines, quest_stage_advance=None, money_given=0, story_mode=False, story_lines=None):
        self.name = name
        self.lines = lines
        self.current_line = 0
        self.quest_stage_advance = quest_stage_advance  # What quest stage to advance to
        self.money_given = money_given
        self.has_given_money = False
        self.story_mode = story_mode
        self.story_lines = story_lines if story_mode else []

    def get_current_line(self):
        """Returns the current line without advancing."""
        if 0 <= self.current_line < len(self.lines):
            return self.lines[self.current_line]
        return None # Or maybe the last line?

    def next_line(self):
        """Advances to the next line and returns it. Returns None if at the end."""
        self.current_line += 1
        if self.current_line >= len(self.lines):
            # self.current_line = len(self.lines) # Stay at end index?
            return None # Signal end of dialogue
        return self.lines[self.current_line]

    def is_finished(self):
        """Checks if the dialogue has reached the end."""
        return self.current_line >= len(self.lines)

    def reset(self):
        self.current_line = 0
        self.has_given_money = False # Reset money flag too if needed

class Cutscene:
    def __init__(self, sentences, images):
        self.sentences = sentences
        self.images = images
# --- dialogues and cutscenes dictionaries remain the same ---
dialogues = {
    "door_1_npc": Dialogue("Door1NPC", ["Hello! I live here."]),
    "donor1": Dialogue("Donor 1", ["Oh no, the pier is broken!", "I really hope this money helps.", "Good luck!"], quest_stage_advance="talked_to_donor1", money_given=5),
    "donor2": Dialogue("Donor 2", ["I heard about the pier.", "Here's 10 gold to help.", "I hope it gets fixed soon!"], quest_stage_advance="talked_to_donor2", money_given=10),
    "donor3": Dialogue("Donor 3", ["The pier is in bad shape.", "I can spare 2 gold.", "Be careful out there!"], quest_stage_advance="talked_to_donor3", money_given=2),
    "donor1_done": Dialogue("Donor 1", ["Thanks for helping with the pier!", "I have no more money to give."], money_given=0),
    "donor2_done": Dialogue("Donor 2", ["Thanks for helping with the pier!", "I have no more money to give."], money_given=0),
    "donor3_done": Dialogue("Donor 3", ["Thanks for helping with the pier!", "I have no more money to give."], money_given=0),
    "story_teller": Dialogue("Story Teller", ["This is the start of a story!"], story_mode=True, story_lines=["This is the first line of the story.", "This is the second line.", "This is the third line."]),
    "pierkeeper": Dialogue("Pierkeeper", [
        "Oh, the Chain Pier! What a terrible sight after last night's storm.",
        "The second bridge is hanging precariously, and the third is gone entirely!",
        "We need to gather funds to repair it. Can you help?",
        "Speak to the townsfolk, they may be able to pledge monetary support."
    ], quest_stage_advance="talked_to_pierkeeper"),
    "pierkeeper_intro": Dialogue("Pierkeeper", ["Hello there, I need to talk to you about the pier."], quest_stage_advance="talked_to_pierkeeper"), #added this line
    "pierkeeper_done": Dialogue("Pierkeeper", ["Thank you for helping to repair the pier!", "I have no more to say."], money_given=0),
    "rude_npc": Dialogue("RudeNPC", ["Go away! I don't have time for you.", "Leave me alone!"]),
}

cutscenes = {
    "intro": Cutscene(
        sentences=[
            "It is the morning of October 16th in the year of our Lord 1833. A most terrible and violent storm the night prior has left the mighty Chain Pier in a ruinous state.",
            "The second bridge is hanging down almost touching the sea.",
            "Only the ropes of the third bridge remain.",
            "Work to repair it must be commenced as soon as possible, for without the Pier there would be no way to dock ships!"
        ],
        images=[
            'game/img/cutscene_image_1.png',  # Image _1
            'game/img/cutscene_image_2.png',  # Image _2
            'game/img/cutscene_image_3.png',  # Image _3
            None  # Black screen
        ]
    )
}
