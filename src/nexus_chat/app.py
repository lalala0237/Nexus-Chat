import toga
from nexus_chat.ui import ChatInterface

def main():
    # 1. 创建你的主界面类实例
    chat_interface = ChatInterface()

    # 2. 创建 Toga 应用，并把 startup 任务交给 chat_interface
    return toga.App(
        formal_name='Nexus Chat',  # 应用的正式名称
        app_id='com.example.nexuschat',  # 应用的唯一标识符，建议改成你自己的
        startup=chat_interface.startup  # 关键：把启动任务交给 ChatInterface 的 startup 方法
    )