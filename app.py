 # 以配置文件的方式启动服务器
from RenderingMarkdown import create_app
from waitress import serve
import os

if __name__ == '__main__':
    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
    app = create_app(config_file)
    print("服务已启动，访问地址: http://localhost:8888")
    serve(app, host='0.0.0.0', port=8888)
