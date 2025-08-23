
from .searchable_text_edit import SearchableTextEdit
from ..global_names import logger
import re
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor, QKeyEvent


class SearchableBoldableTextEdit(SearchableTextEdit):
    def __init__(self):
        super().__init__()
        self._simple_mode = False
        self._components = []
        self._word_indices = []
        self._current_word_selection_index = -1

    def _tokenize(self, text: str):
        if not text:
            return []
        return re.findall(r'__\w[\w\']*__|\w[\w\']*|\S|\s+', text)

    def _update_state_from_text(self, text: str):
        self._components = self._tokenize(text)
        word_pattern = re.compile(r'__\w[\w\']*__|\w[\w\']*')
        self._word_indices = [i for i, token in enumerate(self._components) if word_pattern.fullmatch(token)]
        self._current_word_selection_index = -1

    def _emit_current_word(self):
        if not self._simple_mode or self._current_word_selection_index == -1:
            return

        component_index = self._word_indices[self._current_word_selection_index]
        word = self._components[component_index]
        cleaned_word = re.sub(r'__(.*?)__', r'\1', word)
        if cleaned_word:
            self.double_clicked.emit(cleaned_word)

    def _update_display_and_select(self):
        if not self._simple_mode:
            return

        html_parts = []
        selection_start = -1
        selection_end = -1
        current_pos = 0

        for i, component in enumerate(self._components):
            processed_part = component.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            processed_part = re.sub(r'__([^_]+)__', r'<b>\1</b>', processed_part)

            is_current_word = False
            if self._current_word_selection_index != -1:
                if i == self._word_indices[self._current_word_selection_index]:
                    is_current_word = True

            if is_current_word:
                html_parts.append(f'<span style="background-color: yellow;">{processed_part}</span>')
                selection_start = current_pos
                selection_end = current_pos + len(component)
            else:
                html_parts.append(processed_part)
            
            current_pos += len(component)

        self.setHtml("".join(html_parts))

        if selection_start != -1:
            cursor = self.textCursor()
            cursor.setPosition(selection_start)
            cursor.setPosition(selection_end, QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            cursor = self.textCursor()
            cursor.clearSelection()
            self.setTextCursor(cursor)

    def setSimpleViewMode(self, enabled: bool):
        self._simple_mode = enabled
        self.setReadOnly(enabled)
        if enabled:
            self._update_state_from_text(self.toPlainText())
            self._update_display_and_select()
        else:
            self.setPlainText(self.toPlainText())

    def setText(self, text: str):
        if self._simple_mode:
            self._update_state_from_text(text)
            self._update_display_and_select()
        else:
            super().setText(text)

    def setPlainText(self, text: str):
        if self._simple_mode:
            self._update_state_from_text(text)
            self._update_display_and_select()
        else:
            super().setPlainText(text)

    def keyPressEvent(self, event: QKeyEvent):
        if self._simple_mode:
            if event.key() == Qt.Key_Right:
                if not self._word_indices:
                    event.accept()
                    return
                if self._current_word_selection_index < len(self._word_indices) - 1:
                    self._current_word_selection_index += 1
                self._update_display_and_select()
                self._emit_current_word()
                event.accept()
                return
            elif event.key() == Qt.Key_Left:
                if not self._word_indices:
                    event.accept()
                    return
                if self._current_word_selection_index > 0:
                    self._current_word_selection_index -= 1
                
                if self._current_word_selection_index != -1:
                    self._update_display_and_select()
                    self._emit_current_word()
                event.accept()
                return
        super().keyPressEvent(event)

    def toAnki(self):
        result = re.sub(r'__(.*?)__', r'<b>\1</b>', self.toPlainText())
        result = result.replace('\n', '<br>')
        return result

    def bold(self, word):
        if self._simple_mode:
            return
        logger.debug(f'bolding {word}')
        bolded_sentence = re.sub(r'\b' + re.escape(word) + r'\b', '__' + word + '__', self.toPlainText())
        self.setPlainText(bolded_sentence)

        bolded_word = '__' + word
        cursor = self.textCursor()
        cursor.setPosition(bolded_sentence.rfind(bolded_word) + len(bolded_word))
        self.setTextCursor(cursor)

    def unbold(self):
        if self._simple_mode:
            return
        self.setPlainText(self.toPlainText().replace('__', ''))
