from py2neo import Graph, Node, Relationship


g = Graph("bolt://47.112.122.242:7687",
          user="neo4j",
          password="Password01")


d_nodes = {}


def to_graph(a, r, b):
    global d_nodes
    if r != "PROPERTY":
        left_name, left_label = tuple(a.split(":"))
        right_name, right_label = tuple(b.split(":"))
        a = Node(left_label, name=left_name)
        b = Node(right_label, name=right_name)
        left_hash = hash((left_label, "name", left_name))
        right_hash = hash((right_label, "name", right_name))
        a = d_nodes.setdefault(left_hash, a)
        b = d_nodes.setdefault(right_hash, b)
        return Relationship(a, r, b)
    elif r == "PROPERTY":
        left_name, left_label = tuple(a.split(":"))
        value, _property = tuple(b.split(":"))
        properties = {
            "name": left_name,
            _property: value
        }
        left_hash = hash((left_label, "name", left_name))
        a = Node(left_label, **properties)
        a = d_nodes.setdefault(left_hash, a)
        return a


elements = []
with open("./knowledge.rdf", "r") as file:
    for line in file.readlines():
        line = line.rstrip("\n")
        print(line)
        a, r, b = tuple(line.split(','))
        r = r.upper()
        elements.append(to_graph(a, r, b))

for el in elements:
    print(el)


sub_graph = elements[0]
for element in elements[1:]:
    sub_graph = sub_graph | element


g.delete_all()
tx = g.begin()
tx.create(sub_graph)
tx.commit()



