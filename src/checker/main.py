#!/usr/bin/env python3
"""
Markdown链接检查器
检查项目中所有markdown文件的链接是否正确
"""

import re
import os
from pathlib import Path
from typing import List, Tuple, Set
import argparse


class MarkdownLinkChecker:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.errors: List[Tuple[str, str, str]] = []  # (file, link, error)
        self.checked_files: Set[str] = set()
        
    def find_markdown_files(self) -> List[Path]:
        """递归查找所有markdown文件"""
        md_files = []
        for file_path in self.root_dir.rglob("*.md"):
            if file_path.is_file():
                md_files.append(file_path)
        return md_files
    
    def extract_links(self, content: str) -> List[str]:
        """从markdown内容中提取所有链接"""
        # 匹配 [text](url) 格式的链接
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(pattern, content)
        return [url for text, url in matches]
    
    def resolve_relative_link(self, base_file: Path, link: str) -> Path:
        """解析相对路径链接"""
        # 移除锚点（如#section）
        link_without_anchor = link.split('#')[0]
        
        # 处理空链接
        if not link_without_anchor:
            return base_file.parent
        
        # 解析相对路径
        resolved_path = (base_file.parent / link_without_anchor).resolve()
        
        # 确保路径在项目根目录内
        try:
            resolved_path.relative_to(self.root_dir)
            return resolved_path
        except ValueError:
            # 路径超出项目根目录，返回原路径
            return resolved_path
    
    def check_local_link(self, base_file: Path, link: str) -> Tuple[bool, str]:
        """检查本地文件链接"""
        # 跳过HTTP链接
        if link.startswith(('http://', 'https://', 'mailto:', 'ftp://')):
            return True, "HTTP link (skipped)"
        
        # 跳过锚点链接
        if link.startswith('#'):
            return True, "Anchor link (skipped)"
        
        # 解析相对路径
        resolved_path = self.resolve_relative_link(base_file, link)
        
        # 检查文件是否存在
        if resolved_path.exists():
            return True, "OK"
        else:
            return False, f"File not found: {resolved_path}"
    
    def check_file(self, file_path: Path):
        """检查单个文件的链接"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.errors.append((str(file_path), "", f"Failed to read file: {e}"))
            return
        
        links = self.extract_links(content)
        
        for link in links:
            is_valid, message = self.check_local_link(file_path, link)
            if not is_valid:
                self.errors.append((str(file_path), link, message))
        
        self.checked_files.add(str(file_path))
    
    def check_all(self):
        """检查所有markdown文件"""
        md_files = self.find_markdown_files()
        
        for file_path in md_files:
            self.check_file(file_path)
    
    def report(self):
        """生成检查报告"""
        print(f"检查了 {len(self.checked_files)} 个markdown文件")
        print(f"发现 {len(self.errors)} 个错误\n")
        
        if self.errors:
            print("错误详情:")
            print("-" * 80)
            
            for file_path, link, error in self.errors:
                print(f"文件: {file_path}")
                if link:
                    print(f"链接: [{link}]")
                print(f"错误: {error}")
                print("-" * 80)
            
            return False
        else:
            print("✓ 所有链接检查通过!")
            return True


def main():
    parser = argparse.ArgumentParser(description='检查markdown文件中的链接')
    parser.add_argument('directory', nargs='?', default='.', help='要检查的目录（默认为当前目录）')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    args = parser.parse_args()
    
    checker = MarkdownLinkChecker(args.directory)
    checker.check_all()
    
    if args.verbose:
        print("\n检查的文件:")
        for file in sorted(checker.checked_files):
            print(f"  {file}")
        print()
    
    success = checker.report()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()