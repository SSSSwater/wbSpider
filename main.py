import py2neo
from py2neo import Graph, Subgraph, NodeMatcher
from py2neo import Node, Relationship, Path




# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    graph = Graph('bolt://localhost:7687', auth=('neo4j', '123456'))
    nodes = NodeMatcher(graph)
    res = graph.run("""MATCH (u:User {id: 1640601392})
MATCH (candidate:User)
WHERE candidate <> u AND NOT (u)-[:关注]->(candidate)
WITH u, candidate

OPTIONAL MATCH (u)-[:关注]->(followed:User)-[:关注]->(candidate)
WITH u, candidate, COUNT(followed) AS common_followers

WITH u, candidate, common_followers,
     CASE WHEN candidate.province = u.province THEN 10 ELSE 0 END AS province_score,
     candidate.followers_count AS followers
     
WITH candidate,
     (common_followers * 5) + province_score + (followers / 10000000) AS total_score
ORDER BY total_score DESC
RETURN candidate,total_score
LIMIT 100""")
    print(res)

