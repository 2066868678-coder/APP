#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单词突围 - 启动脚本
==================
用法：
  python run_app.py            # Web模式（浏览器可看）
  python run_app.py --desktop  # 桌面窗口模式

Web模式下：
  电脑浏览器: http://localhost:8550
  手机(同WiFi): http://192.168.3.59:8550
"""

import sys, os, argparse

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 检查后端是否运行
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
backend_running = sock.connect_ex(('127.0.0.1', 8000)) == 0
sock.close()

if not backend_running:
    print("后端未启动，使用本地数据库模式（独立运行）")

import flet as ft
from app.main import WordBreakthroughApp


def main(page: ft.Page):
    WordBreakthroughApp(page)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='启动单词突围App')
    parser.add_argument('--desktop', action='store_true', help='桌面窗口模式')
    args = parser.parse_args()

    if args.desktop:
        ft.app(target=main)
    else:
        print("=" * 50)
        print("单词突围 - Web模式")
        print("=" * 50)
        print()
        print("电脑浏览器访问: http://localhost:8551")
        print("手机(同WiFi) : http://192.168.3.59:8551")
        print()
        print("按 Ctrl+C 停止")
        print("=" * 50)
        port = int(os.getenv("PORT", 8551))
        ft.run(main=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=port)
