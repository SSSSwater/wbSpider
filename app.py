import base64
import os
import subprocess
import threading
import uuid

import requests
from flask import Flask, render_template, request, jsonify
from flask_restful import Resource, Api, reqparse

from WeiboSpider.WeiboSpider.RedisUtil import RedisQueueManager
import DataAnalysis
from WeiboSpider.WeiboSpider.NeoUtil import NeoUtil

app = Flask(__name__)
api = Api(app)

# 存储任务状态和结果
tasks = {}
# 存储爬虫进程
spider_processes = {}


def get_user_data(id):
    """从Neo4j获取用户数据"""
    try:
        # 查询用户节点
        user_node = NeoUtil.get_node_info(id)
        if not user_node:
            return None
        return user_node
    except Exception as e:
        print(f"Error getting user data: {str(e)}")
        return None
def get_main_node_data():
    """从Neo4j获取关注用户数据"""
    try:
        # 查询用户节点
        main_node = NeoUtil.get_main_node_info()
        if not main_node:
            return None
        return main_node
    except Exception as e:
        print(f"Error getting user data: {str(e)}")
        return None

def get_target_nodes_data():
    """从Neo4j获取关注用户数据"""
    try:
        # 查询用户节点
        target_nodes = NeoUtil.get_target_nodes_info()
        if not target_nodes:
            return None
        return target_nodes
    except Exception as e:
        print(f"Error getting user data: {str(e)}")
        return None

def run_spider(user_id, task_id):
    """在后台运行Scrapy爬虫"""
    try:
        # 切换到WeiboSpider目录
        os.chdir('WeiboSpider')
        
        # 运行Scrapy爬虫
        process = subprocess.Popen(
            ['scrapy', 'crawl', 'WeiboUser', '-a', f'user_id={user_id}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 存储进程信息
        spider_processes[task_id] = process
        
        # 等待爬虫完成
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            # 从Neo4j获取数据
            data = get_user_data(user_id)
            if data:
                tasks[task_id] = {
                    'status': 'completed',
                    'user_data': data['user_data'],
                    'stats': data['stats']
                }
            else:
                tasks[task_id] = {
                    'status': 'failed',
                    'error': '未找到用户数据'
                }
        else:
            tasks[task_id] = {
                'status': 'failed',
                'error': stderr.decode('utf-8')
            }
    except Exception as e:
        tasks[task_id] = {
            'status': 'failed',
            'error': str(e)
        }
    finally:
        # 清理进程信息
        if task_id in spider_processes:
            del spider_processes[task_id]
        # 切回原目录
        os.chdir('..')

@app.route('/')
def anl():
    return render_template('analysis.html')

@app.route('/intro')
def intro():
   return render_template('intro.html')

@app.route('/index')
def index():
   return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/analyze/<user_id>', methods=['POST'])
def analyze_user(user_id):
    """启动用户数据分析任务"""
    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'processing'}
    
    # 在后台线程中运行爬虫
    thread = threading.Thread(target=run_spider, args=(user_id, task_id))
    thread.daemon = True
    thread.start()
    
    return jsonify({'task_id': task_id})

@app.route('/api/task_status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态"""
    if task_id not in tasks:
        return jsonify({'status': 'failed', 'error': '任务不存在'})
    return jsonify(tasks[task_id])

@app.route('/api/spider_status', methods=['GET'])
def get_spider_status():
    if not RedisQueueManager.get_status():
        return jsonify({'status': 'none'})
    else:
        status = RedisQueueManager.get_status()
        if status == "1":
            return jsonify({'status': '爬虫启动中', 'data': RedisQueueManager.get_status()})
        elif status == "2":
            return jsonify({'status': '爬取目标用户中', 'data': RedisQueueManager.get_status()})
        elif status == "3":
            return jsonify({'status': '爬取可能的相似用户中', 'data': RedisQueueManager.get_status()})
        else:
            return jsonify({'status': '爬虫已结束', 'data': RedisQueueManager.get_status()})
@app.route('/api/stop_spider/<task_id>', methods=['POST'])
def stop_spider(task_id):
    """停止指定的爬虫任务"""
    if task_id not in spider_processes:
        return jsonify({
            'status': 'failed',
            'error': '任务不存在或已完成'
        })
    
    try:
        process = spider_processes[task_id]
        # 发送SIGTERM信号
        process.terminate()
        # 等待进程结束
        process.wait(timeout=5)
        
        tasks[task_id] = {
            'status': 'stopped',
            'message': '爬虫已手动停止'
        }
        
        return jsonify({
            'status': 'success',
            'message': '爬虫已停止'
        })
    except Exception as e:
        return jsonify({
            'status': 'failed',
            'error': f'停止爬虫时发生错误: {str(e)}'
        })

@app.route('/api/stop_all_spiders', methods=['POST'])
def stop_all_spiders():
    """停止所有正在运行的爬虫"""
    try:
        stopped_count = 0
        for task_id, process in list(spider_processes.items()):
            try:
                process.terminate()
                process.wait(timeout=5)
                tasks[task_id] = {
                    'status': 'stopped',
                    'message': '爬虫已手动停止'
                }
                stopped_count += 1
            except Exception as e:
                print(f"停止任务 {task_id} 时发生错误: {str(e)}")
        
        return jsonify({
            'status': 'success',
            'message': f'已停止 {stopped_count} 个爬虫任务'
        })
    except Exception as e:
        return jsonify({
            'status': 'failed',
            'error': f'停止爬虫时发生错误: {str(e)}'
        })

@app.route('/api/user_data/<user_id>', methods=['GET'])
def get_user_data_api(user_id):
    try:
        data = get_user_data(user_id)
        if data:
            return jsonify(data)
        return jsonify(None)
    except Exception as e:
        return jsonify({
            'error': f'获取用户数据失败: {str(e)}'
        }), 500

@app.route('/api/main_data', methods=['GET'])
def get_main_data_api():
    try:
        data = get_main_node_data()
        if data:
            return jsonify(data)
        return jsonify(None)
    except Exception as e:
        return jsonify({
            'error': f'获取用户数据失败: {str(e)}'
        }), 500
@app.route('/api/target_data', methods=['GET'])
def get_target_data_api():
    try:
        data = get_target_nodes_data()
        if data:
            return jsonify(data)
        return jsonify(None)
    except Exception as e:
        return jsonify({
            'error': f'获取用户数据失败: {str(e)}'
        }), 500

@app.route('/api/cluster_data', methods=['GET'])
def get_cluster_data_api():
    """获取同聚类节点数据"""
    try:
        # 从Neo4j获取聚类数据
        cluster_nodes = DataAnalysis.get_same_cluster_nodes()
        if cluster_nodes:
            return jsonify(cluster_nodes)
        return jsonify(None)
    except Exception as e:
        return jsonify({
            'error': f'获取聚类数据失败: {str(e)}'
        }), 500

@app.route('/api/user_stats', methods=['GET'])
def get_user_stats_api():
    """获取所有用户的性别和地区统计信息"""
    try:

        # 获取所有User节点
        users = NeoUtil.get_user_nodes_info()
        
        # 初始化统计数据结构
        stats = {
            'gender': {
                'm': 0,  # 男性
                'f': 0,  # 女性
                'unknown': 0  # 未知
            },
            'location': {},  # 地区统计
            'total_users': len(users)
        }
        
        # 统计性别和地区
        for user in users:
            # 统计性别
            gender = user.get('gender', 'unknown')
            if gender not in ['m', 'f']:
                gender = 'unknown'
            stats['gender'][gender] += 1
            
            # 统计地区
            location = user.get('location', '未知')
            
            if location in stats['location']:
                stats['location'][location] += 1
            else:
                stats['location'][location] = 1
        
        # 对地区统计进行排序，只返回前20个地区
        sorted_locations = sorted(
            stats['location'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]
        stats['location'] = dict(sorted_locations)
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取统计数据失败: {str(e)}'
        }), 500

@app.route('/api/avatar', methods=['GET'])
def get_avatar_base64():
    """获取用户头像的base64编码"""
    try:
        # 从请求参数获取头像URL
        avatar_url = request.args.get('url')
        if not avatar_url:
            return jsonify({
                'status': 'error',
                'message': '未提供头像URL'
            }), 400

        # 下载头像
        response = requests.get(avatar_url)
        if response.status_code != 200:
            return jsonify({
                'status': 'error',
                'message': '下载头像失败'
            }), 500

        # 转换为base64
        image_data = base64.b64encode(response.content).decode('utf-8')
        
        return jsonify({
            'status': 'success',
            'data': {
                'base64': image_data,
                'content_type': response.headers.get('content-type', 'image/jpeg')
            }
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'获取头像失败: {str(e)}'
        }), 500

parser = reqparse.RequestParser()
parser.add_argument('userId', type=int, help='Rate to charge for this resource')

class UserInfo(Resource):
    def get(self):
        args = parser.parse_args()
        print(args)

api.add_resource(UserInfo, '/anl/user')
# @app.route('/anl/user', methods=["GET","POST"])
# def anl_user():
#     json_value = request.get_json()
#     print(json_value['input'])
# # 发送数据
#     info = dict()
#     info["status"] = "success"
#     info["page"] = "/test/lyshark"
#     return jsonify(info)

if __name__ == '__main__':
    app.run(debug=True)