# Hướng dẫn cập nhật giao diện

1. Thêm CSS mới vào phần `<style>`:
```css
.local-path-input {
    position: relative;
}
.local-path-input .form-control {
    padding-right: 100px;
}
.local-path-input .btn-browse {
    position: absolute;
    right: 0;
    top: 0;
    border-top-left-radius: 0;
    border-bottom-left-radius: 0;
}
.progress {
    display: none;
    margin-top: 10px;
    height: 20px;
}
```

2. Thêm input thư mục vào form download (sau input downloadLimit):
```html
<div class="mb-3">
    <label for="downloadCustomDir" class="form-label fw-bold text-primary">
        Thư mục lưu trên máy tính
    </label>
    <div class="local-path-input">
        <input type="text" class="form-control" id="downloadCustomDir" 
               placeholder="Nhập đường dẫn thư mục trên máy của bạn">
        <button class="btn btn-outline-primary btn-browse" type="button" 
                onclick="showLocalPathGuide()">
            <i class="fas fa-info-circle"></i> Hướng dẫn
        </button>
    </div>
    <small class="text-muted">
        Ví dụ: C:\Downloads hoặc /home/user/Downloads
    </small>
    <div class="progress">
        <div class="progress-bar progress-bar-striped progress-bar-animated" 
             role="progressbar" style="width: 0%"></div>
    </div>
</div>
```

3. Thêm các hàm JavaScript mới (thêm vào phần script):
```javascript
let currentDownload = null;

function showProgress(show, progress = 0) {
    const progressBar = document.querySelector('.progress');
    const progressBarInner = progressBar.querySelector('.progress-bar');
    progressBar.style.display = show ? 'flex' : 'none';
    progressBarInner.style.width = `${progress}%`;
}

function showLocalPathGuide() {
    const guide = `
        <h5>Hướng dẫn nhập đường dẫn:</h5>
        <p><strong>Windows:</strong> C:\\Downloads\\TikTok</p>
        <p><strong>MacOS/Linux:</strong> /Users/yourname/Downloads/TikTok</p>
        <p>Lưu ý: 
            <ul>
                <li>Thư mục phải tồn tại trước khi tải xuống</li>
                <li>Sử dụng dấu \\ cho Windows hoặc / cho MacOS/Linux</li>
                <li>Không sử dụng ký tự đặc biệt trong đường dẫn</li>
            </ul>
        </p>
    `;
    
    showAlert('downloadResult', guide, 'info');
}

function downloadToLocal(filename, localPath) {
    showProgress(true, 10);
    
    fetch('/api/download-to-local', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename, localPath })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showProgress(true, 50);
            
            // Tạo link tải xuống ẩn và kích hoạt
            const link = document.createElement('a');
            link.href = data.download_url;
            link.download = filename;
            link.style.display = 'none';
            document.body.appendChild(link);
            
            // Bắt đầu tải xuống
            link.click();
            document.body.removeChild(link);
            
            showProgress(true, 100);
            setTimeout(() => showProgress(false), 1000);
            
            showAlert('downloadResult', 
                `File đang được tải về thư mục: ${data.local_path}`, 
                'success');
        } else {
            showProgress(false);
            showAlert('downloadResult', data.message, 'danger');
        }
    })
    .catch(error => {
        showProgress(false);
        showAlert('downloadResult', 'Lỗi tải xuống: ' + error.message, 'danger');
    });
}
```

4. Cập nhật hàm handleDownload:
```javascript
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
    showProgress(true, 0);
    
    fetch('/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, proxy, customDir, limit })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('downloadResult', data.message, 'success');
            showProgress(true, 50);
            
            if (data.filename && customDir) {
                // Tải xuống tự động vào thư mục đã chọn
                downloadToLocal(data.filename, customDir);
            } else if (data.file_url) {
                showPreview(data.file_url);
                showProgress(false);
            }
        } else {
            showAlert('downloadResult', data.message, 'danger');
            showProgress(false);
        }
        isLoading = false;
        showLoader('downloadLoader', false);
    })
    .catch(error => {
        isLoading = false;
        showLoader('downloadLoader', false);
        showProgress(false);
        showAlert('downloadResult', 'Lỗi: ' + error.message, 'danger');
    });
}
