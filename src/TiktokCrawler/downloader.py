import os
import sys
import platform
import shutil
import subprocess
import yt_dlp
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

DOWNLOADS_DIR = "downloads"
console = Console()

def get_ffmpeg_path():
    """
    Tìm đường dẫn ffmpeg trong hệ thống theo thứ tự ưu tiên:
    1. Biến môi trường FFMPEG_PATH
    2. Trong PATH của hệ thống
    3. Các vị trí thông dụng
    """
    # 1. Kiểm tra biến môi trường FFMPEG_PATH
    ffmpeg_env = os.getenv('FFMPEG_PATH')
    if ffmpeg_env and os.path.isfile(ffmpeg_env):
        return ffmpeg_env

    # 2. Tìm trong PATH của hệ thống
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return ffmpeg_path

    # 3. Tìm trong các vị trí cụ thể
    possible_paths = []
    
    # Thêm thư mục hiện tại và các thư mục con
    binary_name = 'ffmpeg.exe' if platform.system() == 'Windows' else 'ffmpeg'
    possible_paths.extend([
        os.path.join(os.getcwd(), binary_name),
        os.path.join(os.getcwd(), 'ffmpeg', 'bin', binary_name),
        os.path.join(os.getcwd(), 'bin', binary_name),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), binary_name),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg', 'bin', binary_name),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ffmpeg', 'bin', binary_name),
    ])

    if platform.system() == 'Windows':
        # Đường dẫn Windows
        possible_paths.extend([
            r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe',
            os.path.join(os.path.expanduser('~'), 'ffmpeg', 'bin', 'ffmpeg.exe'),
            os.path.join(os.path.expanduser('~'), 'Downloads', 'ffmpeg', 'bin', 'ffmpeg.exe'),
            os.path.join(os.path.expanduser('~'), 'Downloads', 'ffmpeg-*', 'bin', 'ffmpeg.exe'),  # Cho thư mục với version
        ])
        
        # Tìm trong Downloads với pattern ffmpeg-*
        downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        if os.path.exists(downloads_dir):
            for item in os.listdir(downloads_dir):
                if item.startswith('ffmpeg-') and os.path.isdir(os.path.join(downloads_dir, item)):
                    possible_paths.append(os.path.join(downloads_dir, item, 'bin', 'ffmpeg.exe'))
    else:
        # Đường dẫn Linux/MacOS
        possible_paths.extend([
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            '/opt/homebrew/bin/ffmpeg',
            '/usr/local/ffmpeg/bin/ffmpeg',
            os.path.join(os.path.expanduser('~'), 'ffmpeg', 'ffmpeg'),
            os.path.join(os.path.expanduser('~'), '.local', 'bin', 'ffmpeg'),
        ])
    
    # Kiểm tra từng đường dẫn
    for path in possible_paths:
        if os.path.isfile(path):
            return path

    # Thử chạy lệnh ffmpeg để kiểm tra
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, 
                              text=True)
        if result.returncode == 0:
            return 'ffmpeg'
    except:
        pass
            
    return None

def _ensure_ffmpeg():
    """
    Kiểm tra và đảm bảo ffmpeg được cài đặt 
    """
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        console.print("[red]LỖI: Không tìm thấy ffmpeg trong hệ thống![/red]")
        console.print("[yellow]Hướng dẫn cài đặt ffmpeg:[/yellow]")
        if platform.system() == 'Windows':
            console.print("1. Tải ffmpeg từ: https://www.gyan.dev/ffmpeg/builds/")
            console.print("2. Giải nén và đặt thư mục 'ffmpeg' vào cùng thư mục với chương trình")
            console.print("   HOẶC thêm đường dẫn ffmpeg vào biến môi trường PATH")
        elif platform.system() == 'Linux':
            console.print("Chạy lệnh: sudo apt-get install ffmpeg")
        else:  # MacOS
            console.print("Chạy lệnh: brew install ffmpeg")
        console.print("\nSau khi cài đặt, vui lòng chạy lại chương trình!")
        return None
    return ffmpeg_path

def _get_ydl_opts(proxy: str = None, download: bool = True, output_dir: str = DOWNLOADS_DIR):
    """Cấu hình yt-dlp để chỉ tải video MP4"""
    # Đảm bảo ffmpeg được cài đặt
    ffmpeg_path = _ensure_ffmpeg()
    if not ffmpeg_path:
        return None
        
    ydl_opts = {
        # Format chỉ định rõ ràng chỉ lấy MP4
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
        'noplaylist': True,
        'writedescription': False,
        'writeinfojson': False,
        'writesubtitles': False,
        'writeannotations': False,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        
        # Đảm bảo output là MP4
        'merge_output_format': 'mp4',
        'remux_video': 'mp4',
        'keepvideo': False,  # Không giữ video gốc sau khi merge
        
        # Chỉ định đường dẫn ffmpeg
        'ffmpeg_location': ffmpeg_path,
        
        # Tên file output
        'outtmpl': {
            'default': os.path.join(output_dir, '%(title).50s_%(id)s.%(ext)s')
        },
        
        # TikTok specific settings
        'extractor_args': {
            'TikTok': {
                'download_without_watermark': True,
            }
        },
        
        # Post-processing để đảm bảo MP4
        'postprocessors': [
            {
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            }
        ],
    }

    if not download:
        ydl_opts['simulate'] = True
        ydl_opts['skip_download'] = True

    if proxy:
        ydl_opts['proxy'] = proxy

    return ydl_opts

def _clean_non_mp4_files(directory):
    """Xóa tất cả các tệp không phải MP4"""
    try:
        if not os.path.exists(directory):
            return
            
        for file in os.listdir(directory):
            full_path = os.path.join(directory, file)
            if os.path.isfile(full_path) and not file.lower().endswith('.mp4'):
                try:
                    os.remove(full_path)
                    console.print(f"[yellow]Đã xóa tệp phụ: {file}[/yellow]")
                except OSError as e:
                    console.print(f"[red]Không thể xóa {file}: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Lỗi khi dọn dẹp tệp: {e}[/red]")

def _verify_mp4_files(directory):
    """Kiểm tra và đổi tên các file thành .mp4 nếu cần"""
    try:
        if not os.path.exists(directory):
            return
            
        for file in os.listdir(directory):
            full_path = os.path.join(directory, file)
            if os.path.isfile(full_path) and not file.lower().endswith('.mp4'):
                # Đổi tên thành .mp4 nếu là file video
                name, ext = os.path.splitext(file)
                if ext.lower() in ['.webm', '.mkv', '.m4v', '.mov']:
                    new_name = f"{name}.mp4"
                    new_path = os.path.join(directory, new_name)
                    try:
                        os.rename(full_path, new_path)
                        console.print(f"[green]Đã đổi tên: {file} -> {new_name}[/green]")
                    except OSError as e:
                        console.print(f"[red]Không thể đổi tên {file}: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Lỗi khi kiểm tra file MP4: {e}[/red]")

def download_video(url: str, proxy: str = None, output_dir: str = DOWNLOADS_DIR, limit: int = None) -> tuple[bool, str]:
    """
    Tải video TikTok dưới định dạng MP4
    
    Args:
        url: URL của video TikTok
        proxy: Proxy tùy chọn
        output_dir: Thư mục lưu video
        limit: Số lượng video tối đa (không áp dụng cho video đơn)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        console.print(f"[blue]Đang tải video: {url}[/blue]")
        if proxy:
            console.print(f"[blue]Sử dụng proxy: {proxy}[/blue]")

        # Kiểm tra và lấy cấu hình ffmpeg
        ydl_opts = _get_ydl_opts(proxy=proxy, download=True, output_dir=output_dir)
        if not ydl_opts:
            return False, "Chưa cài đặt ffmpeg. Vui lòng cài đặt ffmpeg theo hướng dẫn và thử lại."

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Lấy thông tin video trước
            info = ydl.extract_info(url, download=False)
            if not info:
                return False, "Không thể lấy thông tin video"
            
            video_title = info.get('title', 'Unknown')
            console.print(f"[cyan]Đã tìm thấy video: {video_title}[/cyan]")
            
            # Tải video
            ydl.download([url])
            
            # Kiểm tra và đảm bảo file là MP4
            _verify_mp4_files(output_dir)
            _clean_non_mp4_files(output_dir)
            
            # Kiểm tra xem có file MP4 nào được tạo không
            mp4_files = [f for f in os.listdir(output_dir) if f.lower().endswith('.mp4')]
            if mp4_files:
                latest_file = max(mp4_files, key=lambda x: os.path.getctime(os.path.join(output_dir, x)))
                console.print(f"[green]Tải thành công: {latest_file}[/green]")
                return True, f"Tải video thành công: {latest_file}"
            else:
                return False, "Không tìm thấy file MP4 sau khi tải"

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        console.print(f"[red]Lỗi tải video: {error_msg}[/red]")
        
        if any(keyword in error_msg.lower() for keyword in ["blocked", "timed out", "403", "404"]):
            return False, "IP bị chặn hoặc video không khả dụng. Thử sử dụng proxy."
        return False, f"Lỗi tải video: {error_msg}"
        
    except Exception as e:
        msg = f"Lỗi không mong muốn: {e}"
        console.print(f"[red]{msg}[/red]")
        return False, msg

def get_video_info(url: str, proxy: str = None) -> tuple[bool, str]:
    """Lấy thông tin video TikTok"""
    try:
        console.print(f"[blue]Đang lấy thông tin video: {url}[/blue]")
        if proxy:
            console.print(f"[blue]Sử dụng proxy: {proxy}[/blue]")

        # Kiểm tra và lấy cấu hình ffmpeg
        ydl_opts = _get_ydl_opts(proxy=proxy, download=False)
        if not ydl_opts:
            return False, "Chưa cài đặt ffmpeg. Vui lòng cài đặt ffmpeg theo hướng dẫn và thử lại."

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                # Format thông tin video
                info_text = (
                    f"Tiêu đề: {info.get('title', 'N/A')}\n"
                    f"Tác giả: {info.get('uploader', 'N/A')}\n"
                    f"Ngày tải: {info.get('upload_date', 'N/A')}\n"
                    f"Thời lượng: {info.get('duration_string', 'N/A')}\n"
                    f"Lượt xem: {info.get('view_count', 'N/A')}\n"
                    f"Lượt thích: {info.get('like_count', 'N/A')}\n"
                    f"Bình luận: {info.get('comment_count', 'N/A')}\n"
                    f"URL: {info.get('webpage_url', 'N/A')}"
                )
                
                console.print(Panel(
                    Text(info_text, justify="left"),
                    title="[bold blue]Thông tin Video[/bold blue]",
                    border_style="blue"
                ))
                return True, info_text
            else:
                return False, "Không thể lấy thông tin video"

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        console.print(f"[red]Lỗi lấy thông tin: {error_msg}[/red]")
        
        if any(keyword in error_msg.lower() for keyword in ["blocked", "timed out", "403", "404"]):
            return False, "IP bị chặn hoặc video không khả dụng. Thử sử dụng proxy."
        return False, f"Lỗi: {error_msg}"
        
    except Exception as e:
        msg = f"Lỗi không mong muốn: {e}"
        console.print(f"[red]{msg}[/red]")
        return False, msg

def download_user_videos(user_url: str, proxy: str = None, limit: int = None, output_dir: str = DOWNLOADS_DIR) -> tuple[bool, str]:
    """
    Tải video từ user TikTok (chỉ định dạng MP4)
    
    Args:
        user_url: URL của user TikTok
        proxy: Proxy tùy chọn
        limit: Số lượng video tối đa
        output_dir: Thư mục lưu video
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        console.print(f"[blue]Đang tải video từ user: {user_url}[/blue]")
        if limit:
            console.print(f"[blue]Giới hạn: {limit} video mới nhất[/blue]")
        if proxy:
            console.print(f"[blue]Sử dụng proxy: {proxy}[/blue]")

        ydl_opts = _get_ydl_opts(proxy=proxy, download=True, output_dir=output_dir)
        
        # Cấu hình cho playlist
        ydl_opts['noplaylist'] = False
        if limit and isinstance(limit, int) and limit > 0:
            ydl_opts['playlistend'] = limit
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Lấy thông tin user trước
            info = ydl.extract_info(user_url, download=False)
            if not info:
                return False, "Không thể lấy thông tin user"
            
            if 'entries' not in info or not info['entries']:
                return False, "Không tìm thấy video nào từ user này"
            
            total_videos = len(info['entries'])
            download_count = min(limit, total_videos) if limit else total_videos
            
            console.print(f"[cyan]Tìm thấy {total_videos} video từ {info.get('uploader', 'N/A')}[/cyan]")
            console.print(f"[cyan]Sẽ tải {download_count} video...[/cyan]")
            
            # Đếm file MP4 trước khi tải
            initial_mp4_count = len([f for f in os.listdir(output_dir) if f.lower().endswith('.mp4')])
            
            # Tải video
            ydl.download([user_url])
            
            # Kiểm tra và đảm bảo tất cả file là MP4
            _verify_mp4_files(output_dir)
            _clean_non_mp4_files(output_dir)
            
            # Đếm file MP4 sau khi tải
            final_mp4_count = len([f for f in os.listdir(output_dir) if f.lower().endswith('.mp4')])
            actual_downloaded = final_mp4_count - initial_mp4_count
            
            if actual_downloaded > 0:
                console.print(f"[green]Tải thành công {actual_downloaded} video MP4 vào {output_dir}[/green]")
                return True, f"Đã tải {actual_downloaded} video MP4 thành công"
            else:
                return False, "Không có video MP4 nào được tải về"

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        console.print(f"[red]Lỗi tải video user: {error_msg}[/red]")
        
        if any(keyword in error_msg.lower() for keyword in ["blocked", "timed out", "403", "404"]):
            return False, "IP bị chặn hoặc user không khả dụng. Thử sử dụng proxy."
        return False, f"Lỗi: {error_msg}"
        
    except Exception as e:
        msg = f"Lỗi không mong muốn: {e}"
        console.print(f"[red]{msg}[/red]")
        return False, msg

def get_mp4_files_only(directory: str) -> list:
    """Lấy danh sách chỉ các file MP4 trong thư mục"""
    try:
        if not os.path.exists(directory):
            return []
        return [f for f in os.listdir(directory) if f.lower().endswith('.mp4') and os.path.isfile(os.path.join(directory, f))]
    except Exception:
        return []