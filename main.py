
import py2neo
from py2neo import Graph, Subgraph, NodeMatcher, RelationshipMatcher
from py2neo import Node, Relationship, Path
from py2neo.cypher import Record
from pyasn1_modules.rfc2985 import gender

import matplotlib.pyplot as plt

graph = Graph('bolt://localhost:7687', auth=('neo4j', '123456'))
nodes_matcher = NodeMatcher(graph)
relationships_matcher = RelationshipMatcher(graph)
targetId = 1640601392

max_fans = 0

# 步骤 1: 计算用户相似度分数（需预定义权重参数）
def proc1_calculate_similar_score():
    target = nodes_matcher.match("User", id=targetId).first()
    users = nodes_matcher.match("User")
    min_fans = 9999999999
    max_fans = 0
    for u in users:
        if u['id'] == targetId:
            continue
        if u['followers_count']:
            min_fans = min(min_fans,u['followers_count'])
            max_fans = max(max_fans,u['followers_count'])
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
        range = max_fans -  min_fans + 0.0001;
        #uFansNorm in [0,1]
        if u['followers_count']:
            fans_norm = (u['followers_count'] - min_fans) / range
        else:
            fans_norm = 0.01

        #权重
        similarity_score = is_region_same * 0.4 + is_gender_same * 0.2 + fans_norm * 0.4
        u['similarity'] = similarity_score
        graph.push(u)


# 步骤 2: 计算图结构距离（关注关系的最短路径）
def proc2_calculate_shortest_path():
    query = """
    MATCH (target:User {{id: {}}})
    MATCH (u:User)
    OPTIONAL MATCH path = shortestPath((target)-[:关注*..20]-(u))
    RETURN path,u.id
    """.format(targetId)
    res = graph.run(query)
    for r in res:
        path:Record = r[0]
        destiny = r[1]
        distance = 0
        for node in path:
            if node['id'] == targetId or node['id'] == destiny:
                continue
            if not node['followers_count']:
                node['followers_count'] = 10000000
            distance += 1-(float(node['followers_count']-10000000) / (max_fans-10000000))
            print(distance)
    users = nodes_matcher.match("User")
    max_distance = 0
    for u in users:
        print(u['distance'])
        if u['distance'] !=1000:
            max_distance = max(max_distance,u['distance'])
    max_distance *=2
    for u in users:
        if u['distance'] ==1000:
            u['normal_distance'] = 1
        else:
            u['normal_distance'] = float(u['distance']) / max_distance
        graph.push(u)

# 步骤 3: 将两个属性加入特征向量
def proc3_calculate_vector():
    users = nodes_matcher.match("User")
    for u in users:
        u['refer_vector'] = [u['similarity'],u['normal_distance']]
        graph.push(u)
    label = []
    x = []
    y = []
    for u in users:
        label.append(u['name'])
        x.append(u['refer_vector'][0])
        y.append(u['refer_vector'][1])

    plt.plot(x, y,'o')
    plt.show()

# 步骤 4: 创建内存投影图
def proc3_create_project():
    res = graph.run("""
    CALL gds.graph.drop('user_cluster')
    CALL gds.graph.project(
    'user_cluster',
    'User',
    '关注',
    {nodeProperties: 'refer_vector' }
    );
    """)
# 步骤 4: 执行 k-means 聚类分析
def proc4_kmeans_analysis():
    res = graph.run("""
    CALL gds.kmeans.write(
    'user_cluster',
    {
    nodeProperty: 'refer_vector',
    k: 5,
    randomSeed: 42 ,            // 固定随机种子
    writeProperty: 'clusterId'  // 结果写入属性
    }
    )
    """)

proc1_calculate_similar_score()
proc2_calculate_shortest_path()
proc3_calculate_vector()
# proc4_create_project()
# proc5_kmeans_analysis()