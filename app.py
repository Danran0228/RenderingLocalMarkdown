# 以配置文件的方式启动服务器
from RenderingMarkdown import create_app
from waitress import serve
import os
import json

if __name__ == '__main__':
    config_file = os.path.join(os.path.dirname(__file__), 'config.json')
    
    with open(config_file, 'r') as f:
        config = json.load(f)

    app = create_app(config_file)
    
    host = config.get('HOST', '0.0.0.0')
    port = config.get('PORT', 8888)
    
    print(f"服务已启动，访问地址: http://{host}:{port}")
    serve(app, host=host, port=port)
