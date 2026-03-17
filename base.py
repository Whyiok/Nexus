import sqlite3

class SQL:
    def __init__(self, database):
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.cursor = self.connection.cursor()

    # Добавление пользователя в БД
    def add_user(self, username, email, password):
        query = "INSERT INTO users (username, email, password) VALUES(?, ?, ?)"
        with self.connection:
            self.cursor.execute(query, (username, email, password))
            self.connection.commit()

    # Проверка, есть ли пользователь в БД
    def user_exist(self, email):
        query = "SELECT * FROM users WHERE email = ?"
        with self.connection:
            result = self.cursor.execute(query, (email,)).fetchall()
            return bool(len(result))

    """    def get_all_users(self):
            query = "SELECT username FROM users"
            with self.connection:
                result = self.cursor.execute(query).fetchone()
                if result:
                    return result[0]
                else:
                    return None"""

    def get_all_users(self):
        query = "SELECT username, id FROM users"
        with self.connection:
            result = self.cursor.execute(query).fetchall()
            return result

    def get_user_by_email(self, email):
        query = "SELECT * FROM users WHERE email = ?"
        with self.connection:
            result = self.cursor.execute(query, (email,)).fetchone()
            return result

    # Универсальные методы
    def get_field(self, table, email, field):
        query = f"SELECT {field} FROM {table} WHERE email = ?"
        with self.connection:
            result = self.cursor.execute(query, (email,)).fetchone()
            if result:
                return result[0]
            else:
                return None

    def update_field(self, table, email, field, value):
        # Создаем НОВОЕ соединение для этого вызова
        temp_connection = sqlite3.connect('db.db')
        temp_cursor = temp_connection.cursor()

        query = f"UPDATE {table} SET {field} = ? WHERE email = ?"
        try:
            temp_cursor.execute(query, (value,))
            temp_connection.commit()
        except Exception as e:
            print(f"Ошибка при обновлении: {e}")
        finally:
            # Всегда закрываем временное соединение
            temp_connection.close()
    
    # Закрытие соединения
    def close(self):
        self.connection.close()