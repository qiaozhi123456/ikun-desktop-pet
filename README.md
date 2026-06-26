# IKUN 桌面宠物 🐔

一个基于 Codex Pet ikun 的桌面宠物程序，支持文件拖拽"吃掉"功能。

## 功能

- 🐔 爱坤像素鸡桌面宠物，循环播放动画
- 📂 拖拽文件到宠物身上即可"吃掉"（放入鸡肚子文件夹）
- 📋 打开鸡肚子窗口管理已吃文件
- 💨 从鸡肚子窗口"吐到桌面"按钮将文件移回桌面
- 🖱️ 右键菜单：打开鸡肚子 / 吐光所有 / 退出

## 使用

1. 下载 IKUN-Pet.exe
2. 运行 `IKUN-Pet.exe` 或双击 `启动爱坤鸡.vbs`

## 技术栈

- Python 3 + tkinter + Pillow
- windnd（文件拖入）
- PyInstaller（打包单文件 exe）

## 构建

```bash
pip install -r requirements.txt
pyinstaller --noconsole --name "IKUN-Pet" --add-data "assets;assets" --icon "assets/icon.ico" --onefile ikun_pet.py
```