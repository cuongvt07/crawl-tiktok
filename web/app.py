import os
import time
import shutil
import json
import io
import zipfile
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template, send_file
from TiktokCrawler.downloader import download_video, get_video_info, download_user_videos

app = Flask(__name__)

# Disable caching completely
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Thư mục lưu video tải về
DOWNLOADS_DIR = os.path.join(os.getcwd(), "downloads")
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

@app.after_request
def after_request(response):
    """Disable caching for all responses"""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
    response.headers['Expires'] = '0'
    response.headers['Pragma'] = 'no-cache'
    # Add CORS headers
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/downloads/<path:filename>')
def download_file(filename):
    """Serve downloaded files"""
    return send_from_directory(DOWNLOADS_DIR, filename, as_attachment=True)

@app.route('/api/download', methods=['POST'])
def api_download():
    """API endpoint để tải video"""
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'message': 'Dữ liệu không hợp lệ'
        })

    url = data.get('url', '').strip()
    proxy = data.get('proxy', '').strip() or None
    custom_dir = data.get('customDir', '').strip()
    limit = data.get('limit')
    
    if not url:
        return jsonify({
            'success': False,
            'message': 'URL không được để trống'
        })

    try:
        # Convert limit to int if provided
        if limit:
            try:
                limit = int(limit)
                if limit < 1:
                    return jsonify({
                        'success': False,
                        'message': 'Số lượng video phải lớn hơn 0'
                    })
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Số lượng video không hợp lệ'
                })

        # Sử dụng thư mục tùy chỉnh nếu được cung cấp
        output_dir = DOWNLOADS_DIR

        # Kiểm tra nếu là URL user hay video đơn lẻ
        if '@' in url and not url.endswith('/video/'):
            success, message = download_user_videos(url, proxy, limit, output_dir)
        else:
            success, message = download_video(url, proxy, output_dir, limit)

        if success:
            return jsonify({
                'success': True,
                'message': message,
                'localPath': output_dir
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        })

@app.route('/api/info', methods=['POST'])
def api_info():
    """API endpoint để lấy thông tin video"""
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'message': 'Dữ liệu không hợp lệ'
        })

    url = data.get('url', '').strip()
    proxy = data.get('proxy', '').strip() or None
    
    if not url:
        return jsonify({
            'success': False,
            'message': 'URL không được để trống'
        })

    try:
        success, info = get_video_info(url, proxy)
        return jsonify({
            'success': success,
            'info': info if success else None,
            'message': None if success else info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        })

@app.route('/api/user-videos', methods=['POST'])
def api_user_videos():
    """API endpoint để tải video từ user"""
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'message': 'Dữ liệu không hợp lệ'
        })

    url = data.get('url', '').strip()
    proxy = data.get('proxy', '').strip() or None
    limit = data.get('limit')
    custom_dir = data.get('customDir', '').strip()
    
    if not url:
        return jsonify({
            'success': False,
            'message': 'URL không được để trống'
        })

    try:
        # Convert limit to int if provided
        if limit:
            try:
                limit = int(limit)
                if limit < 1:
                    return jsonify({
                        'success': False,
                        'message': 'Số lượng video phải lớn hơn 0'
                    })
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Số lượng video không hợp lệ'
                })

        # Sử dụng thư mục tùy chỉnh nếu được cung cấp
        output_dir = custom_dir if custom_dir else DOWNLOADS_DIR

        success, message = download_user_videos(url, proxy, limit, output_dir)

        if success:
            # Lấy danh sách file đã tải
            files = []
            if os.path.exists(output_dir):
                files = [f for f in os.listdir(output_dir) if f.endswith('.mp4')]
            
            return jsonify({
                'success': True,
                'message': message,
                'download_location': output_dir,
                'files': files
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        })

@app.route('/api/list-downloads')
def api_list_downloads():
    """API endpoint để liệt kê các file đã tải"""
    try:
        files = []
        if os.path.exists(DOWNLOADS_DIR):
            for filename in os.listdir(DOWNLOADS_DIR):
                file_path = os.path.join(DOWNLOADS_DIR, filename)
                if os.path.isfile(file_path):
                    stats = os.stat(file_path)
                    files.append({
                        'name': filename,
                        'size': _human_readable_size(stats.st_size),
                        'date': time.strftime('%Y-%m-%d %H:%M', time.localtime(stats.st_mtime)),
                        'url': f'/downloads/{filename}'
                    })
        
        # Sắp xếp theo thời gian mới nhất
        files.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        })

@app.route('/api/delete-file', methods=['POST'])
def api_delete_file():
    """API endpoint để xóa file"""
    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'message': 'Dữ liệu không hợp lệ'
        })

    filename = data.get('filename')
    if not filename:
        return jsonify({
            'success': False,
            'message': 'Tên file không được để trống'
        })

    try:
        file_path = os.path.join(DOWNLOADS_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({
                'success': True,
                'message': f'Đã xóa file {filename}'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'File {filename} không tồn tại'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        })

@app.route('/api/delete-all', methods=['POST'])
def api_delete_all():
    """API endpoint để xóa tất cả file"""
    try:
        if os.path.exists(DOWNLOADS_DIR):
            for filename in os.listdir(DOWNLOADS_DIR):
                file_path = os.path.join(DOWNLOADS_DIR, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': 'Đã xóa tất cả file'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        })

@app.route('/api/cleanup-non-mp4', methods=['POST'])
def api_cleanup_non_mp4():
    """API endpoint để xóa các file không phải MP4"""
    try:
        if os.path.exists(DOWNLOADS_DIR):
            deleted_count = 0
            for filename in os.listdir(DOWNLOADS_DIR):
                file_path = os.path.join(DOWNLOADS_DIR, filename)
                if os.path.isfile(file_path) and not filename.lower().endswith('.mp4'):
                    os.remove(file_path)
                    deleted_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Đã xóa {deleted_count} file không phải MP4'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        })

@app.route("/download-zip")
def download_zip():
    """Tải tất cả file dưới dạng ZIP"""
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename in os.listdir(DOWNLOADS_DIR):
            file_path = os.path.join(DOWNLOADS_DIR, filename)
            if os.path.isfile(file_path) and filename.lower().endswith('.mp4'):
                zipf.write(file_path, arcname=filename)
    memory_file.seek(0)
    return send_file(memory_file, mimetype='application/zip',
                     as_attachment=True, download_name='videos.zip')

def _human_readable_size(size_bytes):
    """Chuyển đổi kích thước file sang định dạng dễ đọc"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)