import matplotlib.pyplot as plt
from py2neo import Graph, NodeMatcher, RelationshipMatcher
from py2neo import Node
from py2neo.cypher import Record
from functools import lru_cache
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Set, Tuple

@lru_cache(maxsize=1000)
def jaccard(list1: tuple, list2: tuple) -> float:
    """使用缓存优化的Jaccard相似度计算"""
    intersection = len(set(list1).intersection(set(list2)))
    union = (len(list1) + len(list2)) - intersection
    return float(intersection) / union if union > 0 else 0.0


class Analysis:

    def __init__(self):
        self.graph = Graph('bolt://localhost:7687', auth=('neo4j', '123456'))
        self.nodes_matcher = NodeMatcher(self.graph)
        self.relationships_matcher = RelationshipMatcher(self.graph)
        self.targetId = 5997871169
        self.min_fans = float('inf')
        self.max_fans = 0
        self._cache = {} 
    def _get_all_users_data(self) -> List[Dict]:
        """批量获取所有用户数据"""
        query = """
        MATCH (u:User)
        RETURN u
        """
        return [record['u'] for record in self.graph.run(query)]

    def _get_targets_data(self) -> List[Dict]:
        """批量获取目标用户数据"""
        query = """
        MATCH (t:Target)
        RETURN t
        """
        return [record['t'] for record in self.graph.run(query)]
    def _calculate_similarity_batch(self, user: Dict, targets: List[Dict]) -> Tuple[float, float]:
        """批量计算单个用户与所有目标用户的相似度"""
        # 1. 地理位置相似度
        region_similarity = sum(
            1.0 / len(targets) if user['province'] == t['province'] and user['city'] == t['city'] and user['province'] and user['city']
            else 0.6 / len(targets) if user['province'] == t['province'] and user['province']
            else 0.2 / len(targets)
            for t in targets
        )
        # 2. 性别相似度
        gender_similarity = sum(
            1.0 / len(targets) if user['gender'] == t['gender']
            else 0.0
            for t in targets
        )
        # 3. 认证信息相似度
        verified_similarity = sum(
            (0.5 + 0.5 * jaccard(tuple(user['verified_detail_key']), tuple(t['verified_detail_key']))) / len(targets)
            if user['verified_type'] == t['verified_type'] and t['verified_type'] == 0
            else 0.3 / len(targets) if user['verified_type'] == t['verified_type'] and t['verified_type'] == -1
            else 0.1 / len(targets) if user['verified_type'] == t['verified_type'] and t['verified_type'] != 0
            else 0.1 / len(targets) if t['verified_type'] == -1
            else 0.3 / len(targets) if t['verified_type'] != 0
            else 0.2 / len(targets)
            for t in targets
        )
        # 4. 粉丝数相似度
        fans_similarity = sum(
            min(user['followers_count'], t['followers_count']) / max(user['followers_count'], t['followers_count']) / len(targets)
            if user['followers_count'] and t['followers_count']
            else 0.1 / len(targets)
            for t in targets
        )
        # 5. 微博数相似度
        weibo_similarity = sum(
            min(user['statuses_count'], t['statuses_count']) / max(user['statuses_count'], t['statuses_count']) / len(targets)
            if user['statuses_count'] and t['statuses_count']
            else 0.1 / len(targets)
            for t in targets
        )
        # 6. 关注数相似度
        following_similarity = sum(
            min(user['friends_count'], t['friends_count']) / max(user['friends_count'], t['friends_count']) / len(targets)
            if user['friends_count'] and t['friends_count']
            else 0.1 / len(targets)
            for t in targets
        )
        # 7. 简介相似度
        description_similarity = sum(
            (0.5 + 0.5 * jaccard(tuple(user['description'].split()), tuple(t['description'].split()))) / len(targets)
            if user['description'] and t['description']
            else 0.1 / len(targets)
            for t in targets
        )

        # 计算综合相似度
        basic_similarity = (
            region_similarity * 0.20 +
            gender_similarity * 0.15 +
            fans_similarity * 0.35 +
            weibo_similarity * 0.15 +
            following_similarity * 0.15
        )

        area_similarity = (
            verified_similarity * 0.40 +
            description_similarity * 0.60
        )

        return basic_similarity, area_similarity

    # 步骤 1: 计算用户相似度分数
    def proc1_calculate_similar_score(self):
        """优化后的相似度计算"""
        # 批量获取数据
        users = self._get_all_users_data()
        targets = self._get_targets_data()
        
        # 计算粉丝数范围
        self.min_fans = min(u['followers_count'] for u in users if u['id'] != self.targetId and u['followers_count'])
        self.max_fans = max(u['followers_count'] for u in users if u['id'] != self.targetId and u['followers_count'])

        for user in users:
            if user['id'] == self.targetId:
                user['basic_similarity'] = 1
                user['area_similarity'] = 1
                self.graph.push(user)
                continue
            basic_similarity, area_similarity = self._calculate_similarity_batch(user,targets)
            user['basic_similarity'] = basic_similarity
            user['area_similarity'] = area_similarity
            self.graph.push(user)
        # 使用线程池并行处理
        # with ThreadPoolExecutor(max_workers=4) as executor:
        #     futures = []
        #
        #         futures.append(executor.submit(self._calculate_similarity_batch, user, targets))
        #     # 批量更新数据库
        #     batch_size = 100
        #     updates = []
        #     for i, future in enumerate(futures):
        #         basic_similarity, area_similarity = future.result()
        #         user = users[i]
        #         user['basic_similarity'] = basic_similarity
        #         user['area_similarity'] = area_similarity
        #         updates.append(user)
        #
        #         if len(updates) >= batch_size:
        #             for u in updates:
        #                 self.graph.push(u)
        #             updates = []
        #
        #     if updates:
        #         for u in updates:
        #             self.graph.push(u)

    # 步骤 2: 计算图结构距离（关注关系的最短路径）
    def proc2_calculate_shortest_path(self):
        query = """
        MATCH (target:Main)
        MATCH (u:User)
        OPTIONAL MATCH path = shortestPath((target)-[:关注*..20]-(u))
        RETURN NODES(path),u
        """
        res = self.graph.run(query)
        for r in res:
            path: Record = r[0]
            destiny = r[1]
            distance = 0
            if not path:
                distance = 1000
            else:
                node: Node
                for node in path:
                    if node['id'] == self.targetId or node['id'] == destiny['id']:
                        continue
                    if not node['followers_count']:
                        node['followers_count'] = 5000000
                    distance += 1 - (float(node['followers_count'] - 5000000) / float(self.max_fans - 5000000))
            destiny['distance'] = distance
            self.graph.push(destiny)
        users = self.nodes_matcher.match("User")
        max_distance = 0
        for u in users:
            print(max_distance, u['distance'], u['name'])
            if u['distance'] != 1000:
                max_distance = max(max_distance, u['distance'])
        max_distance *= 2
        for u in users:
            if u['distance'] == 1000:
                u['normal_distance'] = 1
            else:
                u['normal_distance'] = float(u['distance']) / max_distance
            self.graph.push(u)

    # 步骤 3: 将两个属性加入特征向量
    def proc3_calculate_vector(self):
        users = self.nodes_matcher.match("User")
        for u in users:
            if not u['basic_similarity']:
                print(u['name'])

            u['refer_vector'] = [float(u['basic_similarity']) ,float(u['area_similarity'])]
            self.graph.push(u)
        main_node = self.nodes_matcher.match("Main").first()
        main_node['refer_vector'] = [float(1.0), float(1.0)]
        self.graph.push(main_node)

    # 步骤 4: 创建内存投影图
    def proc4_create_project(self):
        res = self.graph.run("""
        CALL gds.graph.exists('user_cluster')
        YIELD exists 
        """)
        if res.data()[0]['exists']:
            self.graph.run("""
                    CALL gds.graph.drop('user_cluster')
                    """)
        res = self.graph.run("""
        CALL gds.graph.project(
        'user_cluster',
        ['User','Main'],
        '关注',
        {nodeProperties: 'refer_vector' }
        );
        """)

    # 步骤 5: 执行 k-means 聚类分析
    def proc5_kmeans_analysis(self):
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

    # 步骤 6: 删除投影，避免二次冲突
    def proc6_del_project(self):
        res = self.graph.run("""
        CALL gds.graph.drop('user_cluster')
        """)

    # 步骤 7: 通过id获取同聚类的其他node
    def proc7_get_nodes_in_same_cluster(self):
        target_node = self.nodes_matcher.match("Main").first()
        users = self.nodes_matcher.match("User", clusterId=target_node['clusterId']).all()
        return users

    def procT_show_node_figure(self):
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

    ana = Analysis()
    ana.procT_show_node_figure()

# print(get_same_cluster_nodes())
# show_cluster_figure()