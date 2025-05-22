# main.py

from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
import socket
import threading
import json
import os

Window.size = (360, 640)

KV = '''
ScreenManager:
    LoginScreen:
    ChatScreen:

<LoginScreen>:
    name: 'login'
    MDBoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 20

        MDLabel:
            text: "ChatFast Login"
            halign: "center"
            font_style: "H4"

        MDTextField:
            id: username_input
            hint_text: "Enter your username"
            required: True

        MDRaisedButton:
            text: "Login"
            pos_hint: {"center_x": 0.5}
            on_release: root.login()

<ChatScreen>:
    name: 'chat'
    MDBoxLayout:
        orientation: 'vertical'

        ScrollView:
            MDList:
                id: chat_log

        MDTextField:
            id: message_input
            hint_text: "Type a message"
            multiline: False
            on_text_validate: root.send_message()

        MDRaisedButton:
            text: "Send"
            pos_hint: {"center_x": 0.5}
            on_release: root.send_message()
'''

class LoginScreen(Screen):
    def login(self):
        app = MDApp.get_running_app()
        app.username = self.ids.username_input.text.strip()
        if not app.username:
            app.show_dialog("Username required")
            return
        try:
            app.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            app.socket.connect(('127.0.0.1', 12345))  # Change to your server IP
            login_data = {'type': 'login', 'username': app.username}
            app.socket.send(json.dumps(login_data).encode('utf-8'))

            response = json.loads(app.socket.recv(1024).decode('utf-8'))
            if response.get('status') == 'success':
                app.screen_manager.current = 'chat'
                threading.Thread(target=app.receive_messages, daemon=True).start()
            else:
                app.show_dialog("Login failed")
        except Exception as e:
            app.show_dialog(f"Connection error: {e}")

class ChatScreen(Screen):
    def send_message(self):
        app = MDApp.get_running_app()
        text = self.ids.message_input.text.strip()
        if text:
            msg = {'type': 'message', 'sender': app.username, 'text': text}
            try:
                app.socket.send(json.dumps(msg).encode('utf-8'))
                self.ids.message_input.text = ''
            except Exception as e:
                app.show_dialog(f"Send failed: {e}")

    def display_message(self, message):
        from kivymd.uix.label import MDLabel
        self.ids.chat_log.add_widget(
            MDLabel(text=message, halign="left", theme_text_color="Primary")
        )

class ChatFastApp(MDApp):
    def build(self):
        self.username = ''
        self.socket = None
        self.screen_manager = Builder.load_string(KV)
        return self.screen_manager

    def show_dialog(self, text):
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.dismiss()
        self.dialog = MDDialog(text=text)
        self.dialog.open()

    def receive_messages(self):
        while True:
            try:
                message = self.socket.recv(1024).decode('utf-8')
                if message:
                    Clock.schedule_once(lambda dt: self.screen_manager.get_screen('chat').display_message(message))
            except:
                break

if __name__ == '__main__':
    ChatFastApp().run()
