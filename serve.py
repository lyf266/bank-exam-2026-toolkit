#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
2026 银行从业初级资格 1:1 全真机考模拟系统 · 本地一键启动服务
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
        sys.stderr.write(f"[{self.log_date_time_string()}] {args[0]} {args[1]}\n")

def run():
    os.chdir(DIRECTORY)
    global PORT
    while PORT < 8090:
        try:
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                url = f"http://localhost:{PORT}/index.html"
                print("=" * 66)
                print("🏦 2026 银行从业初级资格机考 1:1 全真仿真模拟系统已启动！")
                print(f"👉 浏览器访问链接: {url}")
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
