# -*- coding: utf-8 -*-
"""
tests/conftest.py
=================
Pytest 全局上下文与路径初始化。
"""
import os
import sys

# 确保项目根目录在 sys.path 首位
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
