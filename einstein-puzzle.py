#!/usr/bin/python
import pycosat
class Var(object):
    _num_vars = 0
    idx_to_var = {}

    @staticmethod
    def _add_var(var):
        Var._num_vars += 1
        idx = Var._num_vars
        Var.idx_to_var[idx] = var
        return idx

    def __init__(self, label):
        self.idx = self._add_var(self)
        self.label = label

    def __repr__(self):
        return "{}(idx={!r}, name={!r}".format(type(self).__name__,
                                               self.idx,
                                               self.label)

    def __str__(self):
        return self.label
    
W=5
class DimVar(Var):
    def __init__(self, dim, val, cid):
        super(DimVar, self).__init__("[%s,%s,%d]"%(dim, val, cid))
        self.dim = dim
        self.val = val
        self.cid = cid

def rule_one_dimval_one_position(dim_val_ids):
    clauses = []
    dim_ids = dim_val_ids
    clauses.append(dim_ids) # dimension on at least one position
    for aid in dim_ids:
        for bid in dim_ids:
            if aid != bid:
                clauses.append( [-aid,-bid])
    #dimension should not on two places
    return clauses;

house_map = {}
cig_map = {}
nation_map = {}
drink_map = {}
pet_map = {}


house_vals = ["Red","Green","White","Blue","Yellow"]
cig_vals = ["PallMall","DunHill","Blends","BlueMaster","Prince"]
nation_vals =["British","Swede","Dane","German","Norwish"]
drink_vals = ["Tea","Coffee","Milk","Juice","Water"]
pet_vals = ["Dogs","Birds","Cats","Horses","Fishes"]

def make_dimension(name, vals, dmap):
    clauses = []
    grid =  [[0 for i in range(W)] for j in range(W)]
    row = 0
    #for val in ["Red","Green","White","Blue","Yellow"]:
    for val in vals:
        for i in range(W):
            dim_val_var = DimVar(name,val,i)
            dmap[(val,i)] = dim_val_var
            grid[row][i] = dim_val_var.idx
        clauses.extend(rule_one_dimval_one_position(grid[row]))
        row += 1
    for col in range(W):
        column = [grid[i][col] for i in range(W)]
        clauses.extend(rule_one_dimval_one_position(column))
    return clauses;
def middle_p(v1, v2, p):
    clauses = []
    clauses.append([-v1,-v2,p])
    clauses.append([-p,v1])
    clauses.append([-p,v2])        
    return clauses

def rule_imply(dim1,val1,dim2,val2):
    clauses = []
    relations = []
    prelations = []
    for i in range(W):
        v1 = dim1[(val1,i)].idx
        v2 = dim2[(val2,i)].idx
        p = Var("Imp[%d^%d]"%(v1,v2)).idx
        clauses.extend(middle_p(v1,v2,p))
        prelations.append(p)
    clauses.append(prelations)
    return clauses

def rule_center_house_drink_milk():
    clauses = []
    prelations = []
    for val in house_vals:
        i = 2
        hid = house_map[(val,i)].idx
        mid = drink_map[("Milk",i)].idx
        p = Var("center").idx
        clauses.extend(middle_p(hid,mid,p))
        prelations.append(p)
    clauses.append(prelations)
    return clauses

def rule_lives_to_left(dim1,val1,dim2,val2):
    clauses = []
    prelations = []
    for i in range(W-1):
        v1 = dim1[(val1,i)].idx
        v2 = dim2[(val2,i+1)].idx
        p = Var("LImp[%d^%d]"%(v1,v2)).idx
        clauses.extend(middle_p(v1,v2,p))
        prelations.append(p)
    clauses.append(prelations)
    return clauses


def rule_neighbor(dim1,val1,dim2,val2):
    clauses = []
    prelations = []
    for i in range(W):
        j1 = i-1
        j2 = i+1
        if j1 >= 0 : #to the left
            v1 = dim1[(val1,i)].idx
            v2 = dim2[(val2,j1)].idx
            p = Var("NLImp[%d^%d]"%(v1,v2)).idx
            clauses.extend(middle_p(v1,v2,p))
            prelations.append(p)
        if j2 < W: # to the right
            v1 = dim1[(val1,i)].idx
            v2 = dim2[(val2,j2)].idx
            p = Var("NRImp[%d^%d]"%(v1,v2)).idx
            clauses.extend(middle_p(v1,v2,p))
            prelations.append(p)
    clauses.append(prelations)
    
    return clauses

all_clauses = (
    make_dimension("house", house_vals, house_map) +
    make_dimension("nation", nation_vals, nation_map) +
    make_dimension("drink", drink_vals, drink_map) +
    make_dimension("cig", cig_vals, cig_map) +
    make_dimension("pet", pet_vals, pet_map) +
    rule_imply(nation_map,"British",house_map,"Red")+
    rule_imply(nation_map,"Swede",pet_map,"Dogs")+
    rule_imply(nation_map,"Dane",drink_map,"Tea")+
    rule_lives_to_left(house_map,"Green",house_map,"White")+
    rule_imply(house_map,"Green",drink_map,"Coffee")+
    rule_imply(cig_map,"PallMall",pet_map,"Birds")+
    rule_imply(house_map,"Yellow",cig_map,"DunHill")+
    rule_center_house_drink_milk()+
    [[nation_map[("Norwish",0)].idx]]+ #Norwish lives in the fist
    rule_neighbor(cig_map,"Blends",pet_map,"Cats")+
    rule_neighbor(pet_map,"Horses",cig_map,"DunHill")+
    rule_imply(cig_map,"BlueMaster",drink_map,"Juice")+
    rule_imply(nation_map,"German",cig_map,"Prince")+
    rule_neighbor(nation_map,"Norwish",house_map,"Blue")+
    rule_neighbor(cig_map,"Blends",drink_map,"Water")
)

def pretty_print_solution(sol):
    positive_indices = {t for t in sol if t > 0}
    def print_dimension(dim_map):
        dim_vals = []
        #cid: the coordinate id
        for (val,cid), item in dim_map.items():
            # pick up the dim value which resolves to T
            if item.idx in positive_indices: dim_vals.append(item)
        sdims = sorted(dim_vals,key=lambda x:x.cid)
        print map(lambda x:(x.cid,x.val), sdims)

    print ""
    print_dimension(house_map)
    print_dimension(nation_map)
    print_dimension(drink_map)
    print_dimension(cig_map)
    print_dimension(pet_map)
    print ""

#print all_clauses
#sol = pycosat.solve(all_clauses)
#pretty_print_solution(sol)

for sol_idx, sol in enumerate(pycosat.itersolve(all_clauses)):
    pretty_print_solution(sol)

