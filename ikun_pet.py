#!/usr/bin/env python3
"""
IKUN 桌面宠物 - 基于 Codex Pet 的像素鸡桌面宠物
参考项目: https://codex-pet.org/zh/pets/ikun/
功能：吃掉文件（拖入移到鸡肚子）、从鸡肚子拖出文件（自动删除源文件）
"""

import os
import sys
import random
import shutil
import traceback
import windnd

from PIL import Image, ImageTk


import tkinter as tk
from tkinter import Menu

# 日志文件路径（放在 exe 旁边）
if getattr(sys, 'frozen', False):
    LOG_FILE = os.path.join(os.path.dirname(sys.executable), 'pet.log')
else:
    LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pet.log')

def log(message):
    """记录日志到文件"""
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{message}\n")
        print(message)
    except Exception:
        pass


# 爱坤主题配色
COLOR_BG = '#1a1a1a'
COLOR_PANEL = '#2b2b2b'
COLOR_YELLOW = '#ffd200'
COLOR_YELLOW_DARK = '#cc9f00'
COLOR_TEXT = '#ffe680'
COLOR_TEXT_DARK = '#1a1a1a'


class IKunPet:
    """IKUN 桌面宠物类"""

    STATES = {
        'idle': 0,
        'run_right': 1,
        'run_left': 2,
        'wave': 3,
        'jump': 4,
        'fail': 5,
        'wait': 6,
        'sprint': 7,
        'review': 8
    }

    FRAME_COUNTS = {
        'idle': 4, 'run_right': 6, 'run_left': 6, 'wave': 4,
        'jump': 6, 'fail': 4, 'wait': 4, 'sprint': 6, 'review': 4
    }

    def __init__(self):
        self.sprite_cols = 8
        self.sprite_rows = 9
        self.frame_width = 0
        self.frame_height = 0

        self.current_state = 'idle'
        self.current_frame = 0
        self.facing_right = True
        self.is_eating = False

        self.animation_speed = 150
        self.is_animating = True

        if getattr(sys, 'frozen', False):
            self.base_path = sys._MEIPASS
            self.belly_folder = os.path.join(os.path.dirname(sys.executable), 'ikun_belly')
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))
            self.belly_folder = os.path.join(self.base_path, 'ikun_belly')
        os.makedirs(self.belly_folder, exist_ok=True)
        log(f"鸡肚子文件夹: {self.belly_folder}")

        self.window = tk.Tk()
        self.window.title("IKUN 桌面宠物")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.attributes('-transparentcolor', 'black')
        self.window.config(bg='black')

        self.window.geometry(f"+{self.window.winfo_screenwidth()//2 - 64}+{self.window.winfo_screenheight()//2 - 64}")

        self.load_sprites()

        self.pet_label = tk.Label(self.window, bg='black', bd=0, highlightthickness=0)
        self.pet_label.pack()

        self.pet_label.bind('<Button-1>', self.on_click)
        self.pet_label.bind('<B1-Motion>', self.on_drag)
        self.pet_label.bind('<ButtonRelease-1>', self.on_release)
        self.pet_label.bind('<Button-3>', self.show_menu)

        windnd.hook_dropfiles(self.pet_label, func=self.on_files_dropped)
        log("文件拖入已注册")

        self.drag_x = 0
        self.drag_y = 0

        self.belly_window = None

        self.create_menu()

        self.animate()
        self.auto_idle()

    def load_sprites(self):
        sprite_path = os.path.join(self.base_path, 'assets', 'spritesheet.webp')
        log(f"精灵图路径: {sprite_path}")
        log(f"文件存在: {os.path.exists(sprite_path)}")

        self.scale = 0.5
        try:
            self.sprite_sheet = Image.open(sprite_path)
            new_width = int(self.sprite_sheet.width * self.scale)
            new_height = int(self.sprite_sheet.height * self.scale)
            self.sprite_sheet = self.sprite_sheet.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.frame_width = self.sprite_sheet.width // self.sprite_cols
            self.frame_height = self.sprite_sheet.height // self.sprite_rows
            log(f"精灵图加载成功: {self.sprite_sheet.width}x{self.sprite_sheet.height}")
            log(f"单帧尺寸: {self.frame_width}x{self.frame_height}")
        except Exception as e:
            log(f"加载精灵图失败: {e}")
            log(traceback.format_exc())
            self.sprite_sheet = Image.new('RGBA', (640, 576), (255, 255, 0, 255))
            self.frame_width = 80
            self.frame_height = 64

    def get_frame(self, state, frame_index):
        row = self.STATES.get(state, 0)
        frame_count = self.FRAME_COUNTS.get(state, 4)
        col = frame_index % frame_count
        x1 = col * self.frame_width
        y1 = row * self.frame_height
        x2 = x1 + self.frame_width
        y2 = y1 + self.frame_height
        frame = self.sprite_sheet.crop((x1, y1, x2, y2))
        if not self.facing_right:
            frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
        return frame

    def update_display(self):
        frame = self.get_frame(self.current_state, self.current_frame)
        self.photo = ImageTk.PhotoImage(frame)
        self.pet_label.configure(image=self.photo)

    def animate(self):
        if self.is_animating:
            self.current_frame += 1
            frame_count = self.FRAME_COUNTS.get(self.current_state, 4)
            if self.current_frame >= frame_count:
                self.current_frame = 0
            self.update_display()
        self.window.after(self.animation_speed, self.animate)

    def auto_idle(self):
        if self.current_state == 'idle':
            if random.random() < 0.3:
                actions = ['wave', 'jump', 'wait', 'review']
                self.set_state(random.choice(actions))
                self.window.after(2000, self.set_state, 'idle')
            else:
                if random.random() < 0.2:
                    self.move_random()
        self.window.after(3000, self.auto_idle)

    def move_random(self):
        x = self.window.winfo_x()
        y = self.window.winfo_y()
        dx = random.randint(-50, 50)
        dy = random.randint(-20, 20)
        if dx > 0:
            self.facing_right = True
            self.set_state('run_right')
        elif dx < 0:
            self.facing_right = False
            self.set_state('run_left')
        new_x = max(0, min(x + dx, self.window.winfo_screenwidth() - 128))
        new_y = max(0, min(y + dy, self.window.winfo_screenheight() - 128))
        self.window.geometry(f"+{new_x}+{new_y}")
        self.window.after(500, lambda: self.set_state('idle'))

    def set_state(self, state):
        if state in self.STATES:
            self.current_state = state
            self.current_frame = 0

    def on_click(self, event):
        self.drag_x = event.x
        self.drag_y = event.y
        self.set_state('wave')
        self.window.after(1500, lambda: self.set_state('idle'))

    def on_drag(self, event):
        x = self.window.winfo_x() + (event.x - self.drag_x)
        y = self.window.winfo_y() + (event.y - self.drag_y)
        self.window.geometry(f"+{x}+{y}")
        if event.x - self.drag_x > 0:
            self.facing_right = True
            self.set_state('run_right')
        else:
            self.facing_right = False
            self.set_state('run_left')

    def on_release(self, event):
        self.set_state('idle')

    def on_files_dropped(self, files):
        if self.is_eating:
            log("正在吃东西，请稍等...")
            return
        file_paths = []
        for f in files:
            if isinstance(f, bytes):
                file_paths.append(f.decode('gbk'))
            else:
                file_paths.append(f)
        log(f"收到 {len(file_paths)} 个文件")
        self.eat_files(file_paths)

    def eat_files(self, file_paths):
        self.is_eating = True
        self.set_state('jump')

        eaten_count = 0
        import time
        for file_path in file_paths:
            try:
                file_name = os.path.basename(file_path)
                dest_path = os.path.join(self.belly_folder, file_name)
                if os.path.exists(dest_path):
                    name, ext = os.path.splitext(file_name)
                    dest_path = os.path.join(self.belly_folder, f"{name}_{int(time.time())}{ext}")
                shutil.move(file_path, dest_path)
                eaten_count += 1
                log(f"吃掉了: {file_name}")
            except Exception as e:
                log(f"吃不掉 {file_path}: {e}")

        log(f"总共吃掉了 {eaten_count} 个文件")
        if eaten_count > 0:
            self.show_bubble(f"嗝~吃了{eaten_count}个！")
            self.refresh_belly_window()
        else:
            self.show_bubble("吃不下了...")

        self.window.after(1500, self.finish_eating)

    def finish_eating(self):
        self.is_eating = False
        self.hide_bubble()
        self.set_state('idle')

    def show_bubble(self, text):
        if not hasattr(self, 'bubble_window') or self.bubble_window is None or not self.bubble_window.winfo_exists():
            self.bubble_window = tk.Toplevel(self.window)
            self.bubble_window.overrideredirect(True)
            self.bubble_window.attributes('-topmost', True)
            self.bubble_window.attributes('-transparentcolor', 'black')
            self.bubble_window.config(bg='black')
            self.bubble_label = tk.Label(self.bubble_window, text=text, bg='white', fg='black',
                                          font=('微软雅黑', 10, 'bold'), bd=2, relief='solid',
                                          padx=8, pady=4)
            self.bubble_label.pack()
        self.bubble_label.config(text=text)
        self.window.update_idletasks()
        x = self.window.winfo_x()
        y = self.window.winfo_y()
        self.bubble_window.geometry(f"+{x}+{y - 35}")

    def hide_bubble(self):
        if hasattr(self, 'bubble_window') and self.bubble_window is not None and self.bubble_window.winfo_exists():
            self.bubble_window.destroy()
            self.bubble_window = None

    def show_belly(self):
        if self.belly_window is not None and self.belly_window.winfo_exists():
            self.refresh_belly_window()
            self.belly_window.lift()
            self.belly_window.focus_force()
            return

        win = tk.Toplevel(self.window)
        win.title("鸡肚子 - IKUN")
        win.geometry("480x400")
        win.config(bg=COLOR_BG)
        win.attributes('-topmost', True)
        win.minsize(420, 300)

        header = tk.Frame(win, bg=COLOR_YELLOW, height=44)
        header.pack(fill='x')
        title_lbl = tk.Label(header, text="🐔 鸡肚子", bg=COLOR_YELLOW, fg=COLOR_TEXT_DARK,
                             font=('微软雅黑', 13, 'bold'), pady=8)
        title_lbl.pack(side='left', padx=12)

        list_frame = tk.Frame(win, bg=COLOR_PANEL, bd=0)
        list_frame.pack(fill='both', expand=True, padx=10, pady=(6, 6))

        canvas = tk.Canvas(list_frame, bg=COLOR_PANEL, highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient='vertical', command=canvas.yview, bg=COLOR_PANEL,
                                 troughcolor=COLOR_PANEL)
        inner = tk.Frame(canvas, bg=COLOR_PANEL)
        inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=inner, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        bottom = tk.Frame(win, bg=COLOR_BG, height=44)
        bottom.pack(fill='x', padx=10, pady=(0, 8))

        open_btn = tk.Button(bottom, text="📂 打开文件夹", bg=COLOR_PANEL, fg=COLOR_YELLOW,
                             font=('微软雅黑', 9), relief='flat', padx=10, pady=4,
                             command=lambda: os.startfile(self.belly_folder))
        open_btn.pack(side='left', padx=(0, 8))

        clear_btn = tk.Button(bottom, text="吐光", bg='#cc3300', fg='white',
                              font=('微软雅黑', 9, 'bold'), relief='flat', padx=14, pady=4,
                              command=self.clear_belly)
        clear_btn.pack(side='right')

        def on_closing():
            self.belly_window = None
            win.destroy()
        win.protocol('WM_DELETE_WINDOW', on_closing)

        self.belly_window = win
        self.belly_canvas = canvas
        self.belly_inner = inner

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        canvas.bind('<Enter>', lambda e: canvas.bind_all('<MouseWheel>', on_mousewheel))
        canvas.bind('<Leave>', lambda e: canvas.unbind_all('<MouseWheel>'))

        self.refresh_belly_window()

    def refresh_belly_window(self):
        if self.belly_window is None or not self.belly_window.winfo_exists():
            return

        for child in self.belly_inner.winfo_children():
            child.destroy()

        items = sorted(os.listdir(self.belly_folder))
        if not items:
            tk.Label(self.belly_inner, text="（空的，啥也没吃）", bg=COLOR_PANEL, fg='#888888',
                     font=('微软雅黑', 10), pady=40).pack()
            return

        for fname in items:
            fpath = os.path.join(self.belly_folder, fname)
            is_dir = os.path.isdir(fpath)

            row = tk.Frame(self.belly_inner, bg=COLOR_PANEL)
            row.pack(fill='x', padx=4, pady=2)

            icon = "📁" if is_dir else "📄"
            lbl = tk.Label(row, text=f"{icon} {fname}", bg=COLOR_PANEL, fg=COLOR_TEXT,
                           font=('微软雅黑', 9), anchor='w', padx=6, pady=4, cursor='hand2')
            lbl.pack(side='left', fill='x', expand=True)
            lbl.bind('<Double-Button-1>', lambda e, p=fpath: os.startfile(p))

            def make_menu(e, p=fpath, n=fname):
                m = Menu(self.belly_window, tearoff=0, bg=COLOR_PANEL, fg=COLOR_TEXT,
                         activebackground=COLOR_YELLOW, activeforeground=COLOR_TEXT_DARK)
                m.add_command(label="吐到桌面", command=lambda: self.spit_to_desktop(p))
                m.add_command(label="打开", command=lambda: os.startfile(p))
                m.add_separator()
                m.add_command(label="删除", command=lambda: self.delete_belly_item(p, n))
                m.post(e.x_root, e.y_root)
            lbl.bind('<Button-3>', make_menu)

            btn = tk.Button(row, text="吐到桌面", bg=COLOR_YELLOW, fg=COLOR_TEXT_DARK,
                            font=('微软雅黑', 9, 'bold'), relief='flat', padx=8, pady=2,
                            cursor='hand2',
                            command=lambda p=fpath: self.spit_to_desktop(p))
            btn.pack(side='right', padx=(4, 2))

            del_btn = tk.Button(row, text="×", bg='#4a1a1a', fg='#ff6666',
                                font=('微软雅黑', 9), relief='flat', padx=6, pady=2,
                                cursor='hand2',
                                command=lambda n=fname, p=fpath: self.delete_belly_item(p, n))
            del_btn.pack(side='right')

    def spit_to_desktop(self, path):
        try:
            desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            if not os.path.exists(desktop):
                desktop = os.path.join(os.environ['USERPROFILE'], '桌面')
            name = os.path.basename(path)
            dest = os.path.join(desktop, name)
            if os.path.exists(dest):
                import time
                nm, ext = os.path.splitext(name)
                dest = os.path.join(desktop, f"{nm}_{int(time.time())}{ext}")
            shutil.move(path, dest)
            log(f"吐到桌面: {name}")
            self.refresh_belly_window()
            self.show_bubble(f"吐到了桌面~")
            self.window.after(1500, self.hide_bubble)
        except Exception as e:
            log(f"吐到桌面失败: {e}")

    def delete_belly_item(self, path, name):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            log(f"删除了: {name}")
            self.refresh_belly_window()
        except Exception as e:
            log(f"删除失败 {name}: {e}")

    def clear_belly(self):
        try:
            count = 0
            for item in os.listdir(self.belly_folder):
                item_path = os.path.join(self.belly_folder, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    count += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    count += 1
            log(f"吐出了 {count} 个文件")
            self.refresh_belly_window()
            self.show_bubble(f"全都吐出来了！")
            self.window.after(1500, self.hide_bubble)
        except Exception as e:
            log(f"清空鸡肚子失败: {e}")

    def create_menu(self):
        self.menu = Menu(self.window, tearoff=0)
        self.menu.add_command(label="挥手", command=lambda: self.set_state('wave'))
        self.menu.add_command(label="跳跃", command=lambda: self.set_state('jump'))
        self.menu.add_command(label="奔跑", command=lambda: self.set_state('sprint'))
        self.menu.add_separator()
        self.menu.add_command(label="向左看", command=self.look_left)
        self.menu.add_command(label="向右看", command=self.look_right)
        self.menu.add_separator()
        self.menu.add_command(label="打开鸡肚子", command=self.show_belly)
        self.menu.add_command(label="清空鸡肚子", command=self.clear_belly)
        self.menu.add_separator()
        self.menu.add_command(label="退出", command=self.quit)

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def look_left(self):
        self.facing_right = False

    def look_right(self):
        self.facing_right = True

    def quit(self):
        self.is_animating = False
        self.window.destroy()

    def run(self):
        log("IKUN 桌面宠物已启动！")
        self.window.mainloop()


def main():
    log("=" * 50)
    log("IKUN 桌面宠物启动")
    log(f"Python 版本: {sys.version}")
    log(f"脚本路径: {os.path.abspath(__file__)}")
    try:
        pet = IKunPet()
        pet.run()
    except Exception as e:
        log(f"程序异常: {e}")
        log(traceback.format_exc())


if __name__ == '__main__':
    main()
