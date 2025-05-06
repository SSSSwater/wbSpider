import matplotlib.pyplot as plt
from py2neo import Graph, NodeMatcher, RelationshipMatcher
from py2neo import Node
from py2neo.cypher import Record


def jaccard(list1, list2):
    intersection = len(list(set(list1).intersection(list2)))
    union = (len(list1) + len(list2)) - intersection
    return float(intersection) / union


class Analysis:
    min_fans = 999999999
    max_fans = 0
    graph = Graph('bolt://localhost:7687', auth=('neo4j', '123456'))
    nodes_matcher = NodeMatcher(graph)
    relationships_matcher = RelationshipMatcher(graph)
    targetId = 5997871169

    # 步骤 1: 计算用户相似度分数
    def proc1_calculate_similar_score(self):
        main_node = self.nodes_matcher.match("Main").first()
        main_node['basic_similarity'] = 1
        main_node['area_similarity'] = 1
        self.graph.push(main_node)
        targets = self.nodes_matcher.match("Target").all()
        users = self.nodes_matcher.match("User")
        
        # 计算粉丝数范围
        self.min_fans = 9999999999
        self.max_fans = 0
        for u in users:
            if u['id'] == self.targetId:
                continue
            if u['followers_count']:
                self.min_fans = min(self.min_fans, u['followers_count'])
                self.max_fans = max(self.max_fans, u['followers_count'])

        for u in users:
            # 1. 地理位置相似度
            region_similarity = 0
            for t in targets:
                if u['province'] == t['province'] and u['province']:
                    if u['city'] == t['city'] and u['city']:
                        region_similarity += 1.0 / len(targets)  # 完全匹配
                    else:
                        region_similarity += 0.6 / len(targets)  # 省份匹配
                else:
                    region_similarity += 0.2 / len(targets)  # 不匹配

            # 2. 性别相似度
            gender_similarity = 0
            for t in targets:
                if u['gender'] == t['gender']:
                    gender_similarity += 1.0 / len(targets)  # 性别匹配
                else:
                    gender_similarity += 0.0 / len(targets)  # 性别不匹配

            # 3. 认证信息相似度
            verified_similarity = 0
            for t in targets:
                if u['verified_type'] == t['verified_type']:
                    if t['verified_type'] == -1:  # 未认证
                        verified_similarity += 0.3 / len(targets)
                    elif t['verified_type'] != 0:  # 少推点官号
                        verified_similarity += 0.1 / len(targets)
                    else:  # 个人认证
                        verified_similarity += (0.5 + 0.5 * jaccard(u['verified_detail_key'], t['verified_detail_key'])) / len(targets)
                else:
                    if t['verified_type'] == -1:
                        verified_similarity += 0.1 / len(targets)
                    elif t['verified_type'] != 0:
                        verified_similarity += 0.3 / len(targets)
                    else:
                        verified_similarity += 0.2 / len(targets)

            # 4. 粉丝数相似度
            fans_similarity = 0
            for t in targets:
                if u['followers_count'] and t['followers_count']:
                    ratio = min(u['followers_count'], t['followers_count']) / max(u['followers_count'], t['followers_count'])
                    fans_similarity += ratio / len(targets)
                else:
                    fans_similarity += 0.1 / len(targets)

            # 5. 微博数相似度
            weibo_similarity = 0
            for t in targets:
                if u['statuses_count'] and t['statuses_count']:
                    ratio = min(u['statuses_count'], t['statuses_count']) / max(u['statuses_count'], t['statuses_count'])
                    weibo_similarity += ratio / len(targets)
                else:
                    weibo_similarity += 0.1 / len(targets)

            # 6. 关注数相似度
            following_similarity = 0
            for t in targets:
                if u['friends_count'] and t['friends_count']:
                    ratio = min(u['friends_count'], t['friends_count']) / max(u['friends_count'], t['friends_count'])
                    following_similarity += ratio / len(targets)
                else:
                    following_similarity += 0.1 / len(targets)

            # 7. 简介相似度
            description_similarity = 0
            for t in targets:
                if u['description'] and t['description']:
                    # 计算简介关键词的重叠度
                    u_words = set(u['description'].split())
                    t_words = set(t['description'].split())
                    if u_words and t_words:
                        description_similarity += (0.5+0.5*jaccard(u_words, t_words)) / len(targets)
                else:
                    description_similarity += 0.1 / len(targets)

            # 综合相似度计算（调整权重）
            basic_similarity = (
                region_similarity * 0.20 +      # 地理位置权重
                gender_similarity * 0.15 +      # 性别权重
                fans_similarity * 0.35 +             # 粉丝数权重
                weibo_similarity * 0.15 +      # 微博数权重
                following_similarity * 0.15   # 关注数权重
            )
            area_similarity = (
                verified_similarity * 0.40 +    # 认证信息权重
                description_similarity * 0.60   # 简介相似度权重
            )

            # 保存相似度分数
            u['basic_similarity'] = basic_similarity
            u['area_similarity'] = area_similarity
            self.graph.push(u)

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
            u['refer_vector'] = [float(u['basic_similarity']), float(u['area_similarity'])]
            self.graph.push(u)
        main_node = self.nodes_matcher.match("Main").first()
        main_node['refer_vector'] = [float(main_node['basic_similarity']), float(main_node['area_similarity'])]
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
        k: 6,
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

# ana = Analysis()
# print(get_same_cluster_nodes())