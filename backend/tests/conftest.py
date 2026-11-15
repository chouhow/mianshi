import os
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# 测试数据写入临时目录，避免污染真实数据
_tmp = tempfile.mkdtemp(prefix="mianshi_test_")
os.environ["MIANSHI_DATA_DIR"] = _tmp
