import os
import time
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
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
    return response

@app.route('/')
def index():
    """Serve the main HTML page"""
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikTok Crawler - Web Interface</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {
            background-color: #f0f2f5;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding-bottom: 50px;
        }
        .navbar {
            background-color: #000000;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .navbar-brand {
            font-weight: bold;
            color: #ff0050 !important;
        }
        .card {
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
            border: none;
        }
        .card-header {
            background-color: #ffffff;
            border-bottom: 1px solid #f0f0f0;
            font-weight: bold;
            border-radius: 10px 10px 0 0 !important;
        }
        .btn-primary {
            background-color: #ff0050;
            border-color: #ff0050;
        }
        .btn-primary:hover {
            background-color: #d10045;
            border-color: #d10045;
        }
        .btn-outline-primary {
            color: #ff0050;
            border-color: #ff0050;
        }
        .btn-outline-primary:hover {
            background-color: #ff0050;
            border-color: #ff0050;
        }
        .form-control:focus {
            border-color: #ff0050;
            box-shadow: 0 0 0 0.25rem rgba(255, 0, 80, 0.25);
        }
        .loader {
            display: none;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #ff0050;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin-left: 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .video-preview {
            max-width: 100%;
            border-radius: 5px;
            margin-top: 20px;
        }
        #videoPreviewContainer {
            display: none;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark mb-4">
        <div class="container">
            <a class="navbar-brand" href="#"><i class="fab fa-tiktok me-2"></i>TikTok Crawler</a>
        </div>
    </nav>

    <div class="container">
        <div class="row justify-content-center">
            <div class="col-lg-8">
                <div class="card">
                    <div class="card-header">
                        <ul class="nav nav-tabs card-header-tabs" role="tablist">
                            <li class="nav-item" role="presentation">
                                <button class="nav-link active" id="download-tab" data-bs-toggle="tab" data-bs-target="#download" type="button" role="tab">Download Video</button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="info-tab" data-bs-toggle="tab" data-bs-target="#info" type="button" role="tab">Video Info</button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="user-videos-tab" data-bs-toggle="tab" data-bs-target="#user-videos" type="button" role="tab">User Videos</button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="downloads-tab" data-bs-toggle="tab" data-bs-target="#downloads" type="button" role="tab">Downloads</button>
                            </li>
                        </ul>
                    </div>
                    <div class="card-body">
                        <div class="tab-content">
                            <!-- Download Tab -->
                            <div class="tab-pane fade show active" id="download" role="tabpanel">
                                <h5 class="card-title mb-3">Download TikTok Video</h5>
                                <div class="form-floating mb-3">
                                    <input type="text" class="form-control" id="downloadUrl" placeholder="Enter TikTok video URL">
                                    <label for="downloadUrl">TikTok Video URL</label>
                                </div>
                                <div class="form-floating mb-3">
                                    <input type="text" class="form-control" id="downloadProxy" placeholder="(Optional) Proxy URL">
                                    <label for="downloadProxy">(Optional) Proxy</label>
                                </div>
                                <div class="mb-3">
                                    <label for="downloadCustomDir" class="form-label fw-bold text-primary">
                                        Thư mục tải về tùy chỉnh
                                    </label>
                                    <input type="text" class="form-control" id="downloadCustomDir" 
                                           placeholder="Nhập đường dẫn thư mục (để trống = mặc định)">
                                </div>
                                <div class="mb-3">
                                    <label for="downloadLimit" class="form-label fw-bold text-primary">
                                        Số lượng video tối đa
                                    </label>
                                    <input type="number" min="1" class="form-control" id="downloadLimit" 
                                           placeholder="Nhập số lượng video (để trống = tất cả)">
                                </div>
                                <div class="d-flex align-items-center">
                                    <button id="downloadBtn" class="btn btn-primary">
                                        <i class="fas fa-download me-2"></i>Download Video
                                    </button>
                                    <div id="downloadLoader" class="loader"></div>
                                </div>
                                <div id="downloadResult" class="mt-3"></div>
                                <div id="videoPreviewContainer" class="mt-3">
                                    <h5>Video Preview:</h5>
                                    <div class="ratio ratio-16x9">
                                        <video id="videoPreview" controls class="video-preview">
                                            Your browser does not support the video tag.
                                        </video>
                                    </div>
                                    <div class="d-grid gap-2 mt-3">
                                        <a id="downloadLink" class="btn btn-success" href="#" download>
                                            <i class="fas fa-download me-2"></i>Save Video
                                        </a>
                                    </div>
                                </div>
                            </div>

                            <!-- Video Info Tab -->
                            <div class="tab-pane fade" id="info" role="tabpanel">
                                <h5 class="card-title mb-3">Get TikTok Video Information</h5>
                                <div class="form-floating mb-3">
                                    <input type="text" class="form-control" id="infoUrl" placeholder="Enter TikTok video URL">
                                    <label for="infoUrl">TikTok Video URL</label>
                                </div>
                                <div class="form-floating mb-3">
                                    <input type="text" class="form-control" id="infoProxy" placeholder="(Optional) Proxy URL">
                                    <label for="infoProxy">(Optional) Proxy</label>
                                </div>
                                <div class="d-flex align-items-center">
                                    <button id="infoBtn" class="btn btn-primary">
                                        <i class="fas fa-info-circle me-2"></i>Get Information
                                    </button>
                                    <div id="infoLoader" class="loader"></div>
                                </div>
                                <div id="infoResult" class="mt-3"></div>
                            </div>

                            <!-- User Videos Tab -->
                            <div class="tab-pane fade" id="user-videos" role="tabpanel">
                                <h5 class="card-title mb-3">Download Videos from User</h5>
                                <div class="form-floating mb-3">
                                    <input type="text" class="form-control" id="userUrl" placeholder="Enter TikTok user URL">
                                    <label for="userUrl">TikTok User URL</label>
                                </div>
                                <div class="form-floating mb-3">
                                    <input type="text" class="form-control" id="userProxy" placeholder="(Optional) Proxy URL">
                                    <label for="userProxy">(Optional) Proxy</label>
                                </div>
                                <div class="mb-3">
                                    <label for="userLimit" class="form-label fw-bold text-primary">
                                        Số lượng video tối đa
                                    </label>
                                    <input type="number" min="1" class="form-control" id="userLimit" 
                                           placeholder="Nhập số lượng video (để trống = tất cả)">
                                </div>
                                <div class="mb-3">
                                    <label for="userCustomDir" class="form-label fw-bold text-primary">
                                        Thư mục tải về tùy chỉnh
                                    </label>
                                    <input type="text" class="form-control" id="userCustomDir" 
                                           placeholder="Nhập đường dẫn thư mục (để trống = mặc định)">
                                </div>
                                <div class="d-flex align-items-center">
                                    <button id="userVideosBtn" class="btn btn-primary">
                                        <i class="fas fa-user me-2"></i>Download User Videos
                                    </button>
                                    <div id="userVideosLoader" class="loader"></div>
                                </div>
                                <div id="userVideosResult" class="mt-3"></div>
                            </div>

                            <!-- Downloads Tab -->
                            <div class="tab-pane fade" id="downloads" role="tabpanel">
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <h5 class="card-title mb-0">Manage Downloads</h5>
                                    <button id="refreshDownloadsBtn" class="btn btn-outline-primary">
                                        <i class="fas fa-sync-alt"></i> Refresh
                                    </button>
                                </div>
                                <div class="table-responsive">
                                    <table class="table table-hover">
                                        <thead>
                                            <tr>
                                                <th>Filename</th>
                                                <th>Size</th>
                                                <th>Date</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody id="downloadsList">
                                            <tr>
                                                <td colspan="4" class="text-center">Click Refresh to load downloads...</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                                <div id="downloadsMessage"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Prevent multiple simultaneous requests
        let isLoading = false;

        document.addEventListener('DOMContentLoaded', function() {
            // Download Button
            document.getElementById('downloadBtn').addEventListener('click', handleDownload);
            document.getElementById('infoBtn').addEventListener('click', handleInfo);
            document.getElementById('userVideosBtn').addEventListener('click', handleUserVideos);
            document.getElementById('refreshDownloadsBtn').addEventListener('click', loadDownloads);
            
            // Tab switching
            document.querySelectorAll('[data-bs-toggle="tab"]').forEach(function(triggerEl) {
                triggerEl.addEventListener('click', function(event) {
                    if (this.getAttribute('data-bs-target') === '#downloads') {
                        setTimeout(loadDownloads, 100); // Small delay to ensure tab is active
                    }
                });
            });
        });

        function handleDownload() {
            if (isLoading) return;
            
            const url = document.getElementById('downloadUrl').value.trim();
            const proxy = document.getElementById('downloadProxy').value.trim();
            const customDir = document.getElementById('downloadCustomDir').value.trim();
            const limit = document.getElementById('downloadLimit').value.trim();
            
            if (!url) {
                showAlert('downloadResult', 'Vui lòng nhập URL TikTok video', 'danger');
                return;
            }
            
            isLoading = true;
            showLoader('downloadLoader', true);
            clearResults('downloadResult');
            hidePreview();
            
            const requestData = { url, proxy: proxy || null, customDir: customDir || null, limit: limit || null };
            
            fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            })
            .then(response => response.json())
            .then(data => {
                isLoading = false;
                showLoader('downloadLoader', false);
                
                if (data.success) {
                    showAlert('downloadResult', data.message, 'success');
                    
                    if (data.file_url) {
                        showPreview(data.file_url, data.filename);
                    }
                } else {
                    showAlert('downloadResult', data.message, 'danger');
                }
            })
            .catch(error => {
                isLoading = false;
                showLoader('downloadLoader', false);
                showAlert('downloadResult', 'Lỗi: ' + error.message, 'danger');
            });
        }

        function handleInfo() {
            if (isLoading) return;
            
            const url = document.getElementById('infoUrl').value.trim();
            const proxy = document.getElementById('infoProxy').value.trim();
            
            if (!url) {
                showAlert('infoResult', 'Vui lòng nhập URL TikTok video', 'danger');
                return;
            }
            
            isLoading = true;
            showLoader('infoLoader', true);
            clearResults('infoResult');
            
            fetch('/api/info', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, proxy: proxy || null })
            })
            .then(response => response.json())
            .then(data => {
                isLoading = false;
                showLoader('infoLoader', false);
                showAlert('infoResult', data.message, data.success ? 'success' : 'danger');
            })
            .catch(error => {
                isLoading = false;
                showLoader('infoLoader', false);
                showAlert('infoResult', 'Lỗi: ' + error.message, 'danger');
            });
        }

        function handleUserVideos() {
            if (isLoading) return;
            
            const url = document.getElementById('userUrl').value.trim();
            const proxy = document.getElementById('userProxy').value.trim();
            const limit = document.getElementById('userLimit').value.trim();
            const customDir = document.getElementById('userCustomDir').value.trim();
            
            if (!url) {
                showAlert('userVideosResult', 'Vui lòng nhập URL người dùng TikTok', 'danger');
                return;
            }
            
            isLoading = true;
            showLoader('userVideosLoader', true);
            clearResults('userVideosResult');
            
            const requestData = {
                url,
                proxy: proxy || null,
                limit: limit || null,
                customDir: customDir || null
            };
            
            fetch('/api/user-videos', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            })
            .then(response => response.json())
            .then(data => {
                isLoading = false;
                showLoader('userVideosLoader', false);
                
                if (data.success) {
                    let message = data.message;
                    if (data.download_location) {
                        message += `<br><strong>Thư mục lưu:</strong> ${data.download_location}`;
                    }
                    if (data.files && data.files.length > 0) {
                        message += `<br><strong>Số video:</strong> ${data.files.length}`;
                    }
                    showAlert('userVideosResult', message, 'success');
                } else {
                    showAlert('userVideosResult', data.message, 'danger');
                }
            })
            .catch(error => {
                isLoading = false;
                showLoader('userVideosLoader', false);
                showAlert('userVideosResult', 'Lỗi: ' + error.message, 'danger');
            });
        }

        function loadDownloads() {
            fetch('/api/list-downloads')
                .then(response => response.json())
                .then(data => {
                    const downloadsList = document.getElementById('downloadsList');
                    
                    if (data.files && data.files.length > 0) {
                        let html = '';
                        data.files.forEach(file => {
                            html += `
                                <tr>
                                    <td>${file.name}</td>
                                    <td>${file.size}</td>
                                    <td>${file.date}</td>
                                    <td>
                                        <div class="btn-group btn-group-sm">
                                            <a href="${file.url}" class="btn btn-outline-primary" download title="Download">
                                                <i class="fas fa-download"></i>
                                            </a>
                                            <a href="${file.url}" class="btn btn-outline-info" target="_blank" title="Play">
                                                <i class="fas fa-play"></i>
                                            </a>
                                        </div>
                                    </td>
                                </tr>
                            `;
                        });
                        downloadsList.innerHTML = html;
                    } else {
                        downloadsList.innerHTML = '<tr><td colspan="4" class="text-center text-muted">Không có video nào</td></tr>';
                    }
                })
                .catch(error => {
                    console.error('Error loading downloads:', error);
                    document.getElementById('downloadsList').innerHTML = 
                        '<tr><td colspan="4" class="text-center text-danger">Lỗi tải danh sách</td></tr>';
                });
        }

        function showLoader(loaderId, show) {
            document.getElementById(loaderId).style.display = show ? 'block' : 'none';
        }

        function clearResults(elementId) {
            document.getElementById(elementId).innerHTML = '';
        }

        function showAlert(elementId, message, type) {
            document.getElementById(elementId).innerHTML = `
                <div class="alert alert-${type} alert-dismissible fade show">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        }

        function showPreview(fileUrl, filename) {
            document.getElementById('videoPreviewContainer').style.display = 'block';
            document.getElementById('videoPreview').src = fileUrl;
            
            const downloadLink = document.getElementById('downloadLink');
            downloadLink.href = fileUrl;
            downloadLink.setAttribute('download', filename);
        }

        function hidePreview() {
            document.getElementById('videoPreviewContainer').style.display = 'none';
        }
    </script>
</body>
</html>'''
    
    return html_content

@app.route('/api/download', methods=['POST'])
def api_download():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        proxy = data.get('proxy', None)
        custom_dir = data.get('customDir', None)
        limit = data.get('limit', None)
        
        if not url:
            return jsonify({'success': False, 'message': 'URL không được để trống'})
        
        # Setup output directory
        output_dir = DOWNLOADS_DIR
        if custom_dir and custom_dir.strip():
            try:
                output_dir = os.path.abspath(os.path.expanduser(custom_dir.strip()))
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
            except Exception as e:
                return jsonify({'success': False, 'message': f'Lỗi thư mục: {str(e)}'})
        
        # Convert limit to int if provided
        video_limit = None
        if limit and str(limit).isdigit():
            video_limit = int(limit)
        
                        # Download video
        success, message = download_video(url, proxy, output_dir=output_dir, limit=video_limit)
        
        if success:
            # Find the latest mp4 file
            try:
                mp4_files = [f for f in os.listdir(output_dir) if f.endswith('.mp4')]
                if mp4_files:
                    latest_file = max(mp4_files, key=lambda x: os.path.getctime(os.path.join(output_dir, x)))
                    
                    # If using custom directory, copy to downloads for preview
                    if output_dir != DOWNLOADS_DIR:
                        try:
                            shutil.copy2(os.path.join(output_dir, latest_file), 
                                       os.path.join(DOWNLOADS_DIR, latest_file))
                            file_url = f'/downloads/{latest_file}'
                        except:
                            file_url = None
                    else:
                        file_url = f'/downloads/{latest_file}'
                    
                    return jsonify({
                        'success': True,
                        'message': 'Tải video thành công!',
                        'filename': latest_file,
                        'file_url': file_url,
                        'localPath': os.path.join(output_dir, latest_file)
                    })
            except Exception as e:
                return jsonify({'success': True, 'message': f'{message} (Không thể tạo preview: {str(e)})'})
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'})

@app.route('/api/info', methods=['POST'])
def api_info():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        proxy = data.get('proxy', None)
        
        if not url:
            return jsonify({'success': False, 'message': 'URL không được để trống'})
        
        success, message = get_video_info(url, proxy)
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'})

@app.route('/api/user-videos', methods=['POST'])
def api_user_videos():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        proxy = data.get('proxy', None)
        limit = data.get('limit', None)
        custom_dir = data.get('customDir', None)
        
        if not url:
            return jsonify({'success': False, 'message': 'URL không được để trống'})
        
        # Convert limit to int if provided
        if limit and str(limit).isdigit():
            limit = int(limit)
        else:
            limit = None
        
        # Setup output directory
        output_dir = DOWNLOADS_DIR
        if custom_dir and custom_dir.strip():
            try:
                output_dir = os.path.abspath(os.path.expanduser(custom_dir.strip()))
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
            except Exception as e:
                return jsonify({'success': False, 'message': f'Lỗi thư mục: {str(e)}'})
        
        success, message = download_user_videos(url, proxy, limit=limit, output_dir=output_dir)
        
        if success:
            # Count downloaded files
            try:
                files = [f for f in os.listdir(output_dir) if f.endswith('.mp4')]
                return jsonify({
                    'success': True,
                    'message': message,
                    'files': files,
                    'download_location': output_dir
                })
            except:
                return jsonify({'success': True, 'message': message})
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'})

@app.route('/downloads/<path:filename>')
def download_file(filename):
    """Serve downloaded files"""
    return send_from_directory(DOWNLOADS_DIR, filename)

@app.route('/api/list-downloads')
def list_downloads():
    """List all downloaded files"""
    try:
        files = [f for f in os.listdir(DOWNLOADS_DIR) if f.endswith('.mp4')]
        file_data = []
        
        for file in files:
            file_path = os.path.join(DOWNLOADS_DIR, file)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
            mod_time = time.strftime('%Y-%m-%d %H:%M:%S', 
                                   time.localtime(os.path.getmtime(file_path)))
            
            file_data.append({
                'name': file,
                'size': f'{file_size:.2f} MB',
                'date': mod_time,
                'url': f'/downloads/{file}'
            })
        
        # Sort by modification time (newest first)
        file_data.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({'files': file_data})
        
    except Exception as e:
        return jsonify({'files': [], 'error': str(e)})

if __name__ == '__main__':
    print("Starting TikTok Crawler Server...")
    print(f"Downloads directory: {DOWNLOADS_DIR}")
    app.run(debug=False, host='0.0.0.0', port=8080, threaded=True)