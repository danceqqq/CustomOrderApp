import tkinter as tk
from PIL import Image, ImageTk
import sqlite3
import os


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Заказы")
        self.geometry("800x600")
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
        toolbar = tk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Buttons in the toolbar
        self.update_button = tk.Button(toolbar, text="Обновить 🔄", command=self.update_orders)
        self.update_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.accept_button = tk.Button(toolbar, text="Принять ✅", command=self.accept_order)
        self.accept_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.cancel_button = tk.Button(toolbar, text="Отклонить ❌", command=self.cancel_order)
        self.cancel_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.delete_button = tk.Button(toolbar, text="Удалить 🗑", command=self.delete_order)
        self.delete_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.settings_button = tk.Button(toolbar, text="Настройки ⚙️", command=self.open_settings_window)
        self.settings_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # Main content
        self.order_list = tk.Listbox(self, width=30)
        self.order_list.pack(side=tk.LEFT, fill=tk.Y)
        self.order_info = tk.Text(self, width=50, height=20)
        self.order_info.pack(side=tk.TOP, fill=tk.BOTH)

        # Image label
        self.image_label = tk.Label(self)
        self.image_label.pack(side=tk.RIGHT, anchor="n", padx=10, pady=10)

        self.update_orders()
        self.order_list.bind("<<ListboxSelect>>", lambda event: self.show_order_info())

    def update_orders(self):
        self.order_list.delete(0, tk.END)
        self.cursor.execute('SELECT * FROM orders')
        orders = self.cursor.fetchall()
        for order in orders:
            display_text = f"{order[4]} - {order[2]}"
            self.order_list.insert(tk.END, display_text)

            # Set color based on status
            status = order[5]
            if status == "New":
                self.order_list.itemconfig(tk.END, {'fg': 'blue'})
            elif status == "Cancel":
                self.order_list.itemconfig(tk.END, {'fg': 'red'})
            elif status == "Working":
                self.order_list.itemconfig(tk.END, {'fg': 'green'})
            elif status == "Deleted":
                self.order_list.itemconfig(tk.END, {'fg': 'gray'})

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
            self.order_info.delete(1.0, tk.END)
            self.order_info.insert(tk.END,
                                   f"Номер заказа: {order[4]}\n\nТема: {order[2]}\n\nОписание: {order[3]}\n\nПользователь: {order[1]}\n\nСтатус: {order[5]}")

            # Проверка и отображение изображения, если оно существует
            user_folder = os.path.join('orders', order[1])
            image_path = os.path.join(user_folder, order[6]) if order[6] else None

            if image_path and os.path.exists(image_path):
                image = Image.open(image_path)
                image = self.resize_image(image, 300, 400)  # Устанавливаем размеры для масштабирования
                photo = ImageTk.PhotoImage(image)
                self.image_label.configure(image=photo)
                self.image_label.image = photo  # Нужно сохранить ссылку на изображение, чтобы оно не было уничтожено
                self.order_info.insert(tk.END, f"\n\n[Изображение прикреплено]\n")
            else:
                self.image_label.configure(image=None)
                self.image_label.image = None
                self.order_info.insert(tk.END, f"\n\n[Изображение отсутствует]\n")

    def resize_image(self, image, max_width, max_height):
        """ Масштабирует изображение до заданных размеров, сохраняя пропорции """
        width, height = image.size
        ratio = min(max_width / width, max_height / height)
        new_size = (int(width * ratio), int(height * ratio))
        return image.resize(new_size, Image.Resampling.LANCZOS)

    def open_settings_window(self):
        settings_window = tk.Toplevel(self)
        settings_window.title("Настройки")
        settings_window.geometry("400x200")

        # Toolbar in the settings window
        settings_toolbar = tk.Frame(settings_window)
        settings_toolbar.pack(side=tk.TOP, fill=tk.X)
        back_button = tk.Button(settings_toolbar, text="Вернуться ↩️", command=settings_window.destroy)
        back_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Theme switcher
        self.theme_var = tk.StringVar(value="light")
        theme_switcher = tk.Checkbutton(settings_window, text="Тёмная тема", variable=self.theme_var, onvalue="dark",
                                        offvalue="light", command=self.switch_theme)
        theme_switcher.pack(pady=20)

    def switch_theme(self):
        if self.theme_var.get() == "dark":
            self.configure(bg="#343434")
            self.order_list.configure(bg="#343434", fg="white")
            self.order_info.configure(bg="#343434", fg="white")
        else:
            self.configure(bg="white")
            self.order_list.configure(bg="white", fg="black")
            self.order_info.configure(bg="white", fg="black")


if __name__ == "__main__":
    app = App()
    app.mainloop()
