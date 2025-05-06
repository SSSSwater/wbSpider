from py2neo import Graph, Subgraph, NodeMatcher, RelationshipMatcher
from py2neo import Node, Relationship, Path

from .RequestUtil import get_info

class NeoUtil:
    graph = Graph('bolt://localhost:7687', auth=('neo4j', '123456'))
    nodes_matcher = NodeMatcher(graph)
    relationships_matcher = RelationshipMatcher(graph)

    main_node: Node = None

    # 删除所有已有节点
    @classmethod
    def clear(cls):
        cls.graph.delete_all()

    @classmethod
    def get_node_info(cls,id):
        info = cls.nodes_matcher.match(id=id).first()
        return info

    @classmethod
    def get_main_node_info(cls):
        info = cls.nodes_matcher.match('Main').first()
        return info
    @classmethod
    def get_user_nodes_info(cls):
        infos = cls.nodes_matcher.match('User').all()
        return infos
    @classmethod
    def get_target_nodes_info(cls):
        infos = cls.nodes_matcher.match('Target').all()
        return infos
    @classmethod
    def convert_item_to_node(cls,label,item):
        node = Node(label, id=item['id'], name=item['name'], gender=item['gender'],
                    followers_count=item['followers_count'], province=item['province'], city=item['city'],
                    location=item['location'], verified_type=item['verified_type'], verified_detail_key=item['verified_detail_key'], verified_detail_desc=item['verified_detail_desc'], description=item['description'], created_at=item['created_at'],
                    avatar_img=item['avatar_img'], statuses_count=item['statuses_count'], friends_count=item['friends_count'])
        return node
    @classmethod
    def add_main_node(cls, id):
        info = get_info(id)['data']['user']
        cls.main_node = Node('Main', id=id, name=info['screen_name'], gender=info['gender'],
                             followers_count=info['followers_count'], location=info['location'],
                             description=info['description'], avatar_img=info['avatar_hd'])
        cls.graph.create(cls.main_node)

    @classmethod
    def try_add_node(cls, item):
        if item['domain'] != -1:
            domain: Node = None
            domain = cls.nodes_matcher.match(id=item['domain']).first()
            user: Node = None
            if not cls.nodes_matcher.match(id=item['id']).exists() :
                user = cls.convert_item_to_node('User',item)
                cls.graph.create(user)
            else:
                user = cls.nodes_matcher.match(id=item['id']).first()
            user_to_domain = Relationship(user, '关注', domain)
            cls.graph.create(user_to_domain)
        else:
            target: Node = None
            if not cls.nodes_matcher.match(id=item['id']).exists():
                target = cls.convert_item_to_node('Target',item)
                cls.graph.create(target)
            main_to_target = Relationship(cls.main_node, '关注', target)
            cls.graph.create(main_to_target)
