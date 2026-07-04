import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, LEFT, RIGHT, CENTER
import toga.platform

class NexusChatUI:
    def __init__(self, app):
        self.app = app
        
        # --- 核心改动：自动检测是否为 Android ---
        self.is_android = toga.platform.current_platform == 'android'
        
        # 初始化主容器
        self.main_box = toga.Box(
            style=Pack(
                direction=COLUMN, 
                padding=10 if not self.is_android else 5,  # Android 边距更小
                background_color="#f0f0f0"
            )
        )

        # 1. 聊天显示区域
        self.chat_output = toga.MultilineTextInput(
            readonly=True,
            placeholder="这里将显示聊天记录...",
            style=Pack(
                flex=1,     # 占据剩余所有空间
                margin_bottom=10,
                padding=10,
                font_size=16 if self.is_android else 14, # Android 字体稍大
                background_color="#ffffff"
            )
        )

        # 2. 输入框区域
        self.input_field = toga.TextInput(
            placeholder="Type your message...",
            on_confirm=self.send_message, # 绑定回车发送
            style=Pack(
                flex=1,     # 输入框横向撑满
                margin_right=5,
                font_size=16 if self.is_android else 14
            )
        )

        # 3. 发送按钮
        self.send_button = toga.Button(
            'Send',
            on_press=self.send_message,
            style=Pack(
                padding=10,
                width=80 if not self.is_android else None, # Android 宽度自适应
                background_color="#007AFF",
                color="white"
            )
        )

        # 4. 底部控制栏 (根据平台动态生成)
        bottom_controls = self._create_bottom_controls()

        # 组装界面
        input_row = toga.Box(
            children=[self.input_field, self.send_button],
            style=Pack(direction=ROW, margin_bottom=10)
        )

        # 将所有部分加入主容器
        self.main_box.add(self.chat_output)
        self.main_box.add(input_row)
        self.main_box.add(bottom_controls)

    def _create_bottom_controls(self):
        """根据平台创建不同的底部按钮"""
        
        if self.is_android:
            # --- Android 专用布局 (紧凑、图标化) ---
            settings_btn = toga.Button(
                '⚙️',  # 使用 Emoji 代替文字，节省空间
                on_press=self.open_settings,
                style=Pack(flex=1, margin_right=5, padding=15)
            )
            new_chat_btn = toga.Button(
                '➕',
                on_press=self.new_chat,
                style=Pack(flex=1, margin_left=5, padding=15)
            )
            
            return toga.Box(
                children=[settings_btn, new_chat_btn],
                style=Pack(direction=ROW, height=60) # 固定高度，防止挤压
            )
        else:
            # --- 桌面端原有布局 (保持不变) ---
            settings_btn = toga.Button(
                'SETTINGS',
                on_press=self.open_settings,
                style=Pack(flex=1, margin_right=5)
            )
            new_chat_btn = toga.Button(
                '+ NEW CHAT',
                on_press=self.new_chat,
                style=Pack(flex=1, margin_left=5)
            )
            
            return toga.Box(
                children=[settings_btn, new_chat_btn],
                style=Pack(direction=ROW, height=50)
            )

    def send_message(self, widget):
        """处理发送逻辑"""
        text = self.input_field.value
        if text:
            # 这里调用你的后端逻辑，例如:
            # self.app.backend.process_message(text)
            print(f"Sending: {text}") 
            
            # 清空输入框
            self.input_field.value = ''

    def open_settings(self, widget):
        print("Settings clicked")
        # self.app.open_settings_window()

    def new_chat(self, widget):
        print("New Chat clicked")
        self.chat_output.value = ""