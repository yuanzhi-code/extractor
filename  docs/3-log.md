# 使用文件轮转的轻量化日志方案
```python
import os
from datetime import datetime
from pathlib import Path

class RotatingLogger:
    def __init__(self, log_dir="logs", max_size_mb=10, max_files=5):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.max_size = max_size_mb * 1024 * 1024  # 转换为字节
        self.max_files = max_files
        self.current_file = None
    
    def _get_log_filename(self):
        return self.log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    
    def _rotate_if_needed(self):
        log_file = self._get_log_filename()
        if log_file.exists() and log_file.stat().st_size > self.max_size:
            # 重命名当前文件
            timestamp = datetime.now().strftime('%H%M%S')
            rotated_name = self.log_dir / f"app_{datetime.now().strftime('%Y%m%d')}_{timestamp}.log"
            log_file.rename(rotated_name)
            
            # 清理旧文件
            self._cleanup_old_files()
    
    def _cleanup_old_files(self):
        log_files = sorted(self.log_dir.glob("app_*.log"), key=lambda x: x.stat().st_mtime)
        while len(log_files) > self.max_files:
            oldest = log_files.pop(0)
            oldest.unlink()
    
    def log(self, level, message, **kwargs):
        self._rotate_if_needed()
        log_file = self._get_log_filename()
        
        log_entry = {
            "time": datetime.now().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    def info(self, message, **kwargs):
        self.log("INFO", message, **kwargs)
    
    def error(self, message, **kwargs):
        self.log("ERROR", message, **kwargs)
```