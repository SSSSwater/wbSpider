import time

import matplotlib.pyplot as plt
from py2neo import Graph, NodeMatcher, RelationshipMatcher
from py2neo import Node
from py2neo.cypher import Record
from functools import lru_cache
import numpy as np
from concurrent.futures import ThreadPoolExecutor, Future
from typing import List, Dict, Set, Tuple


@lru_cache(maxsize=1000)
def jaccard(list1: tuple, list2: tuple) -> float:
    """
    使用缓存优化的Jaccard相似度计算
    Args:
        list1: 第一个集合（转换为元组）
        list2: 第二个集合（转换为元组）
    Returns:
        float: Jaccard相似度值
    """
    intersection = len(set(list1).intersection(set(list2)))
    union = (len(list1) + len(list2)) - intersection
    return float(intersection) / union if union > 0 else 0.0


class Analysis:
    """
    数据分析主类，负责用户相似度计算和聚类分析
    """

    def __init__(self):
        """
        初始化分析器，连接Neo4j数据库并设置基本参数
        """
        self.graph = Graph('bolt://localhost:7687', auth=('neo4j', '123456'))
        self.nodes_matcher = NodeMatcher(self.graph)
        self.relationships_matcher = RelationshipMatcher(self.graph)
        self.targetId = 5997871169  # 目标用户ID
        self.min_fans = float('inf')  # 最小粉丝数
        self.max_fans = 0  # 最大粉丝数
        self._cache = {}  # 缓存字典
        self.futures = []  # 线程池任务列表

    def _get_all_users_data(self) -> List[Dict]:
        """
        从Neo4j获取所有用户数据
        Returns:
            List[Dict]: 用户数据列表
        """
        query = """
        MATCH (u:User)
        RETURN u
        """
        return [record['u'] for record in self.graph.run(query)]

    def _get_targets_data(self) -> List[Dict]:
        """
        从Neo4j获取目标用户数据
        Returns:
            List[Dict]: 目标用户数据列表
        """
        query = """
        MATCH (t:Target)
        RETURN t
        """
        return [record['t'] for record in self.graph.run(query)]

    def _calculate_similarity_batch(self, user: Dict, targets: List[Dict]) -> Tuple[float, float]:
        """
        批量计算单个用户与所有目标用户的相似度
        Args:
            user: 待计算用户数据
            targets: 目标用户数据列表
        Returns:
            Tuple[float, float]: (基础相似度, 领域相似度)
        """
        region_similarity = 0;
        gender_similarity = 0;
        verified_similarity = 0;
        fans_similarity = 0;
        weibo_similarity = 0;
        following_similarity = 0;
        description_similarity = 0;
        for t in targets:
            # 1. 地理位置相似度计算
            region_similarity += (
                1.0 / len(targets) if user['province'] == t['province'] and user['city'] == t['city'] and user[
                    'province'] and user['city']
                else 0.6 / len(targets) if user['province'] == t['province'] and user['province']
                else 0.2 / len(targets)
            )
            # 2. 性别相似度计算
            gender_similarity += (
                1.0 / len(targets) if user['gender'] == t['gender']
                else 0.0
            )
            # 3. 认证信息相似度计算
            verified_similarity += (
                (0.5 + 0.5 * jaccard(tuple(user['verified_detail_key']), tuple(t['verified_detail_key']))) / len(targets)
                if user['verified_type'] == t['verified_type'] and t['verified_type'] == 0
                else 0.3 / len(targets) if user['verified_type'] == t['verified_type'] and t['verified_type'] == -1
                else 0.1 / len(targets) if user['verified_type'] == t['verified_type'] and t['verified_type'] != 0
                else 0.1 / len(targets) if t['verified_type'] == -1
                else 0.3 / len(targets) if t['verified_type'] != 0
                else 0.2 / len(targets)
            )
            # 4. 粉丝数相似度计算
            fans_similarity += (
                min(user['followers_count'], t['followers_count']) / max(user['followers_count'],
                                                                        t['followers_count']) / len(targets)
                if user['followers_count'] and t['followers_count']
                else 0.1 / len(targets)
            )
            # 5. 微博数相似度计算
            weibo_similarity += (
                min(user['statuses_count'], t['statuses_count']) / max(user['statuses_count'], t['statuses_count']) / len(
                    targets)
                if user['statuses_count'] and t['statuses_count']
                else 0.1 / len(targets)
            )
            # 6. 关注数相似度计算
            following_similarity += (
                min(user['friends_count'], t['friends_count']) / max(user['friends_count'], t['friends_count']) / len(
                    targets)
                if user['friends_count'] and t['friends_count']
                else 0.1 / len(targets)
            )
            # 7. 简介相似度计算
            description_similarity += (
                (0.5 + 0.5 * jaccard(tuple(user['description'].split()), tuple(t['description'].split()))) / len(targets)
                if user['description'] and t['description']
                else 0.1 / len(targets)
            )

        # 计算综合相似度（基础特征）
        basic_similarity = (
                region_similarity * 0.20 +  # 地理位置权重
                gender_similarity * 0.15 +  # 性别权重
                fans_similarity * 0.35 +    # 粉丝数权重
                weibo_similarity * 0.15 +   # 微博数权重
                following_similarity * 0.15 # 关注数权重
        )

        # 计算领域相似度（专业特征）
        area_similarity = (
                verified_similarity * 0.40 +     # 认证信息权重
                description_similarity * 0.60    # 简介相似度权重
        )

        return basic_similarity, area_similarity

    def proc1_calculate_similar_score(self):
        """
        步骤1: 计算所有用户的相似度分数
        使用线程池并行处理提高性能
        """
        # 批量获取数据
        users = self._get_all_users_data()
        targets = self._get_targets_data()

        # 计算粉丝数范围
        self.min_fans = min(u['followers_count'] for u in users if u['id'] != self.targetId and u['followers_count'])
        self.max_fans = max(u['followers_count'] for u in users if u['id'] != self.targetId and u['followers_count'])

        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=4) as executor:
            self.futures = []
            for user in users:
                if user['id'] == self.targetId:
                    user['basic_similarity'] = 1
                    user['area_similarity'] = 1
                    self.graph.push(user)
                    continue
                self.futures.append(executor.submit(self._calculate_similarity_batch, user, targets))
            # 批量更新数据库
            batch_size = 100
            updates = []
            for i, future in enumerate(self.futures):
                basic_similarity, area_similarity = future.result()
                user = users[i]
                user['basic_similarity'] = basic_similarity
                user['area_similarity'] = area_similarity
                updates.append(user)

                if len(updates) >= batch_size:
                    for u in updates:
                        self.graph.push(u)
                    updates = []

            if updates:
                for u in updates:
                    self.graph.push(u)

    # def proc2_calculate_shortest_path(self):
    #     """
    #     计算用户间的最短路径距离
    #     注意：此方法当前未使用，保留代码以供后续优化
    #     """
    #     query = """
    #     MATCH (target:Main)
    #     MATCH (u:User)
    #     OPTIONAL MATCH path = shortestPath((target)-[:关注*..20]-(u))
    #     RETURN NODES(path),u
    #     """
    #     res = self.graph.run(query)
    #     for r in res:
    #         path: Record = r[0]
    #         destiny = r[1]
    #         distance = 0
    #         if not path:
    #             distance = 1000
    #         else:
    #             node: Node
    #             for node in path:
    #                 if node['id'] == self.targetId or node['id'] == destiny['id']:
    #                     continue
    #                 if not node['followers_count']:
    #                     node['followers_count'] = 5000000
    #                 distance += 1 - (float(node['followers_count'] - 5000000) / float(self.max_fans - 5000000))
    #         destiny['distance'] = distance
    #         self.graph.push(destiny)
    #     users = self.nodes_matcher.match("User")
    #     max_distance = 0
    #     for u in users:
    #         print(max_distance, u['distance'], u['name'])
    #         if u['distance'] != 1000:
    #             max_distance = max(max_distance, u['distance'])
    #     max_distance *= 2
    #     for u in users:
    #         if u['distance'] == 1000:
    #             u['normal_distance'] = 1
    #         else:
    #             u['normal_distance'] = float(u['distance']) / max_distance
    #         self.graph.push(u)

    def judge_proc1_completed(self):
        """
        等待所有相似度计算线程完成
        """
        while True:
            flag = True
            for f in self.futures:
                if not f.done():
                    flag = False
                    break
            if flag:
                break
            else:
                time.sleep(0.2)

    def proc3_calculate_vector(self):
        """
        步骤3: 将相似度属性加入特征向量
        """
        # 等待所有相似度线程计算完成
        self.judge_proc1_completed()
        users = self.nodes_matcher.match("User")
        for u in users:
            u['refer_vector'] = [float(u['basic_similarity']), float(u['area_similarity'])]
            self.graph.push(u)
        main_node = self.nodes_matcher.match("Main").first()
        main_node['refer_vector'] = [float(1.0), float(1.0)]
        self.graph.push(main_node)

    def proc4_create_project(self):
        """
        步骤4: 创建Neo4j内存投影图
        用于后续的图算法分析
        """
        # 如果存在投影图，则删除
        res = self.graph.run("""
        CALL gds.graph.exists('user_cluster')
        YIELD exists 
        """)
        if res.data()[0]['exists']:
            self.graph.run("""
                    CALL gds.graph.drop('user_cluster')
                    """)
        
        # 创建投影图
        res = self.graph.run("""
        CALL gds.graph.project(
        'user_cluster',
        ['User','Main'],
        '关注',
        {nodeProperties: 'refer_vector' }
        );
        """)

    def proc5_kmeans_analysis(self):
        """
        步骤5: 执行k-means聚类分析
        使用Neo4j的图数据科学库进行聚类
        """
        res = self.graph.run("""
        CALL gds.kmeans.write(
        'user_cluster',
        {
        nodeProperty: 'refer_vector',
        k: 4,
        randomSeed: 42 ,            // 固定随机种子
        writeProperty: 'clusterId'  // 结果写入属性
        }
        )
        """)

    def proc6_del_project(self):
        """
        步骤6: 删除投影图
        避免与后续操作冲突
        """
        res = self.graph.run("""
        CALL gds.graph.drop('user_cluster')
        """)

    def proc7_get_nodes_in_same_cluster(self):
        """
        步骤7: 获取与目标用户在同一聚类的其他节点
        Returns:
            List[Node]: 同聚类用户节点列表
        """
        target_node = self.nodes_matcher.match("Main").first()
        users = self.nodes_matcher.match("User", clusterId=target_node['clusterId']).all()
        return users

    def procT_show_node_figure(self):
        """
        可视化聚类结果
        使用matplotlib绘制散点图
        """
        main_node = self.nodes_matcher.match("Main").first()
        users = self.nodes_matcher.match("User")
        label = []
        x = []
        y = []
        label.append(main_node['clusterId'])
        x.append(main_node['refer_vector'][0])
        y.append(main_node['refer_vector'][1])
        for u in users:
            label.append(u['clusterId'])
            x.append(u['refer_vector'][0])
            y.append(u['refer_vector'][1])

        cid2co = ['g', 'b', 'k', 'm', 'r', 'c']

        plt.scatter(x, y, marker='o', c=[cid2co[i] for i in label])
        plt.show()


def get_same_cluster_nodes():
    """
    获取同聚类节点的主函数
    Returns:
        List[Node]: 同聚类用户节点列表
    """
    ana = Analysis()
    ana.proc1_calculate_similar_score()
    # ana.proc2_calculate_shortest_path()
    ana.proc3_calculate_vector()
    ana.proc4_create_project()
    ana.proc5_kmeans_analysis()
    ana.proc6_del_project()
    users = ana.proc7_get_nodes_in_same_cluster()
    # ana.procT_show_node_figure()
    return users


def show_cluster_figure():
    """
    显示聚类结果可视化图
    """
    ana = Analysis()
    ana.procT_show_node_figure()

start = time.time()
print(get_same_cluster_nodes())
print(time.time() - start)
# show_cluster_figure()
