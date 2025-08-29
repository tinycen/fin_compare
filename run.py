#!/usr/bin/env python3
"""
贷款分期金融计算器启动脚本

使用方法:
    python run.py
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from loan_calculator import main
    main()
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装依赖包: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"运行时错误: {e}")
    sys.exit(1)