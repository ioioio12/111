import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QListWidget, QLineEdit, QMessageBox, QLabel, QDialog, QFormLayout
)

SERVER_URL = "http://127.0.0.1:5000"

class CredentialDialog(QDialog):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle(f"Изменить логин/пароль (ID {user_id})")

        layout = QFormLayout()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_credentials)

        layout.addRow("Новый логин:", self.username_input)
        layout.addRow("Новый пароль:", self.password_input)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def save_credentials(self):
        new_username = self.username_input.text().strip()
        new_password = self.password_input.text().strip()

        if not new_username or not new_password:
            QMessageBox.warning(self, "Ошибка", "Логин и пароль не могут быть пустыми")
            return

        try:
            response = requests.put(
                f"{SERVER_URL}/users/{self.user_id}",
                json={"username": new_username, "password": new_password}
            )
            if response.status_code == 200:
                QMessageBox.information(self, "Успех", "Учётные данные обновлены!")
                self.accept()
            else:
                QMessageBox.critical(self, "Ошибка", f"{response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения:\n{e}")


class ClientApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Клиент пользователей")
        self.setGeometry(100, 100, 350, 450)

        layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.load_users_button = QPushButton("Загрузить пользователей")

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.add_user_button = QPushButton("Зарегистрировать пользователя")
        self.delete_user_button = QPushButton("Удалить пользователя")
        self.change_credentials_button = QPushButton("Изменить логин/пароль")

        layout.addWidget(self.list_widget)
        layout.addWidget(self.load_users_button)
        layout.addWidget(QLabel("Добавить нового пользователя:"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.add_user_button)
        layout.addWidget(self.delete_user_button)
        layout.addWidget(self.change_credentials_button)

        self.setLayout(layout)

        self.load_users_button.clicked.connect(self.load_users)
        self.add_user_button.clicked.connect(self.register_user)
        self.delete_user_button.clicked.connect(self.delete_user)
        self.change_credentials_button.clicked.connect(self.change_credentials)
        self.list_widget.itemClicked.connect(self.clear_inputs)

    def load_users(self):
        try:
            response = requests.get(f"{SERVER_URL}/users")
            if response.status_code == 200:
                self.list_widget.clear()
                users = response.json()
                for user in users:
                    self.list_widget.addItem(f"{user['id']}: {user.get('username', '???')}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось загрузить пользователей")
        except requests.exceptions.RequestException:
            QMessageBox.critical(self, "Ошибка", "Сервер недоступен")

    def register_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if username and password:
            try:
                response = requests.post(f"{SERVER_URL}/register", json={
                    "username": username,
                    "password": password
                })
                if response.status_code == 201:
                    QMessageBox.information(self, "Успех", "Пользователь зарегистрирован!")
                    self.username_input.clear()
                    self.password_input.clear()
                    self.load_users()
                else:
                    QMessageBox.critical(self, "Ошибка", f"{response.status_code}: {response.text}")
            except requests.exceptions.RequestException as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка соединения:\n{e}")
        else:
            QMessageBox.warning(self, "Недостаточно данных", "Введите username и пароль")

    def get_selected_user_id(self):
        selected = self.list_widget.currentItem()
        if selected:
            return int(selected.text().split(":")[0])
        return None

    def clear_inputs(self):
        self.username_input.clear()
        self.password_input.clear()

    def delete_user(self):
        user_id = self.get_selected_user_id()
        if user_id is not None:
            confirm = QMessageBox.question(self, "Удаление",
                                           f"Удалить пользователя с ID {user_id}?",
                                           QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                try:
                    response = requests.delete(f"{SERVER_URL}/users/{user_id}")
                    if response.status_code == 200:
                        QMessageBox.information(self, "Успех", "Пользователь удалён")
                        self.load_users()
                    else:
                        QMessageBox.critical(self, "Ошибка", f"{response.status_code}: {response.text}")
                except requests.exceptions.RequestException as e:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка соединения:\n{e}")

    def change_credentials(self):
        user_id = self.get_selected_user_id()
        if user_id is not None:
            dialog = CredentialDialog(user_id)
            dialog.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = ClientApp()
    client.show()
    sys.exit(app.exec())
