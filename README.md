# Markdown 渲染服务器

一个简单的 Markdown 文件渲染服务器，支持预览 Markdown 文件。

## 功能特点

- 支持 Markdown 文件的在线预览
- 支持文件目录浏览
- 支持配置文件自定义服务参数

## 安装要求

- Python 3.7+
- Flask
- markdown2

## 快速开始

1. 创建配置文件 `config.json`：
    ```json
        {
        "MARKDOWN_FOLDER": "markdown", // Markdown 文件存储目录
        "HOST": "0.0.0.0", // 服务器监听地址
        "PORT": 8888, // 服务器端口
        }
    ```

2. 启动服务器：`python app.py`
## 配置说明

### 配置文件选项

| 配置项 | 说明 | 默认值 | 类型 |
|--------|------|--------|------|
| MARKDOWN_FOLDER | Markdown 文件存储目录 | "markdown" | string |
| HOST | 服务器监听地址 | "0.0.0.0" | string |
| PORT | 服务器监听端口 | 8888 | integer |

### 配置文件加载优先级

1. 命令行指定的配置文件（`--config` 参数）
2. 程序目录下的 `config.json`

## 启动方式

### 使用默认配置文件
```bash
python app.py
```

### 使用指定配置文件
```bash
python app.py --config /path/to/your/config.json
```

## 使用说明

1. 启动服务器后，访问 `http://[HOST]:[PORT]` 进入主页
2. 左侧为文件目录树，可以浏览所有 Markdown 文件
3. 点击文件名可以在右侧查看渲染后的效果

## 目录结构

```
.
├── README.md
├── app.py                 # 服务器启动脚本
├── RenderingMarkdown.py   # 主程序文件
├── config.json            # 默认配置文件
├── static/               # 静态资源目录
```


