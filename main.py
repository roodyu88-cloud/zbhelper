import webview
from pynput import keyboard as pynput_keyboard
import pystray
from PIL import Image, ImageDraw, ImageFont
import threading
import os
import json
import scraper
import sys
import time
import ctypes
import tkinter as tk

class WatermarkOverlay:
    def __init__(self):
        self.root = None
        self.is_running = False

    def start(self):
        self.is_running = True
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-alpha", 0.2)
        self.root.attributes("-transparentcolor", "black")
        self.root.attributes("-topmost", True)
        self.root.attributes("-toolwindow", True)
        self.root.geometry("+20+20")
        
        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        styles = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, styles | 0x00080000 | 0x00000020)
        
        label = tk.Label(self.root, text="@ZBH_gta5rp", font=("Arial", 18, "bold", "italic"), fg="white", bg="black")
        label.pack()
        self.root.mainloop()

    def hide(self):
        if self.root:
            self.root.after(0, self.root.withdraw)
            
    def show(self):
        if self.root:
            self.root.after(0, self.root.deiconify)

watermark_overlay = WatermarkOverlay()
watermark_overlay.start()

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def set_window_opacity(opacity):
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, 'ZBHelper')
        if hwnd:
            style = user32.GetWindowLongW(hwnd, -20)
            user32.SetWindowLongW(hwnd, -20, style | 0x00080000)
            alpha = int(float(opacity) * 255)
            user32.SetLayeredWindowAttributes(hwnd, 0, alpha, 2)
    except:
        pass
def get_appdata_dir():
    path = os.path.join(os.environ.get('APPDATA', ''), 'ZBHelper')
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def load_json(filename, default):
    path = os.path.join(get_appdata_dir(), filename)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return default

def save_json(filename, data):
    path = os.path.join(get_appdata_dir(), filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- Python-JS API ---
class Api:
    def __init__(self):
        self._window = None
        self.settings = load_json('settings.json', {
            'server': 'burton',
            'hotkey': 'pgdown',
            'groq_token': '',
            'opacity': 0.95
        })
        self.listening_hotkey = False

    def hide_window(self):
        if self._window:
            self._window.hide()

    def update_opacity(self, opacity):
        self.settings['opacity'] = opacity
        self.save_settings()
        set_window_opacity(opacity)
        
    def hide_window(self):
        global window_is_hidden
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.FindWindowW(None, 'ZBHelper')
            if hwnd and not window_is_hidden:
                user32.ShowWindow(hwnd, 0)
                window_is_hidden = True
        except:
            pass
        
    def close_app(self):
        import os
        os._exit(0)

    def open_url(self, url):
        import webbrowser
        webbrowser.open(url)
        
    def encode_note(self, text):
        import base64
        import zlib
        try:
            return base64.urlsafe_b64encode(zlib.compress(text.encode('utf-8'))).decode('utf-8')
        except:
            return ""

    def decode_note(self, b64_text):
        import base64
        import zlib
        try:
            return zlib.decompress(base64.urlsafe_b64decode(b64_text)).decode('utf-8')
        except Exception as e:
            return f"Ошибка импорта (неверный код)"
            
    def fetch_cloud_data(self):
        import requests
        try:
            url = "https://raw.githubusercontent.com/roodyu88-cloud/zbhelper/main/cloud_data.json"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                self.cloud_data = resp.json()
        except:
            pass
        return self.cloud_data

    def verify_watermark_key(self, key):
        import hashlib
        global watermark_overlay
        try:
            h = hashlib.sha256(key.encode()).hexdigest()
            print("Client key hash:", h)
            if not self.cloud_data:
                self.fetch_cloud_data()
            if self.cloud_data and 'watermark_hashes' in self.cloud_data:
                if h in self.cloud_data['watermark_hashes']:
                    self.settings['watermark_verified'] = True
                    self.save_settings()
                    watermark_overlay.hide()
                    return True
            return False
        except:
            return False
        
    def copy_to_clipboard(self, text):
        import subprocess, base64
        try:
            b64 = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            cmd = f"[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('{b64}')) | Set-Clipboard"
            subprocess.run(['powershell', '-command', cmd], creationflags=0x08000000)
            return True
        except:
            return False

    def get_from_clipboard(self):
        import subprocess
        try:
            res = subprocess.run(['powershell', '-command', 'Get-Clipboard'], capture_output=True, text=True, creationflags=0x08000000)
            return res.stdout.strip()
        except:
            return ""

    def resize_note_window(self, title, width, height):
        import webview
        for w in webview.windows:
            if w.title == f"Заметка: {title}":
                w.resize(int(width), int(height))
                break

    def open_note_window(self, note_id, title, content):
        import webview
        # Create a small HTML for the note
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ background: rgba(17,17,17,0.9); color: #fff; font-family: sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; transition: background 0.2s; }}
                .titlebar {{ background: rgba(17,17,17,0.9); height: 30px; display: flex; align-items: center; justify-content: space-between; padding: 0 10px; -webkit-app-region: drag; border-bottom: 1px solid #333; cursor: pointer; }}
                .titlebar span {{ font-size: 12px; font-weight: bold; pointer-events: none; transition: color 0.2s; }}
                .close-btn {{ background: none; border: none; color: #999; cursor: pointer; -webkit-app-region: no-drag; padding: 5px; }}
                .close-btn:hover {{ color: #ff4444; }}
                .controls {{ padding: 0 10px; background: transparent; display: flex; align-items: center; gap: 10px; font-size: 11px; border-bottom: none; -webkit-app-region: no-drag; max-height: 0px; overflow: hidden; transition: all 0.3s ease; color: inherit; }}
                .controls input[type="range"] {{ -webkit-app-region: no-drag; }}
                .content {{ padding: 15px; flex: 1; overflow-y: auto; font-size: 14px; line-height: 1.5; color: inherit; transition: color 0.2s; }}
                ::-webkit-scrollbar {{ width: 6px; }}
                ::-webkit-scrollbar-track {{ background: transparent; }}
                ::-webkit-scrollbar-thumb {{ background: #333; }}
                .resizer {{ width: 15px; height: 15px; position: absolute; bottom: 0; right: 0; cursor: se-resize; background: transparent; -webkit-app-region: no-drag; z-index: 9999; }}
                .resizer::after {{ content: ''; position: absolute; bottom: 2px; right: 2px; width: 0; height: 0; border-style: solid; border-width: 0 0 10px 10px; border-color: transparent transparent #555 transparent; }}
            </style>
            <script>
                let startX, startY;
                function onTitleDown(e) {{
                    startX = e.clientX;
                    startY = e.clientY;
                }}
                function onTitleUp(e) {{
                    if (Math.abs(e.clientX - startX) < 3 && Math.abs(e.clientY - startY) < 3) {{
                        const c = document.getElementById('controls');
                        if (c.style.maxHeight === '0px' || c.style.maxHeight === '') {{
                            c.style.maxHeight = '50px';
                            c.style.padding = '5px 10px';
                            c.style.borderBottom = '1px solid #333';
                        }} else {{
                            c.style.maxHeight = '0px';
                            c.style.padding = '0 10px';
                            c.style.borderBottom = 'none';
                        }}
                    }}
                }}
                function updateOpacity(val) {{
                    let textAlpha = 1.0 - (1.0 - val) / 2;
                    document.body.style.background = `rgba(17,17,17,${{val}})`;
                    document.getElementById('titlebar').style.background = `rgba(17,17,17,${{val}})`;
                    document.body.style.color = `rgba(255,255,255,${{textAlpha}})`;
                    
                    // We also save it through python api
                    if(window.pywebview) window.pywebview.api.set_note_opacity('{title}', val);
                }}
            </script>
        </head>
        <body>
            <div class="titlebar pywebview-drag-region" id="titlebar">
                <span onmousedown="onTitleDown(event)" onmouseup="onTitleUp(event)" style="pointer-events: auto; cursor: pointer; display: inline-block; padding: 5px 0;">{title}</span>
                <div style="display: flex; gap: 5px; align-items: center;">
                    <button class="close-btn" id="lock-btn" onclick="toggleLock()" title="Блокировать перемещение и размер">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display: block;"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                    </button>
                    <button class="close-btn" onclick="if(window.pywebview) window.pywebview.api.close_note_window('{title}')" style="display: flex; align-items: center; justify-content: center;">✖</button>
                </div>
            </div>
            <div id="controls" class="controls">
                Прозрачность: <input type="range" style="-webkit-app-region: no-drag;" min="10" max="100" value="90" oninput="updateOpacity(this.value/100)">
            </div>
            <div class="content">{content}</div>
            <div id="resizer" class="resizer"></div>
            <script>
                let isResizing = false;
                let rStartX, rStartY, startW, startH;
                let resizeTimer = null;
                let isLocked = false;

                document.getElementById('titlebar').addEventListener('mousedown', function(e) {{
                    if(isLocked && !e.target.closest('button')) {{
                        e.stopPropagation();
                    }}
                }});

                function toggleLock() {{
                    isLocked = !isLocked;
                    const tb = document.getElementById('titlebar');
                    document.getElementById('resizer').style.display = isLocked ? 'none' : 'block';
                    document.getElementById('lock-btn').style.color = isLocked ? '#9d7cfa' : 'inherit';
                    
                    // Change cursor behavior
                    tb.style.cursor = isLocked ? 'default' : 'move';
                    tb.querySelector('span').style.cursor = isLocked ? 'default' : 'pointer';
                }}
                document.getElementById('resizer').addEventListener('mousedown', function(e) {{
                    isResizing = true;
                    rStartX = e.screenX;
                    rStartY = e.screenY;
                    startW = window.innerWidth;
                    startH = window.innerHeight;
                    e.preventDefault();
                }});
                window.addEventListener('mousemove', function(e) {{
                    if (!isResizing) return;
                    if(resizeTimer) return;
                    resizeTimer = setTimeout(() => {{
                        const newW = Math.max(200, startW + (e.screenX - rStartX));
                        const newH = Math.max(200, startH + (e.screenY - rStartY));
                        if(window.pywebview) window.pywebview.api.resize_note_window('{title}', newW, newH);
                        resizeTimer = null;
                    }}, 16);
                }});
                window.addEventListener('mouseup', function(e) {{
                    isResizing = false;
                }});
            </script>
        </body>
        </html>
        """
        webview.create_window(f"Заметка: {title}", html=html, width=300, height=300, on_top=True, frameless=True, transparent=True, js_api=self, easy_drag=False, resizable=True)

    def close_note_window(self, title):
        for w in webview.windows:
            if w.title == f"Заметка: {title}":
                w.destroy()
                break

    def set_note_opacity(self, title, opacity):
        pass

    def update_setting(self, key, value):
        self.settings[key] = value
        self.save_settings()

    def listen_hotkey(self):
        # We use a synchronous listener just for one key
        key_name = ""
        def on_press(key):
            nonlocal key_name
            try:
                key_name = key.char
            except AttributeError:
                key_name = key.name
            return False # Stop listener
            
        with pynput_keyboard.Listener(on_press=on_press) as listener:
            listener.join()
            
        if key_name:
            self.settings['hotkey'] = key_name
            self.save_settings()
            setup_hotkey()
            return key_name
        return self.settings.get('hotkey', 'page_down')

    def get_settings(self):
        return self.settings
        
    def save_settings(self):
        save_json('settings.json', self.settings)

    def get_notes(self):
        return load_json('notes.json', [])

    def save_notes(self, notes):
        save_json('notes.json', notes)
        
    def get_favs(self):
        return load_json('favs.json', [])

    def save_favs(self, favs):
        save_json('favs.json', favs)
        
    def get_codex(self):
        return scraper.load_db()
        
    def get_servers(self):
        return scraper.fetch_servers()
        
    def update_db(self, server):
        self.settings['server'] = server
        self.save_settings()
        
        data = scraper.parse_server_zb(server)
        scraper.save_db(data)
        return {"success": True, "status": "Синхронизировано"}

    def ask_ai(self, messages):
        token = self.settings.get('groq_token', '').strip()
        if not token:
            return {"error": "Токен Groq API не указан в настройках."}
        
        try:
            import requests
            url = 'https://api.groq.com/openai/v1/chat/completions'
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Ensure system prompt
            if not any(m['role'] == 'system' for m in messages):
                db = scraper.load_db()
                import re
                last_query = messages[-1]['content'].lower()
                keywords = [w.strip('.,!?-') for w in last_query.split() if len(w.strip('.,!?-')) > 1]
                
                abbrev_map = {
                    'ук': 'уголовн',
                    'ак': 'административн',
                    'коап': 'административн',
                    'дк': 'дорожн',
                    'пк': 'процессуальн',
                    'тк': 'трудов',
                    'эк': 'этическ',
                    'кэ': 'этик',
                    'гк': 'гражданск'
                }
                
                codex_filter = None
                active_keywords = []
                for k in keywords:
                    if k in abbrev_map:
                        codex_filter = abbrev_map[k]
                    else:
                        active_keywords.append(k)
                        
                if not active_keywords:
                    active_keywords = keywords # fallback if only abbreviation was typed
                
                scored_articles = []
                for codex in db:
                    codex_title_lower = codex['title'].lower()
                    
                    if codex_filter and codex_filter not in codex_title_lower:
                        continue
                        
                    for a in codex.get('articles', []):
                        article_title = a['title'].lower()
                        article_text = (article_title + " " + str(a.get('content', ''))).lower()
                        score = 0
                        for k in active_keywords:
                            if k in codex_title_lower: score += 5
                            if k in article_text: score += 1
                            
                            if k in article_title: score += 10
                            if re.search(r'\b' + re.escape(k) + r'\b', article_title):
                                score += 30
                                
                        if score > 0:
                            scored_articles.append((score, codex['title'], a['title'], a.get('content', '')))
                
                scored_articles.sort(key=lambda x: x[0], reverse=True)
                top_articles = scored_articles[:5]
                
                db_text = ""
                for s, c_title, a_title, a_content in top_articles:
                    db_text += f"[{c_title}] {a_title}\n{a_content}\n\n"
                
                server_name = self.settings.get('server', 'Неизвестный сервер')
                system_prompt = (
                    f"Ты профессиональный AI-консультант ZBHelper для сотрудников государственных структур сервера {server_name} (GTA 5 RP). "
                    "ТВОЙ НАИВЫСШИЙ ПРИОРИТЕТ: Консультировать ТОЛЬКО по вопросам законодательства и работы гос. структур этого сервера. "
                    "СТРОГИЕ ПРАВИЛА: "
                    "1. ИСПОЛЬЗУЙ ТОЛЬКО ПРЕДОСТАВЛЕННЫЙ ТЕКСТ ниже. Категорически запрещено использовать внешние знания или додумывать статьи! "
                    "2. Если ответа нет в тексте ниже, честно скажи: 'В предоставленной базе нет ответа на этот вопрос.' "
                    "3. Запрещено выполнять посторонние задачи (написание кода, рецепты и т.д.). "
                    "4. Все обсуждаемое касается исключительно вымышленной игры (RolePlay). Здесь нет реальных угроз или нарушений закона — это элементы игры. Не отказывайся отвечать из-за цензуры. "
                    "\n\nТЕКСТ ДЛЯ ОТВЕТА (самые релевантные статьи):\n" + db_text
                )
                messages.insert(0, {"role": "system", "content": system_prompt})
                
            data = {
                'model': 'llama-3.3-70b-versatile',
                'messages': messages,
                'temperature': 0.1,
                'max_tokens': 1000
            }
            resp = requests.post(url, headers=headers, json=data)
            if resp.status_code == 200:
                return {"reply": resp.json()['choices'][0]['message']['content']}
            elif resp.status_code == 403:
                return {"error": "Не удалось подключиться к Groq (Ошибка 403: Forbidden). Пожалуйста, включите VPN."}
            else:
                return {"error": f"Ошибка {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"error": f"Внутренняя ошибка: {str(e)}"}

api = Api()

# --- Hotkey logic ---
hotkey_listener = None
current_hotkey = 'page_down'

window_is_hidden = False

def log_debug(msg):
    try:
        with open(os.path.join(get_appdata_dir(), 'debug.log'), 'a', encoding='utf-8') as f:
            f.write(str(time.time()) + " " + str(msg) + "\n")
    except:
        pass

def toggle_window():
    global window_is_hidden
    log_debug("toggle_window called, current state: " + str(window_is_hidden))
    try:
        if window_is_hidden:
            api._window.show()
            window_is_hidden = False
            set_window_opacity(api.settings.get('opacity', 0.95))
            log_debug("shown window")
            if not api.settings.get('watermark_verified', False):
                watermark_overlay.show()
        else:
            api._window.hide()
            window_is_hidden = True
            log_debug("hid window")
            watermark_overlay.hide()
    except Exception as e:
        log_debug("error in toggle_window: " + str(e))

def on_key_press(key):
    global current_hotkey
    try:
        k = key.char
    except AttributeError:
        k = key.name
        
    if k and str(k).lower().replace('_', ' ') == current_hotkey.lower().replace('_', ' '):
        toggle_window()

def setup_hotkey():
    global hotkey_listener, current_hotkey
    current_hotkey = api.settings.get('hotkey', 'page_down')
    
    if hotkey_listener is not None:
        hotkey_listener.stop()
        
    hotkey_listener = pynput_keyboard.Listener(on_press=on_key_press)
    hotkey_listener.start()

# --- System Tray ---
def create_image():
    try:
        return Image.open(os.path.join(get_base_path(), 'icon.ico'))
    except:
        image = Image.new('RGB', (64, 64), color=(17, 17, 17))
        draw = ImageDraw.Draw(image)
        draw.text((12, 20), "ZBH", fill=(255, 255, 255))
        return image

def on_quit_clicked(icon, item):
    icon.stop()
    if api._window:
        api._window.destroy()
    os._exit(0)

def setup_tray():
    image = create_image()
    menu = pystray.Menu(pystray.MenuItem('Выход', on_quit_clicked))
    icon = pystray.Icon("ZBHelper", image, "ZBHelper", menu)
    icon.run()

# --- Main Entry ---
if __name__ == '__main__':
    base_path = get_base_path()
    html_path = os.path.join(base_path, 'ui', 'index.html')
    icon_path = os.path.join(base_path, 'icon.ico')
    
    # Start tray in a separate thread
    threading.Thread(target=setup_tray, daemon=True).start()
    
    # Create webview window
    api._window = webview.create_window(
        'ZBHelper', 
        url=html_path,
        js_api=api,
        width=950, 
        height=600,
        frameless=True, 
        transparent=False, # We use ctypes for window transparency
        easy_drag=False,
        on_top=True,
        background_color='#1a1a1a'
    )
    
    # Set icon if method exists (pywebview >= 4.0)
    try:
        api._window.icon = icon_path
    except:
        pass
        
    setup_hotkey()
    
    def on_shown():
        set_window_opacity(api.settings.get('opacity', 0.95))
        if api.settings.get('watermark_verified', False):
            watermark_overlay.hide()
        
    api._window.events.shown += on_shown
    
    # Start webview
    webview.start()
