# src/nexus_chat/app.py
import toga
from .ui import ChatInterface

def main():
    return toga.App(
        formal_name='Nexus AI',
        app_id='com.example.nexus_chat',
        startup=lambda app: ChatInterface().startup(app)
    )