import matplotlib.pyplot as plt
from py2neo import Graph, NodeMatcher, RelationshipMatcher
from py2neo import Node
from py2neo.cypher import Record


class Analysis:
    min_fans = 999999999
    max_fans = 0
    graph = Graph('bolt://localhost:7687', auth=('neo4j', '123456'))
    nodes_matcher = NodeMatcher(graph)
    relationships_matcher = RelationshipMatcher(graph)
    targetId = 1640601392
    # 步骤 1: 计算用户相似度分数（需预定义权重参数）
    def proc1_calculate_similar_score(self):
        target = self.nodes_matcher.match("User", id=self.targetId).first()
        users = self.nodes_matcher.match("User")
        self.min_fans = 9999999999
        self.max_fans = 0
        for u in users:
            if u['id'] == self.targetId:
                continue
            if u['followers_count']:
                self.min_fans = min(self.min_fans,u['followers_count'])
                self.max_fans = max(self.max_fans,u['followers_count'])
        for u in users:
            if u['province'] == target['province'] and u['province']:
                if u['city'] == target['city'] and u['city']:
                    is_region_same = 1
                else:
                    is_region_same = 0.4
            else:
                is_region_same = 0.1;
            if u['gender'] == target['gender']:
                is_gender_same = 1
            else:
                is_gender_same = 0
            range = self.max_fans -  self.min_fans + 0.0001;
            #uFansNorm in [0,1]
            if u['followers_count']:
                fans_norm = (u['followers_count'] - self.min_fans) / range
            else:
                fans_norm = 0.01

            #权重
            similarity_score = is_region_same * 0.4 + is_gender_same * 0.2 + fans_norm * 0.4
            u['similarity'] = similarity_score
            self.graph.push(u)

    # 步骤 2: 计算图结构距离（关注关系的最短路径）
    def proc2_calculate_shortest_path(self):
        query = """
        MATCH (target:User {{id: {}}})
        MATCH (u:User)
        OPTIONAL MATCH path = shortestPath((target)-[:关注*..20]-(u))
        RETURN NODES(path),u
        """.format(self.targetId)
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
            u['refer_vector'] = [u['similarity'], u['normal_distance']]
            self.graph.push(u)

    # 步骤 4: 创建内存投影图
    def proc4_create_project(self):
        res = self.graph.run("""
        CALL gds.graph.project(
        'user_cluster',
        'User',
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
        target_node = self.nodes_matcher.match("User", id = self.targetId).first()
        users = self.nodes_matcher.match("User", clusterId = target_node['clusterId']).all()
        return users

    def procT_show_node_figure(self):
        users = self.nodes_matcher.match("User")
        label = []
        x = []
        y = []
        for u in users:
            label.append(u['clusterId'])
            x.append(u['refer_vector'][0])
            y.append(u['refer_vector'][1])

        cid2co = ['g','b','k','m','r','c']

        plt.scatter(x, y, marker='o',c=[cid2co[i] for i in label])
        plt.show()

ana = Analysis()
ana.proc1_calculate_similar_score()
ana.proc2_calculate_shortest_path()
ana.proc3_calculate_vector()
ana.proc4_create_project()
ana.proc5_kmeans_analysis()
ana.proc6_del_project()
users = ana.proc7_get_nodes_in_same_cluster()
for u in users:
    print(u['name'])
# ana.procT_show_node_figure()
