import os


class DataImporter:
    """Класс для импорта данных в базу данных"""

    def __init__(self, db, serializer, xml_serializer, os_module=None):
        """
        Инициализация импортера

        Args:
            db: Экземпляр DatabaseWork
            serializer: Экземпляр Serializer
            xml_serializer: Экземпляр XMLSerializer
            os_module: Модуль os (для тестирования)
        """
        self.db = db
        self.serializer = serializer
        self.xml_serializer = xml_serializer
        self.os_module = os_module or os

    # --- АВТОДЕТЕКТ И ИМПОРТ ---

    def auto_detect_and_import(self, filename: str):
        """Автоматическое определение формата и импорт"""
        try:
            # Проверка файла
            if not self.os_module.path.exists(filename):
                return False, f"Файл {filename} не найден"

            # Проверка размера файла
            file_size = self.os_module.path.getsize(filename)
            if file_size > 10 * 1024 * 1024:  # 10 MB
                return True, "large_file", file_size  # Сигнал для подтверждения

            # Определяем формат по расширению файла
            filename_lower = filename.lower()

            if filename_lower.endswith('.json'):
                return self._import_data(filename, 'json')
            elif filename_lower.endswith('.xml'):
                return self._import_data(filename, 'xml')
            elif filename_lower.endswith('.pkl') or filename_lower.endswith('.pickle'):
                return self._import_data(filename, 'pickle')
            elif filename_lower.endswith('.msgpack') or filename_lower.endswith('.mpk'):
                return self._import_data(filename, 'msgpack')
            else:
                # Попробуем определить по содержимому
                try:
                    with open(filename, 'rb') as f:
                        first_bytes = f.read(100)

                    # Грубая проверка форматов
                    if b'<?xml' in first_bytes:
                        return self._import_data(filename, 'xml')
                    elif b'{' in first_bytes or b'[' in first_bytes:
                        return self._import_data(filename, 'json')
                    elif b'\x80' in first_bytes[:2] or b'pickle' in first_bytes.lower():
                        return self._import_data(filename, 'pickle')
                    else:
                        return False, (
                            f"Не удалось определить формат файла.\n"
                            f"Поддерживаемые форматы: .json, .xml, .pkl, .msgpack"
                        )
                except Exception as inner_e:
                    return False, f"Не удалось прочитать файл: {str(inner_e)}"

        except Exception as e:
            return False, f"Ошибка импорта: {str(e)}"

    # --- ОСНОВНОЙ МЕТОД ИМПОРТА ---

    def _import_data(self, filename: str, format_type: str):
        """Универсальный импорт для всех форматов"""
        try:
            imported_counts = {
                'groups': 0,
                'students': 0,
                'lessons': 0,
                'dates': 0,
                'journal': 0
            }

            # Загружаем данные в зависимости от формата
            data = None
            if format_type == 'json':
                if not self.serializer:
                    return False, "JSON сериализатор не доступен"
                data = self.serializer.load_from_json(filename)

            elif format_type == 'xml':
                if not self.xml_serializer:
                    return False, "XML сериализатор не доступен"
                data = self.xml_serializer.load_from_xml(filename)

            elif format_type == 'pickle':
                if not self.serializer:
                    return False, "Pickle сериализатор не доступен"
                data = self.serializer.load_from_pickle(filename)

            elif format_type == 'msgpack':
                if not self.serializer:
                    return False, "MessagePack сериализатор не доступен"
                data = self.serializer.load_from_msgpack(filename)

            else:
                return False, f"Неподдерживаемый формат: {format_type}"

            if not data:
                return False, f"Не удалось загрузить данные из файла"

            # Обрабатываем данные
            self._process_import_data(data, imported_counts, format_type)

            # Формируем отчет
            report = self._generate_import_report(imported_counts)
            return True, report

        except Exception as e:
            return False, f"Ошибка при импорте {format_type.upper()}: {str(e)}"

    # --- ОБРАБОТКА ДАННЫХ ---

    def _process_import_data(self, data, imported_counts, format_type):
        """Обработка импортированных данных"""
        if format_type == 'xml':
            # Обработка XML данных
            self._process_xml_data(data, imported_counts)

        elif isinstance(data, dict):
            # Обработка словарных данных (например, из pickle)
            self._process_dict_data(data, imported_counts)

        elif isinstance(data, list):
            # Обработка списковых данных (например, из JSON)
            self._process_list_data(data, imported_counts)

    def _process_xml_data(self, data, imported_counts):
        """Обработка XML данных"""
        if 'data' not in data:
            return

        for item in data['data']:
            # Обработка групп
            if item.get('tag') == 'group' or item.get('tag') == 'Group':
                group_name = item.get('text') or item.get('name') or item.get('Name')
                if group_name and self._import_group(group_name):
                    imported_counts['groups'] += 1

            # Обработка студентов
            elif item.get('tag') == 'student' or item.get('tag') == 'Student':
                student_data = {}
                if 'children' in item:
                    for child in item['children']:
                        tag_lower = child.get('tag', '').lower()
                        student_data[tag_lower] = child.get('text', '')

                # Проверяем все необходимые поля
                required_fields = ['group', 'surname', 'name', 'patronymic']
                if all(field in student_data for field in required_fields):
                    if self.db.insert_student(
                            student_data['group'],
                            student_data['surname'],
                            student_data['name'],
                            student_data['patronymic']
                    ):
                        imported_counts['students'] += 1

    def _process_dict_data(self, data, imported_counts):
        """Обработка словарных данных (например, из pickle бэкапа)"""
        # Группы
        if 'groups' in data and isinstance(data['groups'], list):
            for item in data['groups']:
                if self._import_group_item(item):
                    imported_counts['groups'] += 1

        # Студенты
        if 'students' in data and isinstance(data['students'], list):
            for item in data['students']:
                if self._import_student_item(item):
                    imported_counts['students'] += 1

        # Занятия
        if 'lessons' in data and isinstance(data['lessons'], list):
            for item in data['lessons']:
                if self._import_lesson_item(item):
                    imported_counts['lessons'] += 1

        # Даты
        if 'dates' in data and isinstance(data['dates'], list):
            for item in data['dates']:
                if isinstance(item, str):
                    # Формат: "YYYY-MM-DD"
                    parts = item.split('-')
                    if len(parts) == 3:
                        year, month, day = parts
                        if self.db.insert_date(year, month, day):
                            imported_counts['dates'] += 1

    def _process_list_data(self, data, imported_counts):
        """Обработка списковых данных"""
        for item in data:
            # Если это строка - скорее всего группа
            if isinstance(item, str):
                if self._import_group(item):
                    imported_counts['groups'] += 1

            # Если это кортеж/список из 4 элементов - студент
            elif isinstance(item, (list, tuple)) and len(item) >= 4:
                if self.db.insert_student(item[0], item[1], item[2], item[3]):
                    imported_counts['students'] += 1

    # --- ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ---

    def _import_group(self, group_name):
        """Импорт группы"""
        if group_name and not self.db.select_where("Groups", ["group"], {"group": group_name}):
            return self.db.insert_group(group_name)
        return False

    def _import_group_item(self, item):
        """Импорт группы из любого формата"""
        if isinstance(item, str):
            group_name = item
        elif isinstance(item, (list, tuple)) and len(item) > 0:
            group_name = item[0]
        elif isinstance(item, dict):
            group_name = item.get('text') or item.get('name') or item.get('group')
        else:
            return False

        return self._import_group(group_name)

    def _import_student_item(self, item):
        """Импорт студента из любого формата"""
        if isinstance(item, (list, tuple)) and len(item) >= 4:
            return self.db.insert_student(item[0], item[1], item[2], item[3])
        elif isinstance(item, dict):
            if all(key in item for key in ['group', 'surname', 'name', 'patronymic']):
                return self.db.insert_student(
                    item['group'], item['surname'], item['name'], item['patronymic']
                )
        return False

    def _import_lesson_item(self, item):
        """Импорт занятия из любого формата"""
        if isinstance(item, str):
            lesson_name = item
        elif isinstance(item, (list, tuple)) and len(item) > 0:
            lesson_name = item[0]
        elif isinstance(item, dict):
            lesson_name = item.get('text') or item.get('name') or item.get('lesson')
        else:
            return False

        if lesson_name and not self.db.select_where("Lessons", ["lesson"], {"lesson": lesson_name}):
            return self.db.insert_lesson(lesson_name)
        return False

    def _generate_import_report(self, imported_counts):
        """Генерация отчета об импорте"""
        report_lines = ["Результаты импорта:"]

        if imported_counts['groups'] > 0:
            report_lines.append(f"• Групп: {imported_counts['groups']}")

        if imported_counts['students'] > 0:
            report_lines.append(f"• Студентов: {imported_counts['students']}")

        if imported_counts['lessons'] > 0:
            report_lines.append(f"• Занятий: {imported_counts['lessons']}")

        if imported_counts['dates'] > 0:
            report_lines.append(f"• Дат: {imported_counts['dates']}")

        if imported_counts['journal'] > 0:
            report_lines.append(f"• Записей журнала: {imported_counts['journal']}")

        # Если ничего не импортировано
        if all(count == 0 for count in imported_counts.values()):
            report_lines.append("Ничего не импортировано.\n"
                                "Возможно, формат данных не поддерживается.")

        return "\n".join(report_lines)

    # --- СПЕЦИФИЧНЫЕ МЕТОДЫ ИМПОРТА (для обратной совместимости) ---

    def import_groups_from_json(self, filename="groups_export.json"):
        """Импорт групп из JSON"""
        return self._import_data(filename, 'json')

    def import_groups_from_xml(self, filename="groups_export.xml"):
        """Импорт групп из XML"""
        return self._import_data(filename, 'xml')

    def import_backup_from_pickle(self, filename="full_backup.pkl"):
        """Импорт полного бэкапа из Pickle"""
        return self._import_data(filename, 'pickle')

    def get_supported_formats(self):
        """Возвращает список поддерживаемых форматов импорта"""
        return ['json', 'xml', 'pickle', 'msgpack']