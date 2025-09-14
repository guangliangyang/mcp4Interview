"""
文件管理工具
处理简历、求职信、附件等文件操作
"""

import os
import shutil
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import aiofiles
import logging

from src.utils.logger import get_logger

logger = get_logger(__name__)

class FileManager:
    """文件管理器"""

    def __init__(self, base_dir: str = "data/files"):
        self.base_dir = Path(base_dir)
        self.resumes_dir = self.base_dir / "resumes"
        self.cover_letters_dir = self.base_dir / "cover_letters"
        self.attachments_dir = self.base_dir / "attachments"
        self.temp_dir = self.base_dir / "temp"

        # 创建目录
        self._create_directories()

        # 支持的文件类型
        self.supported_resume_formats = {'.pdf', '.doc', '.docx'}
        self.supported_attachment_formats = {'.pdf', '.doc', '.docx', '.txt', '.png', '.jpg', '.jpeg'}

    def _create_directories(self):
        """创建必要的目录"""
        try:
            for directory in [self.resumes_dir, self.cover_letters_dir,
                            self.attachments_dir, self.temp_dir]:
                directory.mkdir(parents=True, exist_ok=True)

            logger.info("文件管理目录创建完成")

        except Exception as e:
            logger.error(f"创建文件管理目录失败: {e}")
            raise

    async def save_resume(self, file_path: str, user_id: str,
                         resume_name: str = None) -> Dict:
        """保存简历文件

        Args:
            file_path: 原始文件路径
            user_id: 用户ID
            resume_name: 简历名称

        Returns:
            保存的文件信息
        """
        try:
            original_path = Path(file_path)

            # 验证文件存在
            if not original_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")

            # 验证文件格式
            file_extension = original_path.suffix.lower()
            if file_extension not in self.supported_resume_formats:
                raise ValueError(f"不支持的简历格式: {file_extension}")

            # 生成文件名
            if not resume_name:
                resume_name = original_path.stem

            # 计算文件哈希
            file_hash = await self._calculate_file_hash(file_path)

            # 生成保存路径
            saved_filename = f"{user_id}_{resume_name}_{file_hash[:8]}{file_extension}"
            saved_path = self.resumes_dir / saved_filename

            # 复制文件
            shutil.copy2(file_path, saved_path)

            # 获取文件信息
            file_info = await self._get_file_info(saved_path)
            file_info.update({
                'user_id': user_id,
                'resume_name': resume_name,
                'file_hash': file_hash,
                'saved_path': str(saved_path),
                'relative_path': str(saved_path.relative_to(self.base_dir))
            })

            logger.info(f"简历文件保存成功: {saved_filename}")
            return file_info

        except Exception as e:
            logger.error(f"保存简历文件失败: {e}")
            raise

    async def save_cover_letter(self, content: str, job_id: str,
                              user_id: str, format_type: str = 'txt') -> Dict:
        """保存求职信

        Args:
            content: 求职信内容
            job_id: 职位ID
            user_id: 用户ID
            format_type: 文件格式 ('txt', 'html', 'pdf')

        Returns:
            保存的文件信息
        """
        try:
            # 生成文件名
            filename = f"{user_id}_{job_id}_cover_letter.{format_type}"
            file_path = self.cover_letters_dir / filename

            # 保存内容
            if format_type == 'txt':
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(content)
            elif format_type == 'html':
                html_content = self._text_to_html(content)
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(html_content)
            else:
                raise ValueError(f"不支持的格式: {format_type}")

            # 获取文件信息
            file_info = await self._get_file_info(file_path)
            file_info.update({
                'user_id': user_id,
                'job_id': job_id,
                'content_preview': content[:200],
                'saved_path': str(file_path),
                'relative_path': str(file_path.relative_to(self.base_dir))
            })

            logger.info(f"求职信保存成功: {filename}")
            return file_info

        except Exception as e:
            logger.error(f"保存求职信失败: {e}")
            raise

    async def save_attachment(self, file_path: str, user_id: str,
                            attachment_type: str = 'other') -> Dict:
        """保存附件

        Args:
            file_path: 原始文件路径
            user_id: 用户ID
            attachment_type: 附件类型

        Returns:
            保存的文件信息
        """
        try:
            original_path = Path(file_path)

            # 验证文件
            if not original_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")

            file_extension = original_path.suffix.lower()
            if file_extension not in self.supported_attachment_formats:
                raise ValueError(f"不支持的附件格式: {file_extension}")

            # 生成保存路径
            file_hash = await self._calculate_file_hash(file_path)
            saved_filename = f"{user_id}_{attachment_type}_{file_hash[:8]}{file_extension}"
            saved_path = self.attachments_dir / saved_filename

            # 复制文件
            shutil.copy2(file_path, saved_path)

            # 获取文件信息
            file_info = await self._get_file_info(saved_path)
            file_info.update({
                'user_id': user_id,
                'attachment_type': attachment_type,
                'file_hash': file_hash,
                'saved_path': str(saved_path),
                'relative_path': str(saved_path.relative_to(self.base_dir))
            })

            logger.info(f"附件保存成功: {saved_filename}")
            return file_info

        except Exception as e:
            logger.error(f"保存附件失败: {e}")
            raise

    async def get_user_files(self, user_id: str, file_type: str = 'all') -> List[Dict]:
        """获取用户文件列表

        Args:
            user_id: 用户ID
            file_type: 文件类型 ('resumes', 'cover_letters', 'attachments', 'all')

        Returns:
            文件信息列表
        """
        try:
            files = []

            if file_type in ['resumes', 'all']:
                files.extend(await self._get_directory_files(self.resumes_dir, user_id))

            if file_type in ['cover_letters', 'all']:
                files.extend(await self._get_directory_files(self.cover_letters_dir, user_id))

            if file_type in ['attachments', 'all']:
                files.extend(await self._get_directory_files(self.attachments_dir, user_id))

            # 按修改时间排序
            files.sort(key=lambda x: x['modified_time'], reverse=True)

            logger.debug(f"获取用户文件: {len(files)} 个文件")
            return files

        except Exception as e:
            logger.error(f"获取用户文件失败: {e}")
            return []

    async def delete_file(self, file_path: str) -> bool:
        """删除文件

        Args:
            file_path: 文件路径

        Returns:
            是否删除成功
        """
        try:
            path = Path(file_path)

            # 验证文件在管理目录内
            if not self._is_managed_file(path):
                raise ValueError("只能删除管理目录内的文件")

            if path.exists():
                path.unlink()
                logger.info(f"文件删除成功: {file_path}")
                return True
            else:
                logger.warning(f"文件不存在: {file_path}")
                return False

        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False

    async def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """清理临时文件

        Args:
            max_age_hours: 最大保留时间（小时）

        Returns:
            清理的文件数量
        """
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600

            cleaned_count = 0

            for file_path in self.temp_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        cleaned_count += 1

            logger.info(f"清理临时文件完成: {cleaned_count} 个文件")
            return cleaned_count

        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
            return 0

    async def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件MD5哈希"""
        hash_md5 = hashlib.md5()

        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    async def _get_file_info(self, file_path: Path) -> Dict:
        """获取文件详细信息"""
        stat = file_path.stat()

        return {
            'filename': file_path.name,
            'size': stat.st_size,
            'size_human': self._format_file_size(stat.st_size),
            'created_time': stat.st_ctime,
            'modified_time': stat.st_mtime,
            'mime_type': mimetypes.guess_type(str(file_path))[0],
            'extension': file_path.suffix.lower()
        }

    async def _get_directory_files(self, directory: Path, user_id: str) -> List[Dict]:
        """获取目录下用户的文件"""
        files = []

        if not directory.exists():
            return files

        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.name.startswith(f"{user_id}_"):
                file_info = await self._get_file_info(file_path)
                file_info.update({
                    'full_path': str(file_path),
                    'relative_path': str(file_path.relative_to(self.base_dir)),
                    'directory_type': directory.name
                })
                files.append(file_info)

        return files

    def _is_managed_file(self, file_path: Path) -> bool:
        """检查是否为管理目录内的文件"""
        try:
            file_path.relative_to(self.base_dir)
            return True
        except ValueError:
            return False

    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)

        return f"{s} {size_names[i]}"

    def _text_to_html(self, text: str) -> str:
        """将纯文本转换为HTML格式"""
        # 简单的文本到HTML转换
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Cover Letter</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }}
        .content {{ max-width: 800px; }}
    </style>
</head>
<body>
    <div class="content">
        {text.replace('\n\n', '</p><p>').replace('\n', '<br>')}
    </div>
</body>
</html>"""

        return html_content.replace(text, f"<p>{text}</p>")

if __name__ == "__main__":
    async def test_file_manager():
        """测试文件管理器"""
        file_manager = FileManager("test_data/files")

        # 测试保存求职信
        cover_letter_content = """
Dear Hiring Manager,

I am writing to express my interest in the Software Engineer position at your company.
My experience in Python development and passion for innovation make me an ideal candidate.

Best regards,
John Doe
        """.strip()

        cover_letter_info = await file_manager.save_cover_letter(
            content=cover_letter_content,
            job_id="job_123",
            user_id="user_456"
        )

        print("Cover Letter Info:", cover_letter_info)

        # 测试获取用户文件
        user_files = await file_manager.get_user_files("user_456")
        print("User Files:", user_files)

        # 清理测试文件
        await file_manager.cleanup_temp_files()

        print("文件管理器测试完成")

    import asyncio
    asyncio.run(test_file_manager())