
from py2neo import Graph, Subgraph, NodeMatcher, RelationshipMatcher
from py2neo import Node, Relationship, Path

class NeoUtil:
    graph = Graph('bolt://localhost:7687', auth=('neo4j', '123456'))
    nodes_matcher = NodeMatcher(graph)
    relationships_matcher = RelationshipMatcher(graph)

    # 删除所有已有节点
    @classmethod
    def clear(cls):
        cls.graph.delete_all()
    @classmethod
    def try_add_node(cls, item):

        domain = cls.nodes_matcher.match("User", id=item['domain']).first()
        user: Node = None
        if not cls.nodes_matcher.match("User", id=item['id']).exists():
            user = Node("User", id=item['id'], name=item['name'], gender=item['gender'],
                        followers_count=item['followers_count'], province=item['province'], city=item['city'],
                        location=item['location'], description=item['description'], created_at=item['created_at'],
                        avatar_img=item['avatar_img'])

            cls.graph.create(user)
        else:
            user = cls.nodes_matcher.match("User", id=item['id']).first()
        print(user)
        print(domain)
        user_to_domain = Relationship(user, '关注', domain)

        cls.graph.create(user_to_domain)

NeoUtil.clear()