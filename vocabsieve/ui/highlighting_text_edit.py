import re
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QTextEdit


class HighlightingTextEdit(QTextEdit):
    """
    A QTextEdit that supports word highlighting and navigation in a 'simple mode'.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._simple_mode = False
        self._original_text = ""
        self._words = []
        self._current_word_index = -1

    def setSimpleViewMode(self, enabled: bool):
        """
        Enable or disable the simple view mode.
        """
        self._simple_mode = enabled
        self.setReadOnly(enabled)
        # Hide cursor when read-only
        self.setTextInteractionFlags(Qt.NoTextInteraction if enabled else Qt.TextEditorInteraction)
        
        if enabled:
            self._current_word_index = 0
            self._update_display()
        else:
            # Restore plain text and default behavior
            super().setText(self._original_text)

    def setText(self, text: str):
        """
        Override setText to handle simple mode formatting.
        """
        self._original_text = text
        if self._simple_mode:
            # When text is set in simple mode, reset highlight to first word
            self._current_word_index = 0
            self._update_display()
        else:
            super().setText(text)

    def _update_display(self):
        """
        Update the text display with bolding and word highlighting.
        """
        if not self._simple_mode or not self._original_text:
            self.setHtml("")
            return

        # Split the original text into words and separators (whitespace)
        components = re.split(r'(\s+)', self._original_text)
        
        # Create a list of just the words to calculate indices
        plain_words = [c for c in components if c.strip()]
        self._words = plain_words

        if not self._words:
            # If there are no words, just process for bolding
            html = re.sub(r'__([^_]+)__', r'<b>\1</b>', self._original_text)
            self.setHtml(html)
            return

        # Clamp the current index to be within bounds
        if self._current_word_index < 0:
            self._current_word_index = 0
        if self._current_word_index >= len(self._words):
            self._current_word_index = len(self._words) - 1

        new_html_parts = []
        word_cursor = 0
        for part in components:
            if not part.strip():  # It's whitespace
                new_html_parts.append(part)
                continue

            # It's a word component
            processed_part = re.sub(r'__([^_]+)__', r'<b>\1</b>', part)

            if word_cursor == self._current_word_index:
                # This is the word to highlight
                highlighted_part = f'<span style="background-color: yellow;">{processed_part}</span>'
                new_html_parts.append(highlighted_part)
            else:
                new_html_parts.append(processed_part)
            
            word_cursor += 1
        
        final_html = "".join(new_html_parts)
        self.setHtml(final_html)
        
    def keyPressEvent(self, event: QKeyEvent):
        """
        Handle left and right arrow keys for word navigation in simple mode.
        """
        if self._simple_mode:
            accepted = False
            if event.key() == Qt.Key_Right:
                if self._current_word_index < len(self._words) - 1:
                    self._current_word_index += 1
                    self._update_display()
                accepted = True
            elif event.key() == Qt.Key_Left:
                if self._current_word_index > 0:
                    self._current_word_index -= 1
                    self._update_display()
                accepted = True
            
            if accepted:
                event.accept()
                return

        super().keyPressEvent(event)
