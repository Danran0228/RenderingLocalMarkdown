from flask import Flask, render_template_string, send_from_directory, jsonify
import os
import markdown
import re
from waitress import serve
import json

app = Flask(__name__)

# 设置默认的Markdown文件存放目录
DEFAULT_MARKDOWN_FOLDER = os.path.join(os.path.dirname(__file__), 'markdowns')

def create_app(config_file=None):
    static_folder = os.path.join(os.path.dirname(__file__), 'static')
    app = Flask(__name__, static_folder=static_folder, static_url_path='/static')
    
    # 加载配置文件
    if config_file and os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            app.config.update(config)
    else:
        app.config.setdefault('MARKDOWN_FOLDER', DEFAULT_MARKDOWN_FOLDER)
    
    markdown_folder = os.path.abspath(os.path.normpath(app.config['MARKDOWN_FOLDER']))
    app.config['MARKDOWN_FOLDER'] = markdown_folder
    
    os.makedirs(app.config['MARKDOWN_FOLDER'], exist_ok=True)
    os.makedirs(static_folder, exist_ok=True)
    
    def get_markdown_files(directory):
        """递归获取所有Markdown文件，并按文件夹正确组织"""
        markdown_files = []
        for root, _, files in os.walk(directory):
            # 获取相对于根目录的路径
            rel_path = os.path.relpath(root, directory)
            rel_path = '' if rel_path == '.' else rel_path
            
            # 过滤出当前文件夹下的markdown文件
            md_files = [f for f in files if f.endswith('.md')]
            if md_files:
                # 将当前文件夹的所有markdown文件添加到列表中
                markdown_files.extend([(f, rel_path) for f in md_files])
        
        return markdown_files
    
    @app.route('/')
    def index():
        try:
            all_files = get_markdown_files(app.config['MARKDOWN_FOLDER'])
            folder_structure = {}
            for file, folder in all_files:
                if folder not in folder_structure:
                    folder_structure[folder] = []
                folder_structure[folder].append(file)
            
            return render_template_string("""
                <!DOCTYPE html>
                <html>
                    <head>
                        <title>Markdown文档查看器</title>
                        <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
                        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
                    </head>
                    <body>
                        <div class="layout">
                            <div class="sidebar">
                                <div class="sidebar-header">
                                    <h1>文档目录</h1>
                                </div>
                                <div class="file-tree">
                                    {% for folder, files in structure.items()|sort %}
                                        <div class="folder">
                                            <div class="folder-header" onclick="toggleFolder(this)">
                                                <i class="fas fa-chevron-right folder-icon"></i>
                                                <i class="fas fa-folder"></i>
                                                <span>{{ folder if folder else '根目录' }}</span>
                                            </div>
                                            <ul class="folder-content">
                                                {% for file in files|sort %}
                                                    <li>
                                                        <a href="#" onclick="loadContent('{{ folder + '/' + file[:-3] if folder else file[:-3] }}'); return false;">
                                                            <i class="fas fa-file-alt"></i>
                                                            {{ file[:-3] }}
                                                        </a>
                                                    </li>
                                                {% endfor %}
                                            </ul>
                                        </div>
                                    {% endfor %}
                                </div>
                            </div>
                            <div class="content-area">
                                <div id="content">
                                    <div class="welcome-message">
                                        <h2>欢迎使用 Markdown 文档查看器</h2>
                                        <p>请从左侧目录选择要查看的文档</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <script>
                            function toggleFolder(element) {
                                const folderContent = element.nextElementSibling;
                                const folderIcon = element.querySelector('.folder-icon');
                                
                                if (folderContent.style.display === 'none' || !folderContent.style.display) {
                                    folderContent.style.display = 'block';
                                    folderIcon.classList.remove('fa-chevron-right');
                                    folderIcon.classList.add('fa-chevron-down');
                                } else {
                                    folderContent.style.display = 'none';
                                    folderIcon.classList.remove('fa-chevron-down');
                                    folderIcon.classList.add('fa-chevron-right');
                                }
                            }
                            
                            function loadContent(filePath) {
                                fetch(`/api/content/${filePath}`)
                                    .then(response => response.json())
                                    .then(data => {
                                        document.getElementById('content').innerHTML = data.content;
                                    })
                                    .catch(error => {
                                        console.error('Error:', error);
                                        document.getElementById('content').innerHTML = '<div class="error">加载失败</div>';
                                    });
                            }
                        </script>
                    </body>
                </html>
            """, structure=folder_structure)
        except Exception as e:
            return f"发生错误: {str(e)}"

    # 添加API路由来获取文件内容
    @app.route('/api/content/<path:file_path>')
    def get_content(file_path):
        try:
            file_path = os.path.normpath(file_path)
            full_path = os.path.join(app.config['MARKDOWN_FOLDER'], f'{file_path}.md')
            
            if not os.path.normpath(full_path).startswith(os.path.normpath(app.config['MARKDOWN_FOLDER'])):
                return jsonify({'error': '非法的文件路径'}), 403
            
            if not os.path.exists(full_path):
                return jsonify({'error': '文件未找到'}), 404
            
            with open(full_path, 'r', encoding='utf-8') as file:
                md_content = file.read()
            
            # 获取文件的目录部分
            directory = os.path.dirname(file_path)
            # 替换相对路径的图片链接，确保包含目录层级
            md_content = re.sub(r'!\[([^\]]*)\]\(\./images/([^\)]+)\)', r'![\1](/images/' + directory + r'/images/\2)', md_content)

            html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
            return jsonify({
                'content': f'''
                    <div class="markdown-content">
                        
                        {html_content}
                    </div>
                '''
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/view/<path:file_path>')
    def view_markdown(file_path):
        try:
            file_path = os.path.normpath(file_path)
            full_path = os.path.join(app.config['MARKDOWN_FOLDER'], f'{file_path}.md')
            
            if not os.path.normpath(full_path).startswith(os.path.normpath(app.config['MARKDOWN_FOLDER'])):
                return "非法的文件路径", 403
            
            if not os.path.exists(full_path):
                return "文件未找到", 404
            
            with open(full_path, 'r', encoding='utf-8') as file:
                md_content = file.read()

            html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
            display_name = os.path.basename(file_path)

            return render_template_string("""
                <!DOCTYPE html>
                <html>
                    <head>
                        <title>{{ filename }}</title>
                        <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
                        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
                    </head>
                    <body>
                        <div class="container">
                            <h1>{{ filename }}</h1>
                            <div class="content">{{ content|safe }}</div>
                            <a href="/" class="back-link">
                                <i class="fas fa-arrow-left"></i> 返回文件列表
                            </a>
                        </div>
                    </body>
                </html>
            """, filename=display_name, content=html_content)

        except Exception as e:
            return f"发生错误: {str(e)}"
            
    @app.route('/images/<path:image_path>')
    def serve_image(image_path):
        # 确保图片路径是安全的
        image_full_path = os.path.join(app.config['MARKDOWN_FOLDER'], image_path)
        if os.path.exists(image_full_path):
            return send_from_directory(os.path.dirname(image_full_path), os.path.basename(image_full_path))
        return "图片未找到", 404
    
    return app
