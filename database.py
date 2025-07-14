import sqlite3
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
import traceback


class Database:
    def __init__(self, db_name="meter_bot.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    full_name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    address TEXT NOT NULL,
                    water_meters_count INTEGER NOT NULL,
                    account_number TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS counters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                alias TEXT NOT NULL,
                last_reading INTEGER DEFAULT 0,
                previous_reading INTEGER DEFAULT 0,  
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                counter_id INTEGER NOT NULL,
                value INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (counter_id) REFERENCES counters (id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        self.conn.commit()

    def add_user(self, user_id, full_name, phone_number, address, water_meters_count, account_number):
        self.cursor.execute("""
            INSERT INTO users (user_id, full_name, phone_number, address, water_meters_count, account_number)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, full_name, phone_number, address, water_meters_count, account_number))
        self.conn.commit()

    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()

    def get_counters(self, user_id):
        self.cursor.execute("SELECT * FROM counters WHERE user_id = ? ORDER BY id", (user_id,))
        return self.cursor.fetchall()

    def get_last_reading(self, counter_id):
        self.cursor.execute("SELECT value FROM readings WHERE counter_id = ? ORDER BY created_at DESC LIMIT 1",
                            (counter_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def add_reading(self, counter_id: int, value: int) -> bool:
        """
        Добавляет новые показания счетчика в базу данных
        Args:
            counter_id: ID счетчика
            value: текущие показания
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Получаем текущие показания счетчика
            self.cursor.execute("SELECT last_reading FROM counters WHERE id = ?", (counter_id,))
            last_reading_result = self.cursor.fetchone()
            last_reading = last_reading_result[0] if last_reading_result else None

            # Проверяем что новые показания больше предыдущих
            if last_reading is not None and value <= last_reading:
                raise ValueError(f"Новые показания ({value}) должны быть больше предыдущих ({last_reading})")

            # Начинаем транзакцию
            self.cursor.execute("BEGIN TRANSACTION")

            # Добавляем запись в таблицу показаний
            self.cursor.execute(
                "INSERT INTO readings (counter_id, value, created_at) VALUES (?, ?, ?)",
                (counter_id, value, current_datetime)
            )

            # Обновляем показания в таблице counters:
            if last_reading is None:
                # Первое показание - только обновляем last_reading
                self.cursor.execute(
                    "UPDATE counters SET last_reading = ? WHERE id = ?",
                    (value, counter_id)
                )
            else:
                # Последующие показания - перемещаем last_reading в previous_reading
                self.cursor.execute(
                    "UPDATE counters SET previous_reading = last_reading, last_reading = ? WHERE id = ?",
                    (value, counter_id)
                )

            # Фиксируем изменения
            self.conn.commit()

            print(f"[SUCCESS] Добавлены показания: счетчик {counter_id}, значение {value}, дата {current_datetime}")
            return True

        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"[ERROR] Ошибка SQLite при добавлении показаний: {e}")
            return False
        except ValueError as e:
            self.conn.rollback()
            print(f"[ERROR] Ошибка валидации: {e}")
            return False
        except Exception as e:
            self.conn.rollback()
            print(f"[ERROR] Неожиданная ошибка: {e}")
            return False

    def get_all_users(self):
        self.cursor.execute("SELECT * FROM users")
        return self.cursor.fetchall()

    def add_counter(self, user_id, alias):
        self.cursor.execute("INSERT INTO counters (user_id, alias) VALUES (?, ?)", (user_id, alias))
        self.conn.commit()

    def _convert_date_format(self, date_str: str) -> str:
        """
        Конвертирует дату из формата ДД.ММ.ГГГГ в ISO формат YYYY-MM-DD
        Args:
            date_str: дата в формате ДД.ММ.ГГГГ или YYYY-MM-DD
        Returns:
            дата в формате YYYY-MM-DD
        """
        if not date_str:
            return date_str

        # Убираем время если есть
        date_only = date_str.split(' ')[0]

        try:
            # Парсим дату из формата ДД.ММ.ГГГГ
            parsed_date = datetime.strptime(date_only, "%d.%m.%Y")
            # Возвращаем в формате YYYY-MM-DD
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            # Если дата уже в ISO формате, возвращаем как есть
            try:
                datetime.strptime(date_only, "%Y-%m-%d")
                return date_only
            except ValueError:
                raise ValueError(f"Неверный формат даты: {date_only}. Ожидается ДД.ММ.ГГГГ или YYYY-MM-DD")

    def get_readings_report(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Получает отчет по показаниям за указанный период
        Args:
            start_date: Начальная дата в формате ДД.ММ.ГГГГ или YYYY-MM-DD (опционально)
            end_date: Конечная дата в формате ДД.ММ.ГГГГ или YYYY-MM-DD (опционально)
        Returns:
            Список словарей с данными по пользователям и их счетчикам
        """
        try:
            # Конвертируем даты в ISO формат
            if start_date:
                start_iso = self._convert_date_format(start_date)
            else:
                start_iso = "1970-01-01"

            if end_date:
                end_iso = self._convert_date_format(end_date) + " 23:59:59"
            else:
                end_iso = "2100-12-31 23:59:59"

            # Отладочная информация
            print(f"Исходные даты: {start_date} - {end_date}")
            print(f"Преобразованные даты: {start_iso} - {end_iso}")

            # Запрос для получения последнего и предпоследнего показаний
            query = """
            WITH RankedReadings AS (
                SELECT 
                    r.counter_id,
                    r.value,
                    r.created_at,
                    ROW_NUMBER() OVER (PARTITION BY r.counter_id ORDER BY r.created_at DESC) AS rn,
                    LAG(r.value) OVER (PARTITION BY r.counter_id ORDER BY r.created_at) AS prev_value,
                    LAG(r.created_at) OVER (PARTITION BY r.counter_id ORDER BY r.created_at) AS prev_date
                FROM readings r
                WHERE r.created_at BETWEEN ? AND ?
            )
            SELECT 
                u.user_id,
                u.account_number,
                u.full_name,
                u.phone_number,
                u.address,
                u.water_meters_count,
                c.id AS counter_id,
                c.alias,
                rr.value AS current_reading,
                rr.created_at AS current_date,
                rr.prev_value,
                rr.prev_date
            FROM users u
            INNER JOIN counters c ON c.user_id = u.user_id
            INNER JOIN RankedReadings rr ON c.id = rr.counter_id
            WHERE rr.rn = 1
            ORDER BY u.account_number, c.alias
            """

            # Выполнение запроса
            self.cursor.execute(query, (start_iso, end_iso))
            rows = self.cursor.fetchall()
            print(f"Количество найденных строк после выполнения запроса: {len(rows)}")

            # Для отладки выведем первую строку результата
            if rows:
                print(f"Первая строка результата: {rows[0]}")

            # Структура для хранения результатов
            result = []

            # Словарь для группировки по пользователям
            users_dict = {}

            # Обработка результатов
            for row in rows:
                user_id, account_number, full_name, phone_number, address, water_meters_count, counter_id, alias, current_reading, current_date, prev_value, prev_date = row

                # Если пользователя еще нет в словаре, добавляем его
                if user_id not in users_dict:
                    users_dict[user_id] = {
                        "user_id": user_id,
                        "account_number": account_number,
                        "full_name": full_name,
                        "phone_number": phone_number,
                        "address": address,
                        "water_meters_count": water_meters_count,
                        "counters": []
                    }

                # Добавляем данные счетчика
                users_dict[user_id]["counters"].append({
                    "alias": alias,
                    "readings": [{
                        "value": current_reading,
                        "date": current_date,
                        "prev_value": prev_value,
                        "prev_date": prev_date
                    }]
                })

            # Преобразуем словарь в список
            for user_id, user_data in users_dict.items():
                result.append(user_data)

            print(f"Результат успешно сформирован, количество пользователей: {len(result)}")
            return result

        except Exception as e:
            print(f"Ошибка при получении отчета: {e}")
            traceback.print_exc()
            return []

    def format_report_for_message(self, report_data: List[Dict[str, Any]]) -> str:
        """
        Форматирует отчет для вывода в сообщении
        Args:
            report_data: данные отчета
        Returns:
            Отформатированная строка отчета
        """
        try:
            if not report_data:
                return "Нет данных для формирования отчета"

            result = []

            for user in report_data:
                user_info = (
                    f"👤 *Пользователь*: {user['full_name']}\n"
                    f"📱 *Телефон*: {user['phone_number']}\n"
                    f"🏠 *Адрес*: {user['address']}\n"
                    f"🆔 *Лицевой счет*: {user['account_number']}\n"
                    f"🚰 *Количество счетчиков*: {user['water_meters_count']}\n"
                )

                counters_info = []

                for counter in user['counters']:
                    counter_info = [f"📊 *Счетчик*: {counter['alias']}"]

                    if counter['readings']:
                        readings_info = []

                        for reading in counter['readings']:
                            reading_date = reading['date']
                            if isinstance(reading_date, str):
                                try:
                                    date_obj = datetime.fromisoformat(reading_date.replace('Z', '+00:00'))
                                    formatted_date = date_obj.strftime('%d.%m.%Y %H:%M')
                                except ValueError:
                                    formatted_date = reading_date
                            else:
                                formatted_date = reading_date.strftime('%d.%m.%Y %H:%M')

                            reading_str = f"📅 *Дата*: {formatted_date}\n📉 *Показания*: {reading['value']}"

                            if reading['prev_value'] is not None:
                                prev_date = reading['prev_date']
                                if isinstance(prev_date, str):
                                    try:
                                        prev_date_obj = datetime.fromisoformat(prev_date.replace('Z', '+00:00'))
                                        formatted_prev_date = prev_date_obj.strftime('%d.%m.%Y %H:%M')
                                    except ValueError:
                                        formatted_prev_date = prev_date
                                else:
                                    formatted_prev_date = prev_date.strftime('%d.%m.%Y %H:%M')

                                reading_str += (
                                    f"\n📅 *Предыдущая дата*: {formatted_prev_date}\n"
                                    f"📉 *Предыдущие показания*: {reading['prev_value']}\n"
                                    f"🔄 *Разница*: {reading['diff'] if reading.get('diff') else reading['value'] - reading['prev_value']}"
                                )

                            readings_info.append(reading_str)

                        counter_info.extend(readings_info)
                    else:
                        counter_info.append("❌ *Нет показаний*")

                    counters_info.append("\n".join(counter_info))

                user_section = user_info + "\n\n" + "\n\n".join(counters_info)
                result.append(user_section)

            return "\n\n" + "\n\n---\n\n".join(result)

        except Exception as e:
            print(f"Ошибка при генерации отчета: {e}")
            traceback.print_exc()
            return "Ошибка при форматировании отчета"

    def check_data(self):
        """Вспомогательный метод для проверки данных"""
        print("\nПроверка данных в таблицах:")

        print("\nUsers:")
        self.cursor.execute("SELECT user_id, account_number, full_name FROM users")
        users = self.cursor.fetchall()
        for user in users:
            print(f"user_id: {user[0]}, account: {user[1]}, name: {user[2]}")

        print("\nCounters:")
        self.cursor.execute("SELECT id, user_id, alias FROM counters")
        counters = self.cursor.fetchall()
        for counter in counters:
            print(f"id: {counter[0]}, user_id: {counter[1]}, alias: {counter[2]}")

        print("\nReadings:")
        self.cursor.execute("SELECT counter_id, value, created_at FROM readings ORDER BY created_at DESC LIMIT 5")
        readings = self.cursor.fetchall()
        for reading in readings:
            print(f"counter_id: {reading[0]}, value: {reading[1]}, created_at: {reading[2]}")

    def export_to_excel(self, data):
        try:
            if not isinstance(data, list):
                raise ValueError("Data must be a list of dictionaries")

            # Создаем базовые колонки
            columns = [
                'Особовий рахунок',
                'ПІБ',
                'Адреса',
                'Телефон'
            ]

            # Определяем максимальное количество счетчиков
            max_counters = max(user.get('water_meters_count', 0) for user in data)

            # Добавляем колонки для каждого счетчика
            for i in range(1, max_counters + 1):
                columns.extend([
                    f'Лічильник-{i} поточні',
                    f'Лічильник-{i} дата',
                    f'Лічильник-{i} попередні',
                    f'Лічильник-{i} дата попередніх'
                ])

            # Подготовка данных для Excel
            excel_data = []
            for user in data:
                row = {
                    'Особовий рахунок': user['account_number'],
                    'ПІБ': user['full_name'],
                    'Адреса': user['address'],
                    'Телефон': user['phone_number']
                }

                # Получаем список счетчиков пользователя
                user_counters = {c['alias']: c for c in user['counters']}

                # Добавляем данные счетчиков
                for i in range(max_counters):
                    counter_num = i + 1
                    counter_alias = f'Лічильник-{counter_num}'
                    counter = user_counters.get(counter_alias)

                    if counter and counter['readings'] and len(counter['readings']) > 0:
                        reading = counter['readings'][0]
                        row.update({
                            f'Лічильник-{counter_num} поточні': reading['value'],
                            f'Лічильник-{counter_num} дата': reading['date'],
                            f'Лічильник-{counter_num} попередні': reading['prev_value'],
                            f'Лічильник-{counter_num} дата попередніх': reading['prev_date']
                        })
                    else:
                        row.update({
                            f'Лічильник-{counter_num} поточні': None,
                            f'Лічильник-{counter_num} дата': None,
                            f'Лічильник-{counter_num} попередні': None,
                            f'Лічильник-{counter_num} дата попередніх': None
                        })

                excel_data.append(row)

            # Создаем DataFrame
            df = pd.DataFrame(excel_data, columns=columns)

            # Генерация имени файла
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'readings_report_{current_time}.xlsx'

            # Сохранение в Excel
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Report', index=False)

                # Форматирование Excel файла
                worksheet = writer.sheets['Report']

                # Настройка ширины колонок
                for col in worksheet.columns:
                    max_length = 0
                    column = col[0].column_letter
                    for cell in col:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = (max_length + 2) * 1.2
                    worksheet.column_dimensions[column].width = adjusted_width

            return filename

        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            raise

    def get_user_statistics(self):
        # Статистика по користувачах
        query = """
        SELECT 
            COUNT(*) as total_users,
            COUNT(DISTINCT id) as active_users,
            AVG(water_meters_count) as avg_meters
        FROM users
        """
        return pd.read_sql_query(query, self.conn)

    def add_monthly_reading(self, counter_id: int, current_reading: int, month_year: str = None) -> None:
        """Добавляет месячные показания счетчика"""
        if month_year is None:
            month_year = datetime.now().strftime("%m-%Y")

        # Получаем предыдущие показания за прошлый месяц
        prev_reading = self.get_previous_month_reading(counter_id)

        self.cursor.execute("""
            INSERT INTO monthly_readings 
            (counter_id, current_month_reading, previous_month_reading, month_year)
            VALUES (?, ?, ?, ?)
        """, (counter_id, current_reading, prev_reading, month_year))

        # Обновляем last_reading в таблице counters
        self.cursor.execute("""
            UPDATE counters SET last_reading = ? WHERE id = ?
        """, (current_reading, counter_id))

        self.conn.commit()

    def get_previous_month_reading(self, counter_id: int) -> int:
        """Получает предыдущие показания за прошлый месяц"""
        self.cursor.execute("""
            SELECT current_month_reading FROM monthly_readings 
            WHERE counter_id = ?
            ORDER BY reading_date DESC 
            LIMIT 1
        """, (counter_id))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_monthly_readings(self, counter_id: int) -> List[Dict]:
        """Получает все месячные показания для счетчика"""
        self.cursor.execute("""
            SELECT * FROM monthly_readings 
            WHERE counter_id = ?
            ORDER BY reading_date DESC
        """, (counter_id))
        columns = [col[0] for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def has_current_month_reading(self, counter_id: int) -> bool:
        """Проверяет, есть ли показания за текущий месяц"""
        current_month = datetime.now().strftime("%m-%Y")
        self.cursor.execute("""
            SELECT 1 FROM monthly_readings 
            WHERE counter_id = ? AND month_year = ?
            LIMIT 1
        """, (counter_id, current_month))
        return self.cursor.fetchone() is not None

    def close(self):
        self.conn.close()