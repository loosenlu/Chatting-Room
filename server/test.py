

class A(object):

    def __init__(self):
        self.name = "lu"

    def print_haha(self):

        print "Hello" + " A" + "!"
        self.name = 'li'
    
    def shishi(self):
        return self.print_haha, self


a = A()
print a.name

print '*' * 16
b, c = a.shishi()
type(b)
type(c)
print b
print c
print '*' * 16

b()
print a.name