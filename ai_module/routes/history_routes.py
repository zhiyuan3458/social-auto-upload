"""
AI 历史记录路由

GET /api/ai/history - 获取历史列表
POST /api/ai/history - 创建历史记录
GET /api/ai/history/<id> - 获取历史详情
PUT /api/ai/history/<id> - 更新历史记录
DELETE /api/ai/history/<id> - 删除历史记录
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify
from ai_module.config import AIConfig

logger = logging.getLogger(__name__)


def create_history_blueprint():
    """创建历史记录路由蓝图"""
    bp = Blueprint('ai_history', __name__)
    
    def get_history_index_path():
        """获取历史记录索引文件路径"""
        return AIConfig.get_history_dir() / 'index.json'
    
    def load_history_index():
        """加载历史记录索引"""
        index_path = get_history_index_path()
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"records": []}
    
    def save_history_index(index):
        """保存历史记录索引"""
        index_path = get_history_index_path()
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    @bp.route('/history', methods=['GET'])
    def get_history_list():
        """获取历史记录列表"""
        try:
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('page_size', 20))
            status = request.args.get('status')
            
            index = load_history_index()
            records = index.get('records', [])
            
            # 按状态过滤
            if status:
                records = [r for r in records if r.get('status') == status]
            
            # 按时间倒序
            records.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
            
            # 分页
            total = len(records)
            start = (page - 1) * page_size
            end = start + page_size
            page_records = records[start:end]
            
            return jsonify({
                "success": True,
                "records": page_records,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            })
            
        except Exception as e:
            logger.error(f"Get history list error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @bp.route('/history', methods=['POST'])
    def create_history():
        """创建历史记录"""
        try:
            data = request.get_json() or {}
            
            topic = data.get('topic', '')
            outline = data.get('outline', {})
            task_id = data.get('task_id')
            
            if not topic:
                return jsonify({
                    "success": False,
                    "error": "Topic is required"
                }), 400
            
            # 生成记录 ID
            record_id = str(uuid.uuid4())[:8]
            now = datetime.now().isoformat()
            
            # 创建记录
            record = {
                "id": record_id,
                "title": topic,
                "created_at": now,
                "updated_at": now,
                "status": "draft",
                "outline": outline,
                "images": {
                    "task_id": task_id,
                    "generated": []
                },
                "thumbnail": None,
                "page_count": len(outline.get('pages', []))
            }
            
            # 保存到索引
            index = load_history_index()
            index['records'].append(record)
            save_history_index(index)
            
            logger.info(f"History created: {record_id}")
            
            return jsonify({
                "success": True,
                "record_id": record_id
            })
            
        except Exception as e:
            logger.error(f"Create history error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @bp.route('/history/<record_id>', methods=['GET'])
    def get_history(record_id):
        """获取历史记录详情"""
        try:
            index = load_history_index()
            records = index.get('records', [])
            
            record = next((r for r in records if r.get('id') == record_id), None)
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "record": record
            })
            
        except Exception as e:
            logger.error(f"Get history error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @bp.route('/history/<record_id>', methods=['PUT'])
    def update_history(record_id):
        """更新历史记录"""
        try:
            data = request.get_json() or {}
            
            index = load_history_index()
            records = index.get('records', [])
            
            record_index = next((i for i, r in enumerate(records) if r.get('id') == record_id), None)
            
            if record_index is None:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # 更新字段
            record = records[record_index]
            
            if 'outline' in data:
                record['outline'] = data['outline']
                record['page_count'] = len(data['outline'].get('pages', []))
            
            if 'images' in data:
                record['images'] = data['images']
            
            if 'status' in data:
                record['status'] = data['status']
            
            if 'thumbnail' in data:
                record['thumbnail'] = data['thumbnail']
            
            record['updated_at'] = datetime.now().isoformat()
            
            # 保存
            index['records'][record_index] = record
            save_history_index(index)
            
            return jsonify({
                "success": True
            })
            
        except Exception as e:
            logger.error(f"Update history error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @bp.route('/history/<record_id>', methods=['DELETE'])
    def delete_history(record_id):
        """删除历史记录"""
        try:
            index = load_history_index()
            records = index.get('records', [])
            
            record = next((r for r in records if r.get('id') == record_id), None)
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # 删除关联的图片文件夹
            task_id = record.get('images', {}).get('task_id')
            if task_id:
                task_dir = AIConfig.get_history_dir() / task_id
                if task_dir.exists():
                    import shutil
                    shutil.rmtree(task_dir)
            
            # 从索引中删除
            index['records'] = [r for r in records if r.get('id') != record_id]
            save_history_index(index)
            
            logger.info(f"History deleted: {record_id}")
            
            return jsonify({
                "success": True
            })
            
        except Exception as e:
            logger.error(f"Delete history error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @bp.route('/history/<record_id>/exists', methods=['GET'])
    def check_history_exists(record_id):
        """检查历史记录是否存在"""
        try:
            index = load_history_index()
            records = index.get('records', [])
            
            exists = any(r.get('id') == record_id for r in records)
            
            return jsonify({
                "exists": exists
            })
            
        except Exception as e:
            return jsonify({
                "exists": False
            })
    
    @bp.route('/history/stats', methods=['GET'])
    def get_history_stats():
        """获取统计信息"""
        try:
            index = load_history_index()
            records = index.get('records', [])
            
            # 按状态统计
            by_status = {}
            for record in records:
                status = record.get('status', 'unknown')
                by_status[status] = by_status.get(status, 0) + 1
            
            return jsonify({
                "success": True,
                "total": len(records),
                "by_status": by_status
            })
            
        except Exception as e:
            logger.error(f"Get stats error: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    return bp
