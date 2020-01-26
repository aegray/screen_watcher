#!/usr/bin/env python

import os
import subprocess
import json
from termcolor import colored, cprint


permanent_names = [
    'irssi',
    'ipython',
]

def classify_proc(v, pid, ppid):
    if v.startswith('screen'):
        return colored(v, 'blue')
    elif any(v.startswith(x) for x in ['vi', 'nvim']):
        return colored('E: ' + v, 'red')
    elif v.startswith('/bin/bash'):
        return classify_proc(v[len('/bin/bash '):], pid, ppid)
    elif any(v.startswith(x) for x in permanent_names):
        return v
    else:
        return colored(v, 'green')



def get_window_num(pid):
    with open(f'/proc/{pid}/environ') as fin:
        v = fin.read().split('\0')
        winnum = [x.split('=')[-1] for x in v if x.startswith('WINDOW=')]
        assert len(winnum) == 1
        return winnum[0]


def get_child_procs(pid):
    a = subprocess.check_output(f'ps -Af | grep {pid} | grep -v "grep"', shell=True).decode("ascii")
    res = []
    for x in a.split('\n'):
        p = x.split()
        if p and p[1] != pid:
            res.append((p[1], ' '.join(p[7:])))
    return res


def get_last_cmd(bashpid):
    fn = '%s/utils/cmdstat/stat.%s'%(os.environ['HOME'], bashpid)
    if os.path.exists(fn):
        parts = open(fn).read().strip().split(':')
        res = parts[-1].strip()
        cmd = ':'.join(parts[:-1])
        cmd = ' '.join(cmd.split()[1:])
        if (res != '0'):
            return colored(cmd + ' : ' + res, 'red')
        else:
            return colored(cmd, 'green')

    return None

def get_screen_tree():
    a = [x.split() for x in
            subprocess.check_output('ps -Af', shell=True).decode('ascii').split('\n')[1:]]

    a = [(x[1], x[2], ' '.join(x[7:])) for x in a if x]

    pid_ptrs = {}
    proc_tree = { '0' : ['0', 'init', {}] }
    pid_ptrs['0'] = proc_tree['0']

    # build proc tree
    screen_pids = []
    screen_raw_pids = {}
    reproc = a[:]
    next_reproc = []

    while reproc:
        for pid, ppid, path in reproc:
            if not ppid in pid_ptrs:
                next_reproc.append((pid, ppid, path))
            else:
                assert ppid in pid_ptrs, ((pid, ppid, path), pid_ptrs)
                parent_tree = pid_ptrs[ppid][2]
                assert pid not in parent_tree
                parent_tree[pid] = [ppid, path, {}]
                pid_ptrs[pid] = parent_tree[pid]

                if path.startswith('SCREEN'):
                    screen_pids.append((pid, ppid))

        reproc = next_reproc
        next_reproc = []

    any_screen_pid = set([x[0] for x in screen_pids] + [x[1] for x in screen_pids])

    def recwalk(tree, screen_stack=False):
        out = []
        sub_screens_found = []
        for k, v in tree.items():
            if v[1].startswith('SCREEN'):
                screen_name = None
                if '-S' in v[1]:
                    screen_name = v[1][v[1].index('-S')+3:]

                subres = recwalk(v[2], True)
                out.append(('screen', screen_name, k, v[0], subres))
               # v[1], v[0], subres))
            elif screen_stack:
                # is this a continuing call we should walk through?
                if k in any_screen_pid:
                    # if this is a continuing call:
                    subres = recwalk(v[2], True)
                    out.append(subres)
                elif v[1] == '/bin/bash':
                    winnr = get_window_num(k)
                    subres = recwalk(v[2], True)
                    out.append(('win', winnr, k, v[0], subres))
                else:
                    out.append(('cmd', k, v[0], v[1])) #k, v[1], v[0], []))
            else:
                subres = recwalk(v[2], screen_stack)
                if subres:
                    sub_screens_found.extend(subres)

        if not out and sub_screens_found:
            return sub_screens_found

        assert not (sub_screens_found and out)
        return out


    def recprint(v, depth=0, is_cont=False, iwidth=4):
        def iprint(*args, no_cont=False, **kw):
            if not no_cont and is_cont:
                print(*args, **kw)
            else:
                print(' '*(iwidth*depth), *args, **kw)

        if isinstance(v, tuple) and v[0] == 'screen':
            iprint('screen(', v[1], '):')
            for x in v[-1]:
                recprint(x, depth=depth+1)
        elif isinstance(v, tuple) and v[0] == 'win':
            iprint('win ', v[1], ':', v[2], v[3], ': ',  end='', no_cont=True)
            recprint(v[-1], depth=depth+1, is_cont=True)

            lcmd = get_last_cmd(v[2])
            if lcmd:
                iprint('   ==> ', lcmd)
        elif isinstance(v, tuple) and v[0] == 'cmd':
            iprint(classify_proc(v[-1], v[1], v[2]))
        elif isinstance(v, list):
            for x in v:
                recprint(x, depth, is_cont=is_cont)
            if not v:
                print()
        else:
            iprint(v)

    res = recwalk(proc_tree)
    recprint(res)


if __name__ == '__main__':
    get_screen_tree()


