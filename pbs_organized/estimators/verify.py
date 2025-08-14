#!/usr/bin/env python3

if __name__ == '__main__':
    org = '../reconciliation/test-sets/sets_100000_1000_32_1574465740.txt'
    org_w_path = '/home/saber/Dropbox/large-files/sets_1000000_1000_32_1574465740.txt'
    stop = False
    with open(org, 'r') as f1, open(org, 'r') as f2:
        lno = 0
        for e1 in f1:
            for e2 in f2:
                if lno < 3:
                    lno += 1
                else:
                    if e1 != e2:
                        print(f'{e1} != {e2}')
                        stop = True
                break 
            if stop:
                print("Not consistent!")
        print('Consistent!')
            
                