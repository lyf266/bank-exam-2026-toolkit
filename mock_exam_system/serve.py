#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
2026 银行从业初级资格机考模拟系统 · 本地一键启动服务
"""

import http.server
import socketserver
import os
import sys
import webbrowser

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        # 简化日志输出
        sys.stderr.write(f"[{self.log_date_time_string()}] {args[0]} {args[1]}\n")

def run():
    os.chdir(DIRECTORY)
    # 尝试绑定端口，如果被占用顺延
    global PORT
    while PORT < 8090:
        try:
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                url = f"http://localhost:{PORT}/"
                print("=" * 66)
                print("🏦 2026 银行从业初级资格机考 1:1 仿真模拟系统已启动！")
                print(f"👉 本地访问地址: {url}")
                print(f"📁 根目录: {DIRECTORY}")
                print("⌨️  按 Ctrl + C 即可随时停止服务")
                print("=" * 66)
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
                httpd.serve_forever()
                break
        except OSError as e:
            if e.errno == 98: # Address already in use
                PORT += 1
            else:
                raise e

if __name__ == '__main__':
    run()
