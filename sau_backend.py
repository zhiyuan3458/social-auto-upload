import asyncio
import os
import sys
import sqlite3
import threading
import time
import uuid
import logging
import traceback
from datetime import datetime
from pathlib import Path
from queue import Queue
from flask_cors import CORS
from myUtils.auth import check_cookie
from flask import Flask, request, jsonify, Response, render_template, send_from_directory
from conf import BASE_DIR, DATA_DIR
from myUtils.login import get_tencent_cookie, douyin_cookie_gen, get_ks_cookie, xiaohongshu_cookie_gen
from myUtils.postVideo import post_video_tencent, post_video_DouYin, post_video_ks, post_video_xhs

# ============ 日志配置 ============
def setup_logging():
    """配置日志系统，将日志写入到安装目录的 logs 文件夹"""
    # 创建 logs 目录
    logs_dir = Path(DATA_DIR) / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # 日志文件名（按日期）
    log_filename = logs_dir / f"backend_{datetime.now().strftime('%Y%m%d')}.log"
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # 文件处理器（详细日志）
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # 控制台处理器（简要日志）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', datefmt='%H:%M:%S')
    console_handler.setFormatter(console_formatter)
    
    # 添加处理器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 记录启动信息
    logging.info("=" * 60)
    logging.info("后端服务启动")
    logging.info(f"日志目录: {logs_dir}")
    logging.info(f"数据目录: {DATA_DIR}")
    logging.info(f"基础目录: {BASE_DIR}")
    logging.info(f"Python 版本: {sys.version}")
    logging.info(f"是否打包环境: {getattr(sys, 'frozen', False)}")
    logging.info("=" * 60)
    
    return log_filename

# 初始化日志
LOG_FILE = setup_logging()
logger = logging.getLogger(__name__)

# 导入 AI 模块
from ai_module import register_ai_routes

active_queues = {}
app = Flask(__name__)

#允许所有来源跨域访问
CORS(app)

# 注册 AI 路由
register_ai_routes(app)

# 限制上传文件大小为160MB
app.config['MAX_CONTENT_LENGTH'] = 160 * 1024 * 1024

# ============ 全局异常处理 ============
@app.errorhandler(Exception)
def handle_exception(e):
    """全局异常处理器，记录所有未捕获的异常"""
    error_msg = f"未捕获的异常: {str(e)}"
    logger.error(error_msg)
    logger.error(f"请求路径: {request.path}")
    logger.error(f"请求方法: {request.method}")
    logger.error(f"详细错误堆栈:\n{traceback.format_exc()}")
    
    return jsonify({
        "code": 500,
        "msg": f"服务器内部错误: {str(e)}",
        "data": None
    }), 500

@app.errorhandler(404)
def handle_not_found(e):
    """404 错误处理"""
    logger.warning(f"404 错误: {request.path}")
    return jsonify({
        "code": 404,
        "msg": f"接口不存在: {request.path}",
        "data": None
    }), 404

@app.before_request
def log_request():
    """记录每个请求"""
    if not request.path.startswith('/assets') and not request.path.endswith('.ico'):
        logger.debug(f"请求: {request.method} {request.path}")

# 获取当前目录（假设 index.html 和 assets 在这里）
current_dir = os.path.dirname(os.path.abspath(__file__))

# 处理所有静态资源请求（未来打包用）
@app.route('/assets/<filename>')
def custom_static(filename):
    return send_from_directory(os.path.join(current_dir, 'assets'), filename)

# 处理 favicon.ico 静态资源（未来打包用）
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_dir, 'assets'), 'vite.svg')

@app.route('/vite.svg')
def vite_svg():
    return send_from_directory(os.path.join(current_dir, 'assets'), 'vite.svg')

# （未来打包用）
@app.route('/')
def index():  # put application's code here
    return send_from_directory(current_dir, 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({
            "code": 200,
            "data": None,
            "msg": "No file part in the request"
        }), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 200,
            "data": None,
            "msg": "No selected file"
        }), 400
    try:
        # 保存文件到指定位置
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        filepath = Path(DATA_DIR / "videoFile" / f"{uuid_v1}_{file.filename}")
        file.save(filepath)
        return jsonify({"code":200,"msg": "File uploaded successfully", "data": f"{uuid_v1}_{file.filename}"}), 200
    except Exception as e:
        return jsonify({"code":200,"msg": str(e),"data":None}), 500

@app.route('/getFile', methods=['GET'])
def get_file():
    # 获取 filename 参数
    filename = request.args.get('filename')

    if not filename:
        return {"error": "filename is required"}, 400

    # 防止路径穿越攻击
    if '..' in filename or filename.startswith('/'):
        return {"error": "Invalid filename"}, 400

    # 拼接完整路径
    file_path = str(Path(DATA_DIR / "videoFile"))

    # 返回文件
    return send_from_directory(file_path,filename)


@app.route('/uploadSave', methods=['POST'])
def upload_save():
    if 'file' not in request.files:
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No file part in the request"
        }), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No selected file"
        }), 400

    # 获取表单中的自定义文件名（可选）
    custom_filename = request.form.get('filename', None)
    if custom_filename:
        filename = custom_filename + "." + file.filename.split('.')[-1]
    else:
        filename = file.filename

    try:
        # 生成 UUID v1
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")

        # 构造文件名和路径
        final_filename = f"{uuid_v1}_{filename}"
        filepath = Path(DATA_DIR / "videoFile" / f"{uuid_v1}_{filename}")

        # 保存文件
        file.save(filepath)

        with sqlite3.connect(Path(DATA_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                                INSERT INTO file_records (filename, filesize, file_path)
            VALUES (?, ?, ?)
                                ''', (filename, round(float(os.path.getsize(filepath)) / (1024 * 1024),2), final_filename))
            conn.commit()
            print("✅ 上传文件已记录")

        return jsonify({
            "code": 200,
            "msg": "File uploaded and saved successfully",
            "data": {
                "filename": filename,
                "filepath": final_filename
            }
        }), 200

    except Exception as e:
        print(f"Upload failed: {e}")
        return jsonify({
            "code": 500,
            "msg": f"upload failed: {e}",
            "data": None
        }), 500

@app.route('/getFiles', methods=['GET'])
def get_all_files():
    try:
        # 使用 with 自动管理数据库连接
        with sqlite3.connect(Path(DATA_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row  # 允许通过列名访问结果
            cursor = conn.cursor()

            # 查询所有记录
            cursor.execute("SELECT * FROM file_records")
            rows = cursor.fetchall()

            # 将结果转为字典列表，并提取UUID
            data = []
            for row in rows:
                row_dict = dict(row)
                # 从 file_path 中提取 UUID (文件名的第一部分，下划线前)
                if row_dict.get('file_path'):
                    file_path_parts = row_dict['file_path'].split('_', 1)  # 只分割第一个下划线
                    if len(file_path_parts) > 0:
                        row_dict['uuid'] = file_path_parts[0]  # UUID 部分
                    else:
                        row_dict['uuid'] = ''
                else:
                    row_dict['uuid'] = ''
                data.append(row_dict)

            return jsonify({
                "code": 200,
                "msg": "success",
                "data": data
            }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("get file failed!"),
            "data": None
        }), 500


@app.route("/getAccounts", methods=['GET'])
def getAccounts():
    """快速获取所有账号信息，不进行cookie验证"""
    logger.info("API 调用: getAccounts")
    try:
        db_path = Path(DATA_DIR / "db" / "database.db")
        logger.debug(f"数据库路径: {db_path}, 存在: {db_path.exists()}")
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''SELECT * FROM user_info''')
            rows = cursor.fetchall()
            rows_list = [list(row) for row in rows]

            logger.info(f"获取账号列表成功，共 {len(rows_list)} 条记录")

            return jsonify({
                "code": 200,
                "msg": None,
                "data": rows_list
            }), 200
            
    except Exception as e:
        error_msg = f"获取账号列表失败: {str(e)}"
        logger.error(error_msg)
        logger.error(f"详细错误堆栈:\n{traceback.format_exc()}")
        return jsonify({
            "code": 500,
            "msg": error_msg,
            "data": None
        }), 500


@app.route("/getValidAccounts", methods=['GET'])
async def getValidAccounts():
    """获取所有账号信息，并验证cookie有效性"""
    logger.info("API 调用: getValidAccounts")
    try:
        db_path = Path(DATA_DIR / "db" / "database.db")
        logger.debug(f"数据库路径: {db_path}, 存在: {db_path.exists()}")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT * FROM user_info''')
            rows = cursor.fetchall()
            rows_list = [list(row) for row in rows]
            
            logger.info(f"查询到 {len(rows_list)} 个账号，开始验证 cookie...")
            
            for i, row in enumerate(rows_list):
                try:
                    logger.debug(f"验证账号 [{i+1}/{len(rows_list)}]: type={row[1]}, cookie_file={row[2]}")
                    flag = await check_cookie(row[1], row[2])
                    if not flag:
                        row[4] = 0
                        cursor.execute('''
                        UPDATE user_info 
                        SET status = ? 
                        WHERE id = ?
                        ''', (0, row[0]))
                        conn.commit()
                        logger.info(f"账号 {row[0]} cookie 已失效，状态已更新")
                except Exception as cookie_error:
                    logger.warning(f"验证账号 {row[0]} cookie 时出错: {str(cookie_error)}")
                    # 继续处理其他账号
            
            logger.info(f"getValidAccounts 完成，返回 {len(rows_list)} 条记录")
            return jsonify({
                "code": 200,
                "msg": None,
                "data": rows_list
            }), 200
            
    except Exception as e:
        error_msg = f"获取有效账号列表失败: {str(e)}"
        logger.error(error_msg)
        logger.error(f"详细错误堆栈:\n{traceback.format_exc()}")
        return jsonify({
            "code": 500,
            "msg": error_msg,
            "data": None
        }), 500

@app.route('/deleteFile', methods=['GET'])
def delete_file():
    file_id = request.args.get('id')

    if not file_id or not file_id.isdigit():
        return jsonify({
            "code": 400,
            "msg": "Invalid or missing file ID",
            "data": None
        }), 400

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(DATA_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM file_records WHERE id = ?", (file_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "File not found",
                    "data": None
                }), 404

            record = dict(record)

            # 获取文件路径并删除实际文件
            file_path = Path(DATA_DIR / "videoFile" / record['file_path'])
            if file_path.exists():
                try:
                    file_path.unlink()  # 删除文件
                    print(f"✅ 实际文件已删除: {file_path}")
                except Exception as e:
                    print(f"⚠️ 删除实际文件失败: {e}")
                    # 即使删除文件失败，也要继续删除数据库记录，避免数据不一致
            else:
                print(f"⚠️ 实际文件不存在: {file_path}")

            # 删除数据库记录
            cursor.execute("DELETE FROM file_records WHERE id = ?", (file_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "File deleted successfully",
            "data": {
                "id": record['id'],
                "filename": record['filename']
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("delete failed!"),
            "data": None
        }), 500

@app.route('/deleteAccount', methods=['GET'])
def delete_account():
    account_id = int(request.args.get('id'))

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(DATA_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM user_info WHERE id = ?", (account_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "account not found",
                    "data": None
                }), 404

            record = dict(record)

            # 删除数据库记录
            cursor.execute("DELETE FROM user_info WHERE id = ?", (account_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account deleted successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("delete failed!"),
            "data": None
        }), 500


# SSE 登录接口
@app.route('/login')
def login():
    # 1 小红书 2 视频号 3 抖音 4 快手
    type = request.args.get('type')
    # 账号名
    id = request.args.get('id')

    # 模拟一个用于异步通信的队列
    status_queue = Queue()
    active_queues[id] = status_queue

    def on_close():
        print(f"清理队列: {id}")
        del active_queues[id]
    # 启动异步任务线程
    thread = threading.Thread(target=run_async_function, args=(type,id,status_queue), daemon=True)
    thread.start()
    response = Response(sse_stream(status_queue,), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # 关键：禁用 Nginx 缓冲
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Connection'] = 'keep-alive'
    return response

@app.route('/postVideo', methods=['POST'])
def postVideo():
    # 获取JSON数据
    data = request.get_json()

    # 从JSON数据中提取fileList和accountList
    file_list = data.get('fileList', [])
    account_list = data.get('accountList', [])
    type = data.get('type')
    title = data.get('title')
    tags = data.get('tags')
    category = data.get('category')
    enableTimer = data.get('enableTimer')
    if category == 0:
        category = None
    productLink = data.get('productLink', '')
    productTitle = data.get('productTitle', '')
    thumbnail_path = data.get('thumbnail', '')
    is_draft = data.get('isDraft', False)  # 新增参数：是否保存为草稿

    videos_per_day = data.get('videosPerDay')
    daily_times = data.get('dailyTimes')
    start_days = data.get('startDays')
    # 打印获取到的数据（仅作为示例）
    print("File List:", file_list)
    print("Account List:", account_list)
    match type:
        case 1:
            post_video_xhs(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                               start_days)
        case 2:
            post_video_tencent(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                               start_days, is_draft)
        case 3:
            post_video_DouYin(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                      start_days, thumbnail_path, productLink, productTitle)
        case 4:
            post_video_ks(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                      start_days)
    # 返回响应给客户端
    return jsonify(
        {
            "code": 200,
            "msg": None,
            "data": None
        }), 200


@app.route('/updateUserinfo', methods=['POST'])
def updateUserinfo():
    # 获取JSON数据
    data = request.get_json()

    # 从JSON数据中提取 type 和 userName
    user_id = data.get('id')
    type = data.get('type')
    userName = data.get('userName')
    try:
        # 获取数据库连接
        with sqlite3.connect(Path(DATA_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 更新数据库记录
            cursor.execute('''
                           UPDATE user_info
                           SET type     = ?,
                               userName = ?
                           WHERE id = ?;
                           ''', (type, userName, user_id))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account update successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("update failed!"),
            "data": None
        }), 500

@app.route('/postVideoBatch', methods=['POST'])
def postVideoBatch():
    data_list = request.get_json()

    if not isinstance(data_list, list):
        return jsonify({"error": "Expected a JSON array"}), 400
    for data in data_list:
        # 从JSON数据中提取fileList和accountList
        file_list = data.get('fileList', [])
        account_list = data.get('accountList', [])
        type = data.get('type')
        title = data.get('title')
        tags = data.get('tags')
        category = data.get('category')
        enableTimer = data.get('enableTimer')
        if category == 0:
            category = None
        productLink = data.get('productLink', '')
        productTitle = data.get('productTitle', '')

        videos_per_day = data.get('videosPerDay')
        daily_times = data.get('dailyTimes')
        start_days = data.get('startDays')
        # 打印获取到的数据（仅作为示例）
        print("File List:", file_list)
        print("Account List:", account_list)
        match type:
            case 1:
                return
            case 2:
                post_video_tencent(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                                   start_days)
            case 3:
                post_video_DouYin(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days, productLink, productTitle)
            case 4:
                post_video_ks(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days)
    # 返回响应给客户端
    return jsonify(
        {
            "code": 200,
            "msg": None,
            "data": None
        }), 200

# Cookie文件上传API
@app.route('/uploadCookie', methods=['POST'])
def upload_cookie():
    try:
        if 'file' not in request.files:
            return jsonify({
                "code": 500,
                "msg": "没有找到Cookie文件",
                "data": None
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "code": 500,
                "msg": "Cookie文件名不能为空",
                "data": None
            }), 400

        if not file.filename.endswith('.json'):
            return jsonify({
                "code": 500,
                "msg": "Cookie文件必须是JSON格式",
                "data": None
            }), 400

        # 获取账号信息
        account_id = request.form.get('id')
        platform = request.form.get('platform')

        if not account_id or not platform:
            return jsonify({
                "code": 500,
                "msg": "缺少账号ID或平台信息",
                "data": None
            }), 400

        # 从数据库获取账号的文件路径
        with sqlite3.connect(Path(DATA_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT filePath FROM user_info WHERE id = ?', (account_id,))
            result = cursor.fetchone()

        if not result:
            return jsonify({
                "code": 500,
                "msg": "账号不存在",
                "data": None
            }), 404

        # 保存上传的Cookie文件到对应路径
        cookie_file_path = Path(DATA_DIR / "cookiesFile" / result['filePath'])
        cookie_file_path.parent.mkdir(parents=True, exist_ok=True)

        file.save(str(cookie_file_path))

        # 更新数据库中的账号信息（可选，比如更新更新时间）
        # 这里可以根据需要添加额外的处理逻辑

        return jsonify({
            "code": 200,
            "msg": "Cookie文件上传成功",
            "data": None
        }), 200

    except Exception as e:
        print(f"上传Cookie文件时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"上传Cookie文件失败: {str(e)}",
            "data": None
        }), 500


# Cookie文件下载API
@app.route('/downloadCookie', methods=['GET'])
def download_cookie():
    try:
        file_path = request.args.get('filePath')
        if not file_path:
            return jsonify({
                "code": 500,
                "msg": "缺少文件路径参数",
                "data": None
            }), 400

        # 验证文件路径的安全性，防止路径遍历攻击
        cookie_file_path = Path(DATA_DIR / "cookiesFile" / file_path).resolve()
        base_path = Path(DATA_DIR / "cookiesFile").resolve()

        if not cookie_file_path.is_relative_to(base_path):
            return jsonify({
                "code": 500,
                "msg": "非法文件路径",
                "data": None
            }), 400

        if not cookie_file_path.exists():
            return jsonify({
                "code": 500,
                "msg": "Cookie文件不存在",
                "data": None
            }), 404

        # 返回文件
        return send_from_directory(
            directory=str(cookie_file_path.parent),
            path=cookie_file_path.name,
            as_attachment=True
        )

    except Exception as e:
        print(f"下载Cookie文件时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"下载Cookie文件失败: {str(e)}",
            "data": None
        }), 500


# 包装函数：在线程中运行异步函数
def run_async_function(type,id,status_queue):
    match type:
        case '1':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(xiaohongshu_cookie_gen(id, status_queue))
            loop.close()
        case '2':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(get_tencent_cookie(id,status_queue))
            loop.close()
        case '3':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(douyin_cookie_gen(id,status_queue))
            loop.close()
        case '4':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(get_ks_cookie(id,status_queue))
            loop.close()

# SSE 流生成器函数
def sse_stream(status_queue):
    while True:
        if not status_queue.empty():
            msg = status_queue.get()
            yield f"data: {msg}\n\n"
        else:
            # 避免 CPU 占满
            time.sleep(0.1)

# AI 素材转移到素材库
@app.route('/api/ai/transfer-to-material', methods=['POST'])
def transfer_ai_to_material():
    """将 AI 生成的图片转移到素材库"""
    import shutil
    
    try:
        data = request.get_json() or {}
        task_id = data.get('task_id')
        images = data.get('images', [])
        title = data.get('title', 'AI生成图文')
        
        if not task_id or not images:
            return jsonify({
                "code": 400,
                "msg": "task_id and images are required",
                "data": None
            }), 400
        
        # AI 图片源目录
        ai_history_dir = Path(DATA_DIR) / 'ai_history' / task_id
        if not ai_history_dir.exists():
            return jsonify({
                "code": 404,
                "msg": "AI task not found",
                "data": None
            }), 404
        
        # 素材目标目录
        material_dir = Path(DATA_DIR) / 'videoFile'
        material_dir.mkdir(parents=True, exist_ok=True)
        
        # 转移图片
        transferred = []
        with sqlite3.connect(Path(DATA_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            
            for img_filename in images:
                src_path = ai_history_dir / img_filename
                if not src_path.exists():
                    continue
                
                # 生成唯一文件名
                unique_name = f"ai_{task_id}_{img_filename}"
                dst_path = material_dir / unique_name
                
                # 复制文件
                shutil.copy2(src_path, dst_path)
                
                # 获取文件大小 (MB)
                file_size_mb = dst_path.stat().st_size / (1024 * 1024)
                
                # 插入数据库
                cursor.execute(
                    "INSERT INTO file_records (filename, filesize, file_path) VALUES (?, ?, ?)",
                    (unique_name, file_size_mb, str(dst_path))
                )
                
                transferred.append({
                    "original": img_filename,
                    "new_name": unique_name,
                    "path": str(dst_path)
                })
            
            conn.commit()
        
        return jsonify({
            "code": 200,
            "msg": "Transfer successful",
            "data": {
                "transferred": transferred,
                "count": len(transferred)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str(e),
            "data": None
        }), 500


# 小红书图文发布接口
@app.route('/postImageXHS', methods=['POST'])
def post_image_xhs():
    """
    发布小红书图文笔记
    
    请求参数:
        - title: 标题 (最多20字)
        - content: 正文内容 (最多1000字)
        - tags: 话题标签列表 (不带#号)
        - imageList: 图片文件名列表 (素材库中的文件)
        - accountList: 账号 cookie 文件路径列表
        - enableTimer: 是否定时发布 (0/1)
        - publishTime: 发布时间 (如: "2024-01-20 10:00")
    """
    from uploader.xiaohongshu_uploader.image_uploader import post_image_xhs as xhs_post_image
    from datetime import datetime
    
    try:
        data = request.get_json() or {}
        
        title = data.get('title', '')
        content = data.get('content', '')
        tags = data.get('tags', [])
        image_list = data.get('imageList', [])
        account_list = data.get('accountList', [])
        enable_timer = data.get('enableTimer', 0)
        publish_time = data.get('publishTime', '')
        
        if not image_list:
            return jsonify({
                "code": 400,
                "msg": "图片列表不能为空",
                "data": None
            }), 400
        
        if not account_list:
            return jsonify({
                "code": 400,
                "msg": "请选择发布账号",
                "data": None
            }), 400
        
        # 构建图片完整路径
        image_paths = []
        for img_name in image_list:
            img_path = Path(DATA_DIR) / "videoFile" / img_name
            if img_path.exists():
                image_paths.append(str(img_path))
            else:
                # 尝试从 AI 历史记录目录查找
                ai_path = Path(DATA_DIR) / "ai_history"
                for task_dir in ai_path.iterdir() if ai_path.exists() else []:
                    possible_path = task_dir / img_name
                    if possible_path.exists():
                        image_paths.append(str(possible_path))
                        break
        
        if not image_paths:
            return jsonify({
                "code": 400,
                "msg": "找不到指定的图片文件",
                "data": None
            }), 400
        
        # 解析发布时间
        publish_date = 0
        if enable_timer and publish_time:
            try:
                publish_date = datetime.strptime(publish_time, "%Y-%m-%d %H:%M")
            except:
                pass
        
        # 构建账号文件路径
        account_files = [Path(DATA_DIR / "cookiesFile" / acc) for acc in account_list]
        
        results = []
        for account_file in account_files:
            if not account_file.exists():
                results.append({
                    "account": str(account_file.name),
                    "success": False,
                    "error": "cookie 文件不存在"
                })
                continue
            
            try:
                # 执行上传
                success = asyncio.run(xhs_post_image(
                    title=title,
                    image_paths=image_paths,
                    content=content,
                    tags=tags,
                    account_file=str(account_file),
                    publish_date=publish_date
                ))
                
                results.append({
                    "account": str(account_file.name),
                    "success": success,
                    "error": None if success else "上传失败"
                })
                
            except Exception as e:
                results.append({
                    "account": str(account_file.name),
                    "success": False,
                    "error": str(e)
                })
        
        # 统计结果
        success_count = sum(1 for r in results if r["success"])
        
        return jsonify({
            "code": 200 if success_count > 0 else 500,
            "msg": f"发布完成: {success_count}/{len(results)} 成功",
            "data": {
                "results": results,
                "total": len(results),
                "success": success_count
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str(e),
            "data": None
        }), 500


# AI 图文一键发布到小红书
@app.route('/api/ai/publish-to-xhs', methods=['POST'])
def ai_publish_to_xhs():
    """
    将 AI 生成的图文直接发布到小红书
    
    请求参数:
        - task_id: AI 任务 ID
        - title: 标题
        - content: 正文内容  
        - tags: 标签列表
        - accountId: 账号 ID
    """
    from uploader.xiaohongshu_uploader.image_uploader import post_image_xhs as xhs_post_image
    
    try:
        data = request.get_json() or {}
        
        task_id = data.get('task_id')
        title = data.get('title', '')
        content = data.get('content', '')
        tags = data.get('tags', [])
        account_id = data.get('accountId')
        
        if not task_id:
            return jsonify({
                "code": 400,
                "msg": "task_id 不能为空",
                "data": None
            }), 400
        
        # 获取 AI 生成的图片
        ai_history_dir = Path(DATA_DIR) / 'ai_history' / task_id
        if not ai_history_dir.exists():
            return jsonify({
                "code": 404,
                "msg": "找不到 AI 任务",
                "data": None
            }), 404
        
        # 收集图片文件
        image_paths = []
        for i in range(20):  # 最多20张图
            img_path = ai_history_dir / f"{i}.png"
            if img_path.exists():
                image_paths.append(str(img_path))
        
        if not image_paths:
            return jsonify({
                "code": 400,
                "msg": "没有找到生成的图片",
                "data": None
            }), 400
        
        # 获取账号 cookie 文件
        account_file = None
        if account_id:
            with sqlite3.connect(Path(DATA_DIR / "db" / "database.db")) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM user_info WHERE id = ?", (account_id,))
                account = cursor.fetchone()
                if account:
                    account_file = Path(DATA_DIR / "cookiesFile" / account['filePath'])
        
        if not account_file or not account_file.exists():
            return jsonify({
                "code": 400,
                "msg": "账号不存在或 cookie 已失效",
                "data": None
            }), 400
        
        # 执行上传
        success = asyncio.run(xhs_post_image(
            title=title,
            image_paths=image_paths,
            content=content,
            tags=tags,
            account_file=str(account_file),
            publish_date=0
        ))
        
        if success:
            return jsonify({
                "code": 200,
                "msg": "发布成功",
                "data": {
                    "task_id": task_id,
                    "image_count": len(image_paths)
                }
            }), 200
        else:
            return jsonify({
                "code": 500,
                "msg": "发布失败",
                "data": None
            }), 500
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str(e),
            "data": None
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0' ,port=5409)
