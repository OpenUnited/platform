export class FileUploadHandler {
    constructor() {
        this.fileInput = document.getElementById('file-input');
        this.fileList = document.getElementById('file-list');
        this.dropArea = document.getElementById('file-upload-area');
        this.maxFileSize = 10 * 1024 * 1024; // 10MB
        this.files = new Set();
        
        this.bindEvents();
    }

    bindEvents() {
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.dropArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.dropArea.addEventListener('drop', (e) => this.handleDrop(e));
    }

    handleFileSelect(event) {
        this.addFiles(event.target.files);
    }

    handleDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
        this.dropArea.classList.add('border-primary');
    }

    handleDrop(event) {
        event.preventDefault();
        event.stopPropagation();
        this.dropArea.classList.remove('border-primary');
        this.addFiles(event.dataTransfer.files);
    }

    addFiles(fileList) {
        Array.from(fileList).forEach(file => {
            if (file.size > this.maxFileSize) {
                alert(`File ${file.name} is too large. Maximum size is 10MB.`);
                return;
            }
            this.files.add(file);
            this.updateFileList();
        });
    }

    updateFileList() {
        this.fileList.innerHTML = '';
        this.files.forEach(file => {
            const fileElement = this.createFileElement(file);
            this.fileList.appendChild(fileElement);
        });
    }

    createFileElement(file) {
        const div = document.createElement('div');
        div.className = 'flex items-center justify-between p-2 bg-base-200 rounded-lg';
        div.innerHTML = `
            <div class="flex items-center gap-2">
                <iconify-icon icon="lucide:file" height="18"></iconify-icon>
                <span class="text-sm">${file.name}</span>
            </div>
            <button type="button" class="btn btn-ghost btn-sm btn-square">
                <iconify-icon icon="lucide:x" height="18"></iconify-icon>
            </button>
        `;
        div.querySelector('button').onclick = () => {
            this.files.delete(file);
            this.updateFileList();
        };
        return div;
    }

    getFiles() {
        return Array.from(this.files);
    }
} 