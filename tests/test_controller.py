import pytest
from unittest.mock import Mock, MagicMock, patch
import tkinter as tk

from src.controllers.app_controller import AppController


class TestAppController:
    """Тесты для AppController"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        # Создаем моки зависимостей
        self.mock_db = Mock()
        self.mock_logger = Mock()
        self.mock_state_manager = Mock()

        # Настройка моков
        self.mock_db.select_where.return_value = []

        # Создаем контроллер с минимальными зависимостями
        self.controller = AppController(
            db_model=self.mock_db,
            logger=self.mock_logger,
            state_manager=self.mock_state_manager,
            show_info=Mock(),
            show_error=Mock(),
            ask_confirmation=Mock(return_value=True)
        )

        # Создаем мок представления
        self.mock_view = Mock()
        self.controller.set_view(self.mock_view)

        # Создаем мок корневого окна
        self.mock_root = Mock()
        self.controller.set_root(self.mock_root)

    def test_initialization(self):
        """Тест инициализации контроллера"""
        assert self.controller.db == self.mock_db
        assert self.controller.logger == self.mock_logger
        assert self.controller.state_manager == self.mock_state_manager
        assert "selected_year" in self.controller.current_state
        assert self.controller.current_state["language"] == "en"

    def test_change_language_success(self):
        """Тест успешной смены языка"""
        with patch('src.utils.i18n.I18n.load_locale') as mock_load:
            result = self.controller.change_language("ru")

            assert result is True
            mock_load.assert_called_once_with("ru")
            assert self.controller.current_state["language"] == "ru"
            self.mock_state_manager.save_state.assert_called_once()
            self.mock_logger.info.assert_called()

    def test_change_language_same_language(self):
        """Тест смены на тот же язык"""
        self.controller.current_state["language"] = "ru"

        result = self.controller.change_language("ru")

        assert result is True
        # Не должно быть вызова сохранения состояния
        self.mock_state_manager.save_state.assert_not_called()

    def test_change_language_error(self):
        """Тест ошибки при смене языка"""
        with patch('src.utils.i18n.I18n.load_locale', side_effect=Exception("Test error")):
            result = self.controller.change_language("ru")

            assert result is False
            self.mock_logger.error.assert_called()

    def test_get_current_language(self):
        """Тест получения текущего языка"""
        self.controller.current_state["language"] = "fr"
        assert self.controller.get_current_language() == "fr"

    def test_get_available_languages(self):
        """Тест получения доступных языков"""
        languages = self.controller.get_available_languages()
        assert languages == ["ru", "en"]

    def test_save_current_state(self):
        """Тест сохранения текущего состояния"""
        # Настраиваем мок представления с комбобоксами
        self.mock_view.year = Mock(get=Mock(return_value="2024"))
        self.mock_view.month = Mock(get=Mock(return_value="01"))
        self.mock_view.groups = Mock(get=Mock(return_value="Group A"))
        self.mock_view.lessons = Mock(get=Mock(return_value="Math"))
        self.mock_view.root = Mock(geometry=Mock(return_value="800x600"))

        self.controller.save_current_state()

        # Проверяем, что состояние обновилось
        assert self.controller.current_state["selected_year"] == "2024"
        assert self.controller.current_state["selected_month"] == "01"
        assert self.controller.current_state["selected_group"] == "Group A"
        assert self.controller.current_state["selected_lesson"] == "Math"

        # Проверяем вызов сохранения
        self.mock_state_manager.save_state.assert_called_once_with(
            self.controller.current_state
        )

    def test_save_current_state_error(self):
        """Тест ошибки при сохранении состояния"""
        self.mock_state_manager.save_state.side_effect = Exception("Test error")

        # Не должно быть исключения
        self.controller.save_current_state()

        # Должен быть лог ошибки
        self.mock_logger.error.assert_called()

    def test_clear_saved_state(self):
        """Тест очистки сохраненного состояния"""
        self.mock_state_manager.clear_state.return_value = True

        result = self.controller.clear_saved_state()

        assert result is True
        self.mock_state_manager.clear_state.assert_called_once()
        self.mock_logger.info.assert_called()

    def test_get_state_info(self):
        """Тест получения информации о состоянии"""
        mock_info = {"exists": True, "size": 1024}
        self.mock_state_manager.get_state_info.return_value = mock_info

        result = self.controller.get_state_info()

        assert result == mock_info
        self.mock_state_manager.get_state_info.assert_called_once()

    def test_save_data(self):
        """Тест сохранения данных"""
        self.controller.save_data()

        self.mock_db._db.commit.assert_called_once()
        self.mock_logger.info.assert_called_with("Data saved to database")

    def test_db_operations(self):
        """Тест базовых операций с БД"""
        # Проверяем, что методы делегируются к БД
        self.controller.insert_date("2024", "01", "15")
        self.mock_db.insert_date.assert_called_once_with("2024", "01", "15")

        self.controller.update_group("Old", "New")
        self.mock_db.update_group.assert_called_once_with("Old", "New")

        self.controller.delete_student("Group", "Surname", "Name", "Patronymic")
        self.mock_db.delete_student.assert_called_once_with("Group", "Surname", "Name", "Patronymic")

    def test_export_methods_without_exporter(self):
        """Тест методов экспорта без экспортера"""
        # Проверяем, что методы не падают без экспортера
        self.controller.exporter = None

        # Должны вызывать show_error
        self.controller.export_json()
        self.controller.show_error.assert_called_with("Error", "Экспортер не доступен")

    def test_import_methods_without_importer(self):
        """Тест методов импорта без импортера"""
        self.controller.importer = None

        self.controller.auto_detect_and_import("test.json")
        self.controller.show_error.assert_called_with("Error", "Импортер не доступен")

    def test_close_program(self):
        """Тест закрытия программы"""
        self.controller.close_program()

        self.mock_db.close.assert_called_once()
        self.mock_root.destroy.assert_called_once()

    def test_main_frame_reset(self):
        """Тест сброса главного фрейма"""
        self.controller.main_frame_reset(only_combobox_values=True)

        # Принимаем оба варианта - именованный или позиционный аргумент
        self.mock_view.main_frame_reset.assert_called_once()

        # Проверяем аргументы вызова
        call_args = self.mock_view.main_frame_reset.call_args

        if call_args.kwargs:  # Именованные аргументы
            assert call_args.kwargs.get('only_combobox_values') == True
        else:  # Позиционные аргументы
            assert len(call_args.args) > 0 and call_args.args[0] == True