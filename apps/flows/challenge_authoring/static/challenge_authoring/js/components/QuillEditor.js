export class QuillEditor {
    constructor(selector, options = {}) {
        this.editor = new Quill(selector, {
            theme: 'snow',
            modules: {
                toolbar: [
                    [{ 'header': [1, 2, 3, false] }],
                    ['bold', 'italic', 'underline'],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                    ['link']
                ]
            },
            placeholder: 'Enter description...',
            ...options
        });
    }

    getContent() {
        return this.editor.root.innerHTML;
    }

    setContent(content) {
        this.editor.root.innerHTML = content;
    }
} 