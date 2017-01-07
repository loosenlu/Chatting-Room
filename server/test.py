
class A(object):

    def __init__(self):

        self.name = "hehe"

a = A()
b = A()

m = {1:a, 2:b}
hehe = m[1]
hehe.name = "haha"
print m[1].name
m[1].name = "luli"
print '*' * 32
print hehe.name