from flask import Flask, render_template_string, send_from_directory, jsonify, request, make_response, render_template
import os
import markdown
import re
from waitress import serve
import json
import requests
import urllib.parse

app = Flask(__name__)

# 设置默认的Markdown文件存放目录
DEFAULT_MARKDOWN_FOLDER = os.path.join(os.path.dirname(__file__), 'markdowns')

def create_app(config_file=None):
    static_folder = os.path.join(os.path.dirname(__file__), 'static')
    app = Flask(__name__, static_folder=static_folder, static_url_path='/static')
    
    # 配置日志
    import logging
    from logging.handlers import RotatingFileHandler
    
    # 创建日志目录
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 配置日志处理器
    log_file = os.path.join(log_dir, 'app.log')
    handler = RotatingFileHandler(log_file, maxBytes=10000000, backupCount=5)
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    
    # 设置日志级别
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    
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
        """递归获取所有Markdown文件，并构建层级结构"""
        def build_tree(path):
            result = {}
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                relative_path = os.path.relpath(item_path, directory)
                
                if os.path.isdir(item_path):
                    subtree = build_tree(item_path)
                    if subtree:  # 只添加非空目录
                        result[item] = {
                            'type': 'directory',
                            'children': subtree
                        }
                elif item.endswith('.md'):
                    result[item] = {
                        'type': 'file',
                        'path': relative_path[:-3]  # 移除.md后缀
                    }
            return result

        return build_tree(directory)
    
    @app.route('/')
    def index():
        try:
            file_structure = get_markdown_files(app.config['MARKDOWN_FOLDER'])
            response = make_response(render_template('index.html', structure=file_structure))
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response
        except Exception as e:
            return make_response(f"发生错误: {str(e)}", 500, {'Content-Type': 'text/plain; charset=utf-8'})

    @app.after_request
    def set_response_encoding(response):
        if response.content_type.startswith('application/json'):
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response

    # 添加API路由来获取文件内容
    @app.route('/api/content/<path:file_path>')
    def get_content(file_path):
        try:
            file_path = os.path.normpath(file_path)
            full_path = os.path.join(app.config['MARKDOWN_FOLDER'], f'{file_path}.md')
            
            if not os.path.exists(full_path):
                app.logger.warning(f'文件未找到: {full_path}')
                return jsonify({'error': '文件未找到'}), 404
            
            with open(full_path, 'r', encoding='utf-8') as file:
                md_content = file.read()
            
            # 获取文件的目录部分
            directory = os.path.dirname(file_path)
            
            # 替换相对路径的图片链接
            def replace_image_path(match):
                alt_text = match.group(1)
                img_path = match.group(2)
                # 构建新的图片路径，保持原有的目录结构
                new_path = f'/images/{directory}/images/{img_path}'
                return f'![{alt_text}]({new_path})'
            
            md_content = re.sub(r'!\[([^\]]*)\]\(\./images/([^\)]+)\)', replace_image_path, md_content)

            html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
            return jsonify({
                'content': f'''
                    <div class="markdown-content">
                        {html_content}
                    </div>
                '''
            })
        except Exception as e:
            app.logger.error(f'处理内容请求时出错: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/view/<path:file_path>')
    def view_markdown(file_path):
        try:
            # 处理特殊字符编码
            file_path = file_path.replace('\x82', '20')  # 处理年份前缀
            file_path = file_path.replace('\x01', '/')   # 处理月份分隔符
            file_path = file_path.replace('\x05', '/')   # 处理日期分隔符
            
            # 规范化路径
            file_path = os.path.normpath(file_path)
            full_path = os.path.join(app.config['MARKDOWN_FOLDER'], f'{file_path}.md')
            
            if not os.path.normpath(full_path).startswith(os.path.normpath(app.config['MARKDOWN_FOLDER'])):
                app.logger.warning(f'非法的文件路径尝试: {full_path}')
                return jsonify({'error': '非法的文件路径'}), 403
            
            if not os.path.exists(full_path):
                app.logger.warning(f'文件未找到: {full_path}')
                return jsonify({'error': '文件未找到'}), 404
            
            with open(full_path, 'r', encoding='utf-8') as file:
                md_content = file.read()

            html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
            display_name = os.path.basename(file_path)

            response = make_response(render_template('view.html', 
                                 filename=display_name, 
                                 content=html_content))
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response

        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    @app.route('/images/<path:image_path>')
    def serve_image(image_path):
        try:
            # 解码 URL 编码的路径
            decoded_path = image_path
            if '%' in image_path:
                decoded_path = urllib.parse.unquote(image_path)
            
            # 确保图片路径是安全的
            image_full_path = os.path.join(app.config['MARKDOWN_FOLDER'], decoded_path)
            
            if os.path.exists(image_full_path):
                directory = os.path.dirname(image_full_path)
                filename = os.path.basename(image_full_path)
                return send_from_directory(directory, filename)
            
            app.logger.warning(f'图片未找到: {image_full_path}')
            return "图片未找到", 404
            
        except Exception as e:
            app.logger.error(f'处理图片请求时出错: {str(e)}')
            return "处理图片请求时出错", 500
    
    @app.route('/save-article', methods=['POST'])
    def save_article():
        try:
            data = request.get_json()
            article_url = data.get('url')

            # 从配置文件中获取文章保存服务的URL
            save_service_url = app.config.get('SAVE_ARTICLE_SERVICE_URL')  
            if not save_service_url:
                return jsonify({
                    'message': '文章保存服务URL未配置',
                    'status': 'error'
                }), 500

            response = requests.get(save_service_url, params={'url': article_url})
            
            if response.status_code == 200:
                return jsonify({
                    'message': '文章保存成功',
                    'status': 'success'
                })
            else:
                return jsonify({
                    'message': '文章保存失败',
                    'status': 'error'
                }), 500

        except Exception as e:
            return jsonify({
                'message': f'发生错误: {str(e)}',
                'status': 'error'
            }), 500
    
    
    return app
