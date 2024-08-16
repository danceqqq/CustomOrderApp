import customtkinter as ctk
from tkinter import Listbox, Text, END
from PIL import Image, ImageTk
import sqlite3
import os
import webbrowser
import requests

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Заказы")
        self.geometry("1000x800")
        self.conn = sqlite3.connect('orders.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                theme TEXT,
                description TEXT,
                order_number INTEGER,
                status TEXT DEFAULT 'New',
                image TEXT
            )
        ''')
        self.conn.commit()

        # Toolbar frame
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(side=ctk.TOP, fill=ctk.X)

        # Search entry for order numbers
        self.search_entry = ctk.CTkEntry(toolbar, width=200, placeholder_text="Поиск 🔎")
        self.search_entry.pack(side=ctk.LEFT, padx=5, pady=5)
        self.search_entry.bind('<FocusIn>', self.on_search_focus_in)
        self.search_entry.bind('<FocusOut>', self.on_search_focus_out)
        self.search_entry.bind('<KeyRelease>', self.on_search_key_release)

        # Buttons in the toolbar
        self.update_button = ctk.CTkButton(toolbar, text="Обновить 🔄", command=self.update_orders)
        self.update_button.pack(side=ctk.LEFT, padx=5, pady=5)
        self.accept_button = ctk.CTkButton(toolbar, text="Принять ✅", command=self.accept_order)
        self.accept_button.pack(side=ctk.LEFT, padx=5, pady=5)
        self.cancel_button = ctk.CTkButton(toolbar, text="Отклонить ❌", command=self.cancel_order)
        self.cancel_button.pack(side=ctk.LEFT, padx=5, pady=5)
        self.delete_button = ctk.CTkButton(toolbar, text="Удалить 🗑", command=self.delete_order)
        self.delete_button.pack(side=ctk.LEFT, padx=5, pady=5)
        self.settings_button = ctk.CTkButton(toolbar, text="Настройки ⚙️", command=self.open_settings_window)
        self.settings_button.pack(side=ctk.RIGHT, padx=5, pady=5)

        # Main content
        self.order_list = Listbox(self, width=50, height=20)
        self.order_list.pack(side=ctk.LEFT, fill=ctk.Y)

        self.order_frame = ctk.CTkFrame(self)
        self.order_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

        # Avatar and dialog button frame
        self.avatar_frame = ctk.CTkFrame(self.order_frame)
        self.avatar_frame.pack(side=ctk.LEFT, anchor="n", padx=10, pady=10)

        # Label for Telegram avatar
        self.avatar_label = ctk.CTkLabel(self.avatar_frame, text="")
        self.avatar_label.pack(side=ctk.TOP)

        # Button for opening Telegram dialog (initially hidden)
        self.open_dialog_button = ctk.CTkButton(self.avatar_frame, text="Открыть диалог 📨", command=self.open_telegram_dialog)
        self.open_dialog_button.pack(side=ctk.TOP, pady=10)

        self.order_info = ctk.CTkTextbox(self.order_frame, width=500, height=300)
        self.order_info.pack(side=ctk.LEFT, fill=ctk.BOTH)

        # Image label for order image
        self.image_label = ctk.CTkLabel(self, text="")
        self.image_label.pack(side=ctk.RIGHT, anchor="n", padx=10, pady=10)

        self.update_orders()
        self.order_list.bind("<<ListboxSelect>>", lambda event: self.show_order_info())

        self.current_user_name = None

    def on_search_focus_in(self, event):
        if self.search_entry.get() == 'Поиск 🔎':
            self.search_entry.delete(0, ctk.END)
            self.search_entry.config(fg='black')

    def on_search_focus_out(self, event):
        if self.search_entry.get() == '':
            self.search_entry.insert(0, 'Поиск 🔎')
            self.search_entry.config(fg='gray')

    def on_search_key_release(self, event):
        search_text = self.search_entry.get().strip()
        self.update_orders(search_text)

    def update_orders(self, search_text=''):
        self.order_list.delete(0, ctk.END)
        query = 'SELECT * FROM orders'
        params = ()
        if search_text and search_text != 'Поиск 🔎':
            query += ' WHERE order_number LIKE ?'
            params = (f'%{search_text}%',)
        self.cursor.execute(query, params)
        orders = self.cursor.fetchall()
        for order in orders:
            display_text = f"{order[4]} - {order[2]}"
            self.order_list.insert(ctk.END, display_text)

    def accept_order(self):
        selected_order = self.order_list.curselection()
        if selected_order:
            order_number = self.order_list.get(selected_order)
            order_number = order_number.split(' - ')[0]
            self.cursor.execute('UPDATE orders SET status = "Working" WHERE order_number =?', (order_number,))
            self.conn.commit()
            self.update_orders()

    def cancel_order(self):
        selected_order = self.order_list.curselection()
        if selected_order:
            order_number = self.order_list.get(selected_order)
            order_number = order_number.split(' - ')[0]
            self.cursor.execute('UPDATE orders SET status = "Cancel" WHERE order_number =?', (order_number,))
            self.conn.commit()
            self.update_orders()

    def delete_order(self):
        selected_order = self.order_list.curselection()
        if selected_order:
            order_number = self.order_list.get(selected_order)
            order_number = order_number.split(' - ')[0]
            self.cursor.execute('UPDATE orders SET status = "Deleted" WHERE order_number =?', (order_number,))
            self.conn.commit()
            self.update_orders()

    def show_order_info(self):
        selected_order = self.order_list.curselection()
        if selected_order:
            order_number = self.order_list.get(selected_order)
            order_number = order_number.split(' - ')[0]
            self.cursor.execute('SELECT * FROM orders WHERE order_number =?', (order_number,))
            order = self.cursor.fetchone()
            self.order_info.delete(1.0, ctk.END)
            self.order_info.insert(ctk.END,
                                   f"Номер заказа: {order[4]}\n\nТема: {order[2]}\n\nОписание: {order[3]}\n\nПользователь: {order[1]}\n\nСтатус: {order[5]}")

            self.current_user_name = order[1]

            # Check and display image if it exists
            user_folder = os.path.join('orders', order[1])
            image_path = os.path.join(user_folder, order[6]) if order[6] else None

            if image_path and os.path.exists(image_path):
                image = Image.open(image_path)
                image = self.resize_image(image, 300, 400)
                photo = ImageTk.PhotoImage(image)
                self.image_label.configure(image=photo)
                self.image_label.image = photo
                self.order_info.insert(ctk.END, f"\n\n[Изображение прикреплено]\n")
            else:
                self.image_label.configure(image=None)
                self.image_label.image = None
                self.order_info.insert(ctk.END, f"\n\n[Изображение отсутствует]\n")

            self.load_and_display_avatar()
            self.open_dialog_button.pack(side=ctk.TOP, pady=10)

    def resize_image(self, image, max_width, max_height):
        width, height = image.size
        ratio = min(max_width / width, max_height / height)
        new_size = (int(width * ratio), int(height * ratio))
        return image.resize(new_size, Image.Resampling.LANCZOS)

    def load_and_display_avatar(self):
        avatar_url = f"https://t.me/i/userpic/320/{self.current_user_name}.jpg"
        try:
            response = requests.get(avatar_url, stream=True)
            if response.status_code == 200:
                avatar_image = Image.open(response.raw)
                avatar_image = self.resize_image(avatar_image, 100, 100)
                avatar_photo = ImageTk.PhotoImage(avatar_image)
                self.avatar_label.configure(image=avatar_photo, text="")
                self.avatar_label.image = avatar_photo
            else:
                self.avatar_label.configure(image=None, text="Аватар отсутствует")
                self.avatar_label.image = None
        except requests.RequestException as e:
            self.avatar_label.configure(image=None, text="Ошибка загрузки аватара")
            self.avatar_label.image = None
            print(f"Ошибка загрузки аватара: {e}")

    def open_telegram_dialog(self):
        if self.current_user_name:
            telegram_url = f"https://t.me/{self.current_user_name}"
            webbrowser.open(telegram_url)
        else:
            print("Пользователь не выбран.")

    def open_settings_window(self):
        # Создаем новое окно настроек
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Настройки")
        settings_window.geometry("300x200")

        # Переключатель для смены темы
        self.theme_switch = ctk.CTkSwitch(settings_window, text="Светлая тема", command=self.toggle_theme)
        self.theme_switch.pack(pady=20)

        # Устанавливаем переключатель в соответствии с текущей темой
        if ctk.get_appearance_mode() == "Light":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()

        close_button = ctk.CTkButton(settings_window, text="Закрыть", command=settings_window.destroy)
        close_button.pack(pady=20)

    def toggle_theme(self):
        # Смена темы между светлой и тёмной
        if self.theme_switch.get():
            ctk.set_appearance_mode("Light")
        else:
            ctk.set_appearance_mode("Dark")

if __name__ == "__main__":
    app = App()
    app.mainloop()
