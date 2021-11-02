def read_proc_maps(fname):
    with open(fname, 'r') as f:
        lines = f.read().splitlines()
    rv = []
    for line in lines:
        r1, r2 = line.split(' ')[0].split('-')
        rv.append((int(r1,0x10), int(r2,0x10)))
    return rv

def can_merge(r1, r2):
    return r1[1] == r2[0]

def merge(r1, r2):
    return (r1[0], r2[1])

def print_merged(mappings):
    print (f"RANGE\t\t\t\t\tSIZE")
    
    i = 0
    while i < len(mappings) - 1:
        r1, r2 = mappings[i:i+2]
        if can_merge(r1, r2):
            mappings = mappings[:i] + [merge(r1, r2)] + mappings[i+2:]
        else:
            i += 1

    old_r = None
    for r in mappings:
        if old_r is not None:
            if r[0] - old_r[1] < 0x10000000:    
                print (f"SMALL GAP\t\t\t\t{r[0] - old_r[1]:#010x}")
            else:
                print (f"HUGE GAP")
        print(f"{r[0]:#018x} - {r[1]:#018x}\t{r[1] - r[0]:#010x}")
        
        old_r = r

mappings = read_proc_maps('./mappings')
print_merged(mappings)