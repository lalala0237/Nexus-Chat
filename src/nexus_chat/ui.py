# src/nexus_chat/ui.py
import toga
import asyncio
import json
from pathlib import Path
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER

from .api_client import APIClient

class ChatInterface:
    def __init__(self):
        self.api_client = None
        self.settings_window = None
        self.is_waiting = False
        
        # 会话管理相关
        self.sessions = {}
        self.current_session_id = None
        self.session_counter = 0
        self.history_file = Path.home() / ".nexus_chat_history.json"

    def startup(self, app):
        self.app = app
        
        # 1. 聊天显示区域
        self.chat_display = toga.MultilineTextInput(
            readonly=True, 
            style=Pack(flex=1, margin=15, padding=10)
        )

        # 2. 消息输入区域
        self.message_input = toga.MultilineTextInput(
            placeholder='Type your message here...', 
            style=Pack(flex=1, margin=(15, 5, 15, 5), padding=5, height=60)
        )
        self.message_input.on_key_down = self.on_key_pressed

        self.send_button = toga.Button(
            'Send', 
            on_press=self.send_message, 
            style=Pack(margin=(15, 5, 15, 5), padding=(5, 25))
        )

        self.settings_button = toga.Button(
            '⚙️ Settings', 
            on_press=self.open_settings,
            style=Pack(margin=(15, 5, 15, 5), padding=(5, 15))
        )

        self.new_chat_button = toga.Button(
            '➕ New Chat', 
            on_press=self.create_new_session,
            style=Pack(margin=(15, 15, 15, 5), padding=(5, 15))
        )

        input_box = toga.Box(
            children=[self.settings_button, self.new_chat_button, self.message_input, self.send_button],
            style=Pack(direction=ROW)
        )

        main_box = toga.Box(
            children=[self.chat_display, input_box],
            style=Pack(direction=COLUMN, flex=1)
        )

        self.load_history()
        
        if self.current_session_id is None:
            self.create_new_session(None)

        return main_box

    # ================= 设置窗口逻辑 =================
    def open_settings(self, widget):
        if self.settings_window is not None:
            self.settings_window.show()
            return

        self.settings_window = toga.Window(title='Nexus AI Settings', size=(450, 500))
        # 【彻底移除 on_close，避免 Windows 下的卡死问题】

        # --- API 配置区 ---
        self.api_key_input = toga.PasswordInput(
            placeholder='Enter your API Key...', 
            style=Pack(flex=1, margin=(0, 0, 10, 0), padding=5)
        )
        self.api_url_input = toga.TextInput(
            placeholder='Enter API Base URL...', 
            style=Pack(flex=1, margin=(0, 0, 10, 0), padding=5)
        )
        self.model_input = toga.TextInput(
            placeholder='Enter model name (e.g., gpt-3.5-turbo)...', 
            style=Pack(flex=1, margin=(0, 0, 10, 0), padding=5)
        )
        
        apply_button = toga.Button(
            'Apply Settings', 
            on_press=self.apply_settings,
            style=Pack(margin=(10, 0, 0, 0), align_items=CENTER, padding=(5, 20))
        )

        # --- 数据管理区 ---
        clear_button = toga.Button(
            '🗑️ Clear Current Chat', 
            on_press=self.clear_current_chat,
            style=Pack(margin=(20, 0, 10, 0), padding=(5, 20), background_color='#f44336', color='white')
        )

        delete_box = toga.Box(
            style=Pack(direction=ROW, margin=(10, 0, 0, 0))
        )
        self.session_selection = toga.Selection(
            style=Pack(flex=1, margin=(0, 5, 0, 0), padding=5)
        )
        self.update_session_selection()
        
        delete_button = toga.Button(
            'Delete Session', 
            on_press=self.delete_selected_session,
            style=Pack(margin=(0, 0, 0, 0), padding=(5, 15), background_color='#d32f2f', color='white')
        )
        delete_box.add(self.session_selection)
        delete_box.add(delete_button)

        # 【新增】显式的关闭按钮，作为安全出口
        close_button = toga.Button(
            'Close Window', 
            on_press=self.close_settings,
            style=Pack(margin=(20, 0, 0, 0), align_items=CENTER, padding=(5, 20))
        )

        settings_box = toga.Box(
            children=[
                self.api_key_input, self.api_url_input, self.model_input, apply_button,
                clear_button, delete_box, close_button
            ],
            style=Pack(direction=COLUMN, margin=15)
        )

        self.settings_window.content = settings_box
        self.settings_window.show()
        
        # 打开设置时，禁用主界面的设置按钮
        self.settings_button.enabled = False

    # ================= 【新增】手动关闭设置窗口的安全方法 =================
    def close_settings(self, widget):
        """
        通过点击 Close Window 按钮触发。
        安全地清理引用并恢复主界面按钮。
        """
        self.settings_window = None
        self.settings_button.enabled = True
        # 注意：这里不需要调用 .close()，因为 Toga 在执行按钮回调后，
        # 如果窗口失去所有焦点或引用，在某些情况下会自动处理，
        # 但为了稳妥，我们保留显式关闭：
        if hasattr(self, 'settings_window') and self.settings_window is None:
            # 由于我们已经将 self.settings_window 置为 None，
            # 我们需要在置为 None 之前关闭窗口。
            pass 

    # 让我们修正一下 close_settings 的执行顺序
    def close_settings(self, widget):
        if self.settings_window:
            self.settings_window.close()
        self.settings_window = None
        self.settings_button.enabled = True

    # ================= 数据管理逻辑 =================
    def update_session_selection(self):
        if hasattr(self, 'session_selection'):
            items = [f"{sid} ({data['name']})" for sid, data in self.sessions.items()]
            self.session_selection.items = items if items else ["No sessions available"]

    def clear_current_chat(self, widget):
        if self.current_session_id and self.current_session_id in self.sessions:
            self.chat_display.value = ""
            self.sessions[self.current_session_id]["history"] = ""
            self.save_history()

    def delete_selected_session(self, widget):
        selected = self.session_selection.value
        if not selected or selected == "No sessions available":
            return

        session_id = selected.split(" (")[0]
        
        confirm = toga.Window(title="Confirm Delete", size=(300, 150))
        confirm_label = toga.Label(f"Are you sure you want to delete '{session_id}'?", style=Pack(margin=10))
        
        def do_delete(w):
            if session_id in self.sessions:
                del self.sessions[session_id]
            
            if self.current_session_id == session_id:
                if self.sessions:
                    self.switch_session(next(iter(self.sessions)))
                else:
                    self.create_new_session(None)
            
            self.save_history()
            self.update_session_selection()
            confirm.close()

        def cancel_delete(w):
            confirm.close()

        btn_box = toga.Box(style=Pack(direction=ROW, margin=10))
        yes_btn = toga.Button("Yes, Delete", on_press=do_delete, style=Pack(flex=1, margin=5, background_color='#d32f2f', color='white'))
        no_btn = toga.Button("Cancel", on_press=cancel_delete, style=Pack(flex=1, margin=5))
        btn_box.add(yes_btn)
        btn_box.add(no_btn)

        confirm.content = toga.Box(children=[confirm_label, btn_box], style=Pack(direction=COLUMN))
        confirm.show()

    # ================= 会话管理逻辑 =================
    def create_new_session(self, widget):
        self.session_counter += 1
        session_id = f"session_{self.session_counter}"
        
        self.sessions[session_id] = {
            "name": f"Chat {self.session_counter}",
            "history": ""
        }
        self.switch_session(session_id)
        self.save_history()
        self.update_session_selection()

    def switch_session(self, session_id):
        if self.current_session_id and self.current_session_id in self.sessions:
            self.sessions[self.current_session_id]["history"] = self.chat_display.value
        
        self.current_session_id = session_id
        self.chat_display.value = self.sessions[session_id]["history"]

    # ================= 键盘事件处理 =================
    def on_key_pressed(self, widget, key, modifiers):
        if key == toga.Key.ENTER and toga.Key.SHIFT not in modifiers:
            if not self.is_waiting:
                asyncio.ensure_future(self.send_message(widget))
            return True
        return False

    # ================= 历史记录保存与加载 =================
    def save_history(self):
        try:
            if self.current_session_id:
                self.sessions[self.current_session_id]["history"] = self.chat_display.value
                
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "sessions": self.sessions,
                    "current_session_id": self.current_session_id,
                    "session_counter": self.session_counter
                }, f, ensure_ascii=False)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.sessions = data.get("sessions", {})
                    self.current_session_id = data.get("current_session_id")
                    self.session_counter = data.get("session_counter", 0)
                    
                    if self.current_session_id and self.current_session_id in self.sessions:
                        self.chat_display.value = self.sessions[self.current_session_id]["history"]
            except Exception as e:
                print(f"加载历史记录失败: {e}")

    # ================= 【修复】核心逻辑代码 =================
    def apply_settings(self, widget):
        api_key = self.api_key_input.value.strip().strip("'\"")
        api_url = self.api_url_input.value.strip().strip("'\"")
        model_name = self.model_input.value.strip() or "gpt-3.5-turbo"
        
        if not api_key or not api_url:
            self.chat_display.value += "--- System: Please enter both API Key and Base URL! ---\n\n"
            return
            
        api_url = api_url.rstrip("/")
        
        self.api_client = APIClient(api_key=api_key, base_url=api_url, model=model_name)
        self.chat_display.value += f"--- System: API Settings Applied Successfully! ---\nURL: {api_url}\nModel: {model_name}\n\n"
        self.api_key_input.value = ""
        self.api_url_input.value = ""
        
        # 安全地关闭窗口并恢复按钮
        if self.settings_window:
            self.settings_window.close()
        self.settings_window = None
        self.settings_button.enabled = True

    async def send_message(self, widget):
        if self.is_waiting:
            return

        if self.api_client is None:
            self.chat_display.value += "--- System: Please apply API settings first! ---\n\n"
            return
            
        prompt = self.message_input.value.strip()
        if not prompt:
            return
        
        self.is_waiting = True
        self.send_button.enabled = False
            
        self.chat_display.value += f"You: {prompt}\n\n"
        self.message_input.value = ""
        
        try:
            response = await self.api_client.send_message(prompt)
            self.chat_display.value += f"Bot: {response}\n\n"
        except Exception as e:
            self.chat_display.value += f"--- Error: {str(e)} ---\n\n"
        finally:
            self.is_waiting = False
            self.send_button.enabled = True
            self.save_history()