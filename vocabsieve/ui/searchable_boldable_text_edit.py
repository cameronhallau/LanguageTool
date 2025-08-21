from .searchable_text_edit import SearchableTextEdit
from ..global_names import logger
import re
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeyEvent, QTextCursor


class SearchableBoldableTextEdit(SearchableTextEdit):
    def __init__(self):
        super().__init__()
        self._simple_mode = False
        self._original_text = ""
        self._components = []  # A list of all tokens (words and delimiters)
        self._word_indices = []  # A list of indices into _components that are words
        self._current_word_selection_index = -1  # An index into _word_indices

        self.lookup_timer = QTimer(self)
        self.lookup_timer.setSingleShot(True)
        self.lookup_timer.setInterval(1000)  # 1 second delay
        self.lookup_timer.timeout.connect(self._emit_current_word)

    def _tokenize(self, text: str):
        """Tokenize the text into words, punctuation, and whitespace."""
        if not text:
            return []
        # This regex finds: 1. bolded words, 2. normal words, 3. any non-whitespace/non-word char, 4. whitespace
        return re.findall(r'__\w[\w\']*__|\w[\w\']*|\S|\s+', text)

    def _update_state_from_text(self, text: str):
        """Helper to update internal state when text changes."""
        self._original_text = text
        self._components = self._tokenize(self._original_text)
        word_pattern = re.compile(r'__\w[\w\']*__|\w[\w\']*')
        self._word_indices = [i for i, token in enumerate(self._components) if word_pattern.fullmatch(token)]

        if self._word_indices:
            self._current_word_selection_index = 0
        else:
            self._current_word_selection_index = -1

    def _emit_current_word(self):
        """Gets the current word, cleans it, and emits the double_clicked signal."""
        if not self._simple_mode or self._current_word_selection_index == -1:
            return

        component_index = self._word_indices[self._current_word_selection_index]
        word = self._components[component_index]

        cleaned_word = re.sub(r'__(.*?)__', r'\1', word)
        if cleaned_word:
            self.double_clicked.emit(cleaned_word)

    def setSimpleViewMode(self, enabled: bool):
        """Enable or disable the simple view mode."""
        self._simple_mode = enabled
        self.setReadOnly(enabled)
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        
        if enabled:
            self._update_state_from_text(self.toPlainText())
            self._update_display()
            self._select_current_word()
            self.lookup_timer.start()
        else:
            self.lookup_timer.stop()
            self.setPlainText(self._original_text)
            # Clear selection when leaving simple mode
            cursor = self.textCursor()
            cursor.clearSelection()
            self.setTextCursor(cursor)

    def setText(self, text: str):
        """Override setText to handle simple mode formatting."""
        if self._simple_mode:
            self.lookup_timer.stop()
            self._update_state_from_text(text)
            self._update_display()
            self._select_current_word()
            self.lookup_timer.start()
        else:
            super().setText(text)
    
    def setPlainText(self, text: str):
        """Override setPlainText to handle simple mode formatting."""
        if self._simple_mode:
            self.lookup_timer.stop()
            self._update_state_from_text(text)
            self._update_display()
            self._select_current_word()
            self.lookup_timer.start()
        else:
            super().setPlainText(text)

    def _select_current_word(self):
        """Visually select the current word in the text box."""
        if self._current_word_selection_index == -1:
            cursor = self.textCursor()
            cursor.clearSelection()
            self.setTextCursor(cursor)
            return

        start_pos = 0
        target_component_index = self._word_indices[self._current_word_selection_index]
        for i in range(target_component_index):
            start_pos += len(self._components[i])
        
        word_len = len(self._components[target_component_index])

        cursor = self.textCursor()
        cursor.setPosition(start_pos)
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, word_len)
        self.setTextCursor(cursor)

    def _update_display(self):
        """Update the text display with bolding."""
        if not self._simple_mode:
            self.setPlainText("")
            return
            
        html_parts = []
        for component in self._components:
            processed_part = component.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            processed_part = re.sub(r'__([^_]+)__', r'<b>\1</b>', processed_part)
            html_parts.append(processed_part)
        
        self.setHtml("".join(html_parts))
        
    def unbold(self):
        self.setPlainText(self.toPlainText().replace('__', ''))

    def bold(self, word):
        logger.debug(f'bolding {word}')
        bolded_sentence = re.sub(r'\b' + re.escape(word) + r'\b', '__' + word + '__', self.toPlainText())
        self.setPlainText(bolded_sentence)

        bolded_word = '__' + word
        cursor = self.textCursor()
        cursor.setPosition(bolded_sentence.rfind(bolded_word) + len(bolded_word))
        self.setTextCursor(cursor)

    def toAnki(self):
        # substitute __word__ with <b>word</b>
        result = re.sub(r'__(.*?)__', r'<b>\1</b>', self.toPlainText())
        # substitute newlines with <br>
        result = result.replace('\n', '<br>')
        return result
