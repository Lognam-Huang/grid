'''
---                            __     
---                    __     /\ \    
---     __      _ __  /\_\    \_\ \   
---   /'_ `\   /\`'__\\/\ \   /'_` \  
---  /\ \L\ \  \ \ \/  \ \ \ /\ \L\ \ 
---  \ \____ \  \ \_\   \ \_\\ \___,_\
---   \/___L\ \  \/_/    \/_/ \/__,_ /
---     /\____/                       
---     \_/__/                        
'''

import math
import re
import sys
import csv



the = {}
help = """
gird.lua : a rep grid processor
(c)2022, Tim Menzies <timm@ieee.org>, BSD-2 

USAGE: grid.lua  [OPTIONS] [-g ACTION]

OPTIONS:
  -d  --dump    on crash, dump stack   = false
  -f  --file    name of file           = ../etc/data/repgrid1.csv
  -g  --go      start-up action        = data
  -h  --help    show help              = false
  -p  --p       distance coefficient   = 2
  -s  --seed    random number seed     = 937162211

ACTIONS:
"""


#Summarize a stream of symbols.
class SYM:
    
    #no need to care about obj()
    
    ## line 35 function SYM.new(i)
    def __init__(self, at=0, txt=""):
        self.at = at
        self.txt = txt
        self.n = 0 # basic
        self.has = {} # similar as before?
        # dict for keeping data
        
        self.most = 0 #the frequency of the most frequent object
        self.mode = None #there is no mode initially

    # line 40 function SYM.add(i,x)
    def add(self, x):
        if x != "?":
            self.n +=  1
            
            #if x already exists in current record, just add frequency of its occurance
            #otherwise, create a new key and its new value-1            
            if x in self.has.keys():
                self.has[x] += 1
            else:
                self.has[x] = 1
            
            
            #after each insertion, check whether the frequency of new record becomes the most frequent one
            #by comparing with 'most'
            if self.has[x] > self.most:
                self.most = self.has[x]
                self.mode = x

    # line 47 function SYM.mid(i,x)
    def mid(self, *x):
        #here 'mid' stands for mode
        return self.mode

    # line 48 functon SYM.div(i,x,  fun, e)
    # fun() here should be an anonymous funciton
    #return the entropy
    def div(self, *x):
        e = 0
        for key in self.has:
            p = self.has[key] / self.n
            p = p*(math.log2(p))
            e += p
        
        return -e
    
    def rnd(self, x, *n):
        return x

    def dist(self, s1, s2):
        if s1 == '?' and s2 == '?':
            return 1
        elif s1 == s2:
            return 0
        else: return 1
    
#line 53
#Summarizes a stream of numbers.
class NUM:
    ## line 55 function NUM.new(i)
    def __init__(self, at=0, txt=""):
        self.at = at
        self.txt = txt
        self.n = 0 # basic
        
        self.mu = 0 # mean value of all
        self.m2 = 0 # standard deviation
        
        self.lo = math.inf # lowest value, initially set as MAX
        self.hi = -math.inf # highest value, initially set as MIN
        if txt=="":
            self.w = -1
        elif txt[-1]=="-":
            self.w = -1
        else: 
            self.w = 1
    # line 59 function NUM.add(i,x)
    # add `n`, update lo,hi and stuff needed for standard deviation
    def add(self, n):
        if n != "?":
            self.n +=  1
            
            d = n - self.mu
            
            self.mu += d/(self.n)
            self.m2 += d*(n - self.mu)
            
            self.lo = min(self.lo, n)
            self.hi = max(self.hi, n)

    # line 68 function NUM.mid(i,x)
    def mid(self, *x):
        #here 'mid' stands for mean
        return self.mu

    # line 69 functon NUM.div(i,x)
    # return standard deviation using Welford's algorithm
    def div(self, *x):
        if(self.m2 < 0 or self.n <2):
            return 0
        else:
            return pow((self.m2 / (self.n-1)), 0.5)
        
    def rnd(self, x, n): return x if x=="?" else rnd(x, n)

    def norm(self, n):
        if n == '?':
            return n
        else:
            return (n - self.lo) / (self.hi - self.lo)
    
    def dist(self, n1, n2):
        if n1 == '?' and n2 == '?': return 1
        n1 = self.norm(n1)
        n2 = self.norm(n2)
        if n1 == '?':
            n1 = (n2 < .5 and 1 or 0)
        if n2 == '?':
            n2 = (n1 < .5 and 1 or 0)
        return abs(n1 - n2)



class COLS:
    def __init__(self, names):
        self.names = names #dic
        self.all = {}
        self.klass = None
        self.x = {}
        self.y = {}
        
        for index, name in names.items():
            # all columns should be recorded in self.all, including those skipped columns
            # if the column starts with a capital character, it is Num
            # otherwise, it is Sym
            if name[0].istitle():
                curCol = push(self.all, NUM(index, name))
            else:
                curCol = push(self.all, SYM(index, name))    
            
            # lenOfName = len(name)
            
            # if a column ends with a ':', the column should be skipped and recorded nowhere except self.all
            
            # if there is any '+' or '-', the column should be regarded as a dependent variable
            # all dependent variables should be recoreded in self.y
            # on the contrary, those independent variables should be recorded in self.x
            if name[-1] != "X":
                if name [-1] == '!':
                    self.klass = curCol
                if "+" in name or "-" in name:
                    push(self.y, curCol)
                else:
                    push(self.x, curCol)
                
                # if a column name ends with a '!', this column should be recorded AS self.klass
                # NOTICE THAT IT IS "AS", NOT "INCLUDED IN"

    def add(self, row):
        for _,t in self.y.items():
            t.add(row.cells[t.at])

                
        for _,t in self.x.items():
            t.add(row.cells[t.at])


class ROW:
    def __init__(self, t):
        self.cells = t
        self.x = None
        self.y = None

class DATA:
    def __init__(self , src):
        self.rows = {}
        self.cols = None
        def fun(x):
            self.add(x)
        if type(src) == str:
            Csv(src , fun)
        else:
            if src:
                #map(src , fun)
                self.add(src)
            else:
                map({} , fun)
    
    def add(self , t):
        if self.cols:
            t = t if type(t) == ROW else ROW(t)
            push(self.rows , t)
            self.cols.add(t) #COLS.add()
        else:
            self.cols = COLS(t)
    
    def clone(self , init):
        data = DATA(self.cols.names)
        def fun(x):
            data.add(x)
        map(init or {} , fun)
        return data
            
    def stats(self , what , cols , nPlaces):
        def fun(k , col):
            if what == 'div':
                return col.rnd(col.div(col) , nPlaces)
            else:
                return col.rnd(col.mid(col) , nPlaces)
        u = {}
        for i in range(len(cols)):
            k = cols[i].txt
            u[k] = fun(k , cols[i])
        res = {}
        for k in sorted(u.keys()):
            res[k] = u[k]
        return res
    
    def better(self , row1 , row2):
        s1 = 0
        s2 = 0
        ys = self.cols.y
        for _ , col in ys.items():
            x = col.norm(row1.cells[col.at])
            y = col.norm(row2.cells[col.at])
            s1 -= math.exp(col.w * (x - y) / len(ys))
            s2 -= math.exp(col.w * (y - x) / len(ys))
        return (s1 / len(ys)) < (s2 / len(ys))

    
    def dist(self , row1 , row2 , *cols):
        n , d = 0 , 0
        if cols is None: cols = self.cols.x
        for _ , col in self.cols.x.items():
            n += 1
            d += col.dist(row1.cells[col.at] , row2.cells[col.at]) ** the['p']
        return (d / n) ** (1 / the['p']) 

    def around(self , row1 , *rows , **cols): #--> list[dict{row: , dist: }]
        def fun(row2):
            dic = {}
            dic['row'] = row2
            dic['dist'] = self.dist(row1 , row2 , cols)
            return dic
        rows = rows or self.rows
        rows = rows[0]
        tmp = map(rows or self.rows , fun) #dic{dic{}}
        tmp = list(tmp.values()) # [dict]
        return sort(tmp , lt('dist')) 
    
    def half(self , **kwargs):
        def dist(row1 , row2):
            return self.dist(row1 , row2 , kwargs['cols'] if 'cols' in kwargs else None)

        def project(row):
            dic = {}
            x , y = cosine(dist(row , A) , dist(row , B) , c)
            row.x = row.x or x
            row.y = row.y or y
            dic['row'] = row
            dic['x'] = x
            dic['y'] = y
            return dic
        
        rows = kwargs['rows'] if 'rows' in kwargs else self.rows
        A = kwargs['above'] if ('above' in kwargs and kwargs['above']) else any(rows)
        B = self.furthest(A , rows)['row']
        c = dist(A , B)
        left , right = {} , {}
        for n , tmp in enumerate(sort(list(map(rows , project).values()) , lt('x'))):
            if n+1 <= (len(rows)+1) // 2:
                push(left , tmp['row'])
                mid = tmp['row']
            else:
                push(right , tmp['row'])
        return left , right , A , B , mid , c
        
    
    def cluster(self , **kwargs):
        rows = kwargs['rows'] if 'rows' in kwargs else self.rows
        #min = kwargs['min'] if 'min' in kwargs else len(rows) ** the['min']
        cols = kwargs['cols'] if 'cols' in kwargs else self.cols.x
        node = {}
        node['data'] = self.clone(rows)
        if len(rows) >= 2: #* min
            left , right , node['A'] , node['B'] , node['mid'], node['c'] = self.half(rows=rows , cols=cols , above=kwargs['above'] if 'above' in kwargs else None)
            node['left'] = self.cluster(rows=left , cols=cols , above=node['A'])
            node['right'] = self.cluster(rows=right , cols=cols , above=node['B'])
        return node
    
    def sway(self , **kwargs):
        rows = kwargs['rows'] if 'rows' in kwargs else self.rows
        min = kwargs['min'] if 'min' in kwargs else len(rows) ** the['min']
        cols = kwargs['cols'] if 'cols' in kwargs else self.cols.x
        node = {}
        node['data'] = self.clone(rows)
        if len(rows) > 2 * min:
            left , right , node['A'] , node['B'] , node['mid'], _ = self.half(rows=rows , cols=cols , above=kwargs['above'] if 'above' in kwargs else None)
            if self.better(node['B'] , node['A']):
                left , right , node['A'] , node['B'] = right , left , node['B'] , node['A']
            node['left'] = self.sway(rows=left , min=min , cols=cols , above=node['A'])
        return node

    def furthest(self, row1, rows, *cols):
        t = self.around(row1 , rows , cols)
        return t[-1]


       
## Misc

def transpose(t):
    u = [[0]*len(t) for _ in range(len(t[0]))]
    for i in range(len(t[0])):
        for j in range(len(t)):
            u[i][j] = t[j][i]
    return u

def repCols(cols:list):
    newcols = copy(cols)
    for col in newcols:
        col[-1] = col[0] + ':' + col[-1]
        col.pop(0)
    header = []
    for i in range(len(newcols[0])):
        id = i + 1
        header.append('Num' + str(id))
    header[-1] = "thingX"
    newcols.insert(0 , header)
    with open('../etc/data/cols.csv' , 'w' , encoding='UTF8' , newline='') as f:
        writer = csv.writer(f)
        writer.writerows(newcols)
    return DATA('../etc/data/cols.csv')


def repRows(t, rows): #rows = cols.transpose
    rows = copy(rows)
    for j , s in enumerate(rows[-1]):
        rows[0][j] = rows[0][j] + ':' + s
    rows.pop()
    for n , row in enumerate(rows):
        if n == 0:
            row.append('thingX')
        else:
            u = t['rows'][len(t['rows']) - n]
            row.append(u[-1])
    with open('../etc/data/rows.csv' , 'w' , encoding='UTF8' , newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return DATA('../etc/data/rows.csv') 


def repPlace(data):
    n = 20
    g = {}
    for i in range(1 , n+2):
        g[i] = {}
        for j in range(1 , n+2):
            g[i][j] = ' '
    maxy = 0
    print('')
    for r , row in enumerate(data.rows.values()):
        c = chr(64 + r + 1)
        print(c , last(row.cells))
        x,y= int(row.x*n//1), int(row.y*n//1)
        maxy = max(maxy,y+1)
        g[y+1][x+1] = c
    print('')
    #print(maxy) --> 12
    for y in range(1,maxy+1):
        oo(g[y])


def repgrid(sFile):
    t = dofile(sFile)
    rows = repRows(t, transpose(t['cols'])) 
    cols = repCols(t['cols'])
    show(rows.cluster())
    show(cols.cluster())
    repPlace(rows) 

def show(node, lvl:int=None):
    if node:
        lvl = lvl if lvl else 0
        res = '|.. ' * lvl
        if 'left' not in node:
            print(res + o(last(last(node['data'].rows).cells)))
        else:
            print(res + fmt("%.f",rnd(100*node['c'])))
        #if 'left' in node:
            show(node['left'], lvl+1)
        #if 'right' in node:
            show(node['right'], lvl+1)

def dofile(file): #use regex to transfer repgrid1.csv to a dict{[list]}
    fo = open(file , 'r')
    res = []
    cols = []
    rows = []
    for line in fo:
        line = line.strip()
        if line[0][0] == 'c' or line[0][0] == 'r':
            line = line[5:]
        line = line.strip(',')
        line = line.replace(' ' , '')
        line = line.replace("'" , '')
        line = line.replace('{' , '')
        line = line.replace('}' , '')
        res.append(line.split(','))
    fo.close()

    cols = res[3:11]
    rows = res[11:-1]
    t = {}
    t['rows'] = rows
    t['cols'] = cols
    return t



## Numerics 

Seed = 937162211

# n ; a integer lo..hi-1
def rint(lo, hi):
    return math.floor(0.5 + rand(lo, hi))

# n; a float "x" lo<=x < x
def rand(lo, hi):
    global Seed
    lo = lo or 0
    hi = hi or 1
    Seed = (16807 * Seed) % 2147483647
    return lo + (hi-lo) * Seed / 2147483647

# num. return `n` rounded to `nPlaces`
def rnd(n, nPlaces=3):
    mult = 10**nPlaces
    return math.floor(n * mult + 0.5) / mult

# n,n;  find x,y from a line connecting `a` to `b`
def cosine(a, b, c):
    x1 = (a**2 + c**2 - b**2) / (2*c)
    x2 = max(0, min(1, x1))
    y = math.sqrt(abs(a**2 - x2**2))
    return x2, y

## Lists

# Note the following conventions for `map`.
# - If a nil first argument is returned, that means :skip this result"
# - If a nil second argument is returned, that means place the result as position size+1 in output.
# - Else, the second argument is the key where we store function output.

# t; map a function `fun`(v) over list (skip nil results)
def map(t:dict, fun):
    u = {}
    for k, v in t.items():
        u[k]=fun(v)
    return u

# t; map function `fun`(k,v) over list (skip nil results)
def kap(t:dict, fun):
    u = {}
    for k, v in t.items():
        u[k]=fun(k, v)
    return u

# t; return `t`,  sorted by `fun` (default= `<`)
def sort(t:list, fun = lambda x: x.keys()):
    return sorted(t, key=fun)

def lt(x: str):
    def fun(dic):
        return dic[x]
    return fun

# ss; return list of table keys, sorted
def keys(t:list):
    return sorted(kap(t, lambda k, _:k))

# any; push `x` to end of list; return `x` 
def push(t:dict, x):
    t[len(t)] = x
    return x

# x; returns one items at random
def any(t):
    return list(t.values())[rint(0,len(t)-1)]

# t1; returns some items from `t`
def many(t, n):
    u = {}
    for i in range(0, n):
        u[i] = any(t)
    return u

def last(t):
    return list(t.values())[-1]

def copy(t):
    import copy
    return copy.deepcopy(t) # not sure if it works



## Strings



def fmt(sControl , *elements): # emulate printf
    return (sControl%(elements)) 
#test
##a=1
##b=2
##print(fmt("%s and %s" , a , b)) #--> "1 and 2"


def o(t , *isKeys): #--> s; convert `t` to a string. sort named keys.
    if type(t) != dict:
        return str(t)
    
    def fun(k , v):
        if not re.findall('[^_]' , str(k)):
            return fmt(":%s %s",o(k),o(v))
    
    if len(t) > 0 and not isKeys:
        tmp = map(t , o)
    else:
        tmp = sort(kap(t , fun))

    def concat(tmp:dict):
        res = []
        for k , v in tmp.items():
            #res.append(':' + str(k))
            res.append(v)
        return res
    return '{' + ' '.join(concat(tmp)) + '}'

def oo(t):
    print(o(t))
    return t

def coerce(s):
    def fun(s1):
        if s1 == 'true':
            return True
        if s1 == 'false':
            return False 
        return s1.strip()
    if s.isdigit():
        return int(s)
    try:
        tmp = float(s)
        return tmp
    except ValueError:
        return fun(s)
    

def Csv(fname, fun):
    n=0
    with open(fname,'r') as src:
        rdr = csv.reader(src, delimiter=',')
        for l in rdr:
            d={}
            for v in l:
                d[len(d)]=coerce(v)
            n+=len(d)
            fun(d)
    return n

### Main


def settings(s):  # --> t;  parse help string to extract a table of options
    t = {}
    # match the contents like: '-d  --dump  on crash, dump stack = false'
    res = r"[-][\S]+[\s]+[-][-]([\S]+)[^\n]+= ([\S]+)"
    m = re.findall(res, s)
    for key, value in m:
        t[key] = coerce(value)
    return t
# test
# print(settings(help)) --> {'dump': False, 'go': 'data', 'help': False, 'seed': 937162211}

# Update settings from values on command-line flags. Booleans need no values


def cli(t, list):
    slots = list[1:]
    # search the key and value we want to update
    for slot, v in t.items():
        # give each imput slot an index(begin from 0)
        for n, x in enumerate(slots):
            # match imput slot with the.keys: x == '-e' or '--eg'
            if x == ('-'+slot[0]) or x == ('--'+slot):
                v = str(v)
                # we just flip the defeaults
                if v == 'True':
                    v = 'false'
                elif v == 'False':
                    v = 'true'
                else:
                    v = slots[n+1]
                t[slot] = coerce(v)
    return t

def parse(t , id):
    #map(t.cols.all,oo)
    id = id
    colres = ['{a:']
    for col in t.cols.all.values():
        colres = ['{a:']
        if col.__class__.__name__ == 'NUM':  
            colres = colres + [col.__class__.__name__ , ':at ' + str(col.at+1) , ':hi ' + str(col.hi) , ':id ' + str(id) , ':lo ' + str(col.lo) , ':m2 ' + str(round(col.m2 , 3)) , ':mu ' + str(round(col.mu , 3)) , ':n ' + str(col.n) , ':txt ' + str(col.txt) , ':w ' + str(col.w)]
            colres = ' '.join(colres)
            print(colres)
        else:
            colres = colres + [col.__class__.__name__ , ':at ' + str(col.at+1) , ':has ' + '{}' , ':id ' + str(id) , ':most ' + str(col.most) , ':n ' + str(col.n) , ':txt ' + col.txt]
            colres = ' '.join(colres)
            print(colres)
        id += 1
    
    #map(t.rows,oo)
    rowres = ['{a:']
    for row in t.rows.values():
        rowres = ['{a:']
        tmp = list(row.cells.values())
        for i in range(len(tmp)):
            tmp[i] = str(tmp[i])
        rowres += [row.__class__.__name__ , ':cells {'  + ' '.join(tmp) + '} ' + ':id ' + str(id)]
        print(' '.join(rowres))
        id += 1

def main(options, help, funs, *k):
    saved = {}
    fails = 0
    for k, v in cli(settings(help), sys.argv).items():
        options[k] = v
        saved[k] = v
    if options['help']:
        print(help)
    

    else:
        for what, fun in funs.items():
            if options['go'] == 'all' or what == options['go']:
                for k, v in saved.items():
                    options[k] = v
                if fun() == False:
                    fails += 1
                    print("❌ fail:", what)
                else:
                    print("✅ pass:", what)


## Examples

egs = {}
def eg(key, str, fun):  #--> nil; register an example.
    global help
    egs[key] = fun
    #help = help + f'  -g  {key}\t{str}\n'
    help = help + fmt('  -g  %s\t%s\n', key, str)




if __name__=='__main__':

    # eg("crash","show crashing behavior", function()
    #   return the.some.missing.nested.field end)
    def thefun():
        global the
        oo(the)
    eg("the","show settings", thefun)

    def copyfun():
        t1={'a':1,'b':{'c':2,'d':{0:3}}}
        t2 = copy(t1)
        t2['b']['d'][0]=10000
        print("b4",str(t1),"\nafter",str(t2))
    eg("copy","check copy", copyfun)


    def symfun():
        sym = SYM()
        for x in ["a","a","a","a","b","b","c"]:
            sym.add(x)
        return "a" == sym.mid() and 1.379 == rnd(sym.div())
    eg("sym","check syms", symfun)

    def numfun():
        num = NUM()
        for x in [1,1,1,1,2,2,3]:
            num.add(x)
        return 11/7 == num.mid() and 0.787 == rnd(num.div())
    eg("num", "check nums", numfun)
    
    def repColsfun():
        t = repCols(dofile(the['file'])['cols'])
        parse(t , 910)
    eg("repcols","checking repcols", repColsfun)

    def synonymsfun():
        show(repCols( dofile(the['file'])['cols'] ).cluster())
    eg("synonyms","checking repcols cluster", synonymsfun)

    def reprowsfun():
        t = dofile(the['file'])
        rows = repRows(t, transpose(t['cols']))
        parse(rows , 931)
    eg("reprows","checking reprows", reprowsfun)

    def prototypesfun():
        t = dofile(the['file'])
        rows = repRows(t, transpose(t['cols']))
        show(rows.cluster())
    eg("prototypes","checking reprows cluster", prototypesfun)

    def positionfun():
        t = dofile(the['file'])
        rows = repRows(t, transpose(t['cols']))
        rows.cluster()
        repPlace(rows)
    eg("position","where's wally", positionfun)

    def everyfun():
        global the
        repgrid(the['file'])
    eg("every","the whole enchilada", everyfun)


    main(the, help, egs)