import os
from typing import List, Optional

# 工作区模型文件的命名约定：目录中包含这些文件之一即视为候选工作区
MODEL_FILES = [
    'm1-object-model.yaml',
    'm2-behavior-model.yaml',
    'm3-rule-model.yaml',
    'm4-scenario-model.yaml',
    'm5-actor-model.yaml',
    'me-event-model.yaml',
    'event-model.yaml'
]

# 扫描时跳过的目录
SKIP_DIRS = {'.git', '.svn', '.idea', '.vscode', 'node_modules', '.venv', 'venv',
             '__pycache__', 'dist', 'build', '.next', 'target', '.autoclaw', '.claude'}


class FileService:
    def read_file(self, file_path: str) -> Optional[str]:
        """读取文件内容"""
        try:
            if not os.path.exists(file_path):
                return None
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"读取文件失败: {file_path}, 错误: {str(e)}")
            return None
    
    def write_file(self, file_path: str, content: str) -> bool:
        """写入文件内容"""
        try:
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # 先写临时文件
            temp_path = f"{file_path}.tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 原子替换
            if os.path.exists(file_path):
                os.replace(temp_path, file_path)
            else:
                os.rename(temp_path, file_path)
            
            return True
        except Exception as e:
            print(f"写入文件失败: {file_path}, 错误: {str(e)}")
            return False
    
    def check_directory(self, directory: str) -> bool:
        """检查目录是否存在"""
        return os.path.exists(directory) and os.path.isdir(directory)

    def list_yaml_files(self, directory: str) -> List[str]:
        """列出目录下（不递归）所有 .yaml/.yml 文件"""
        if not self.check_directory(directory):
            return []
        return sorted([
            f for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(('.yaml', '.yml'))
        ])

    def scan_workspace_directories(self, root_dir: str, max_depth: int = 4) -> List[dict]:
        """扫描目录树，找出包含模型 YAML 文件的候选工作区目录。"""
        results: List[dict] = []
        if not self.check_directory(root_dir):
            return results

        root_dir = os.path.abspath(root_dir)
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # 计算相对深度，超过限制则不再深入
            rel = os.path.relpath(dirpath, root_dir)
            depth = 0 if rel == '.' else rel.count(os.sep) + 1
            if depth > max_depth:
                dirnames[:] = []
                continue

            # 跳过无关目录
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

            found = [f for f in MODEL_FILES if f in filenames]
            if found:
                results.append({
                    'directory': dirpath,
                    'name': os.path.basename(dirpath) or dirpath,
                    'files': found,
                })

        results.sort(key=lambda r: (r['name'].lower(), r['directory'].lower()))
        return results
