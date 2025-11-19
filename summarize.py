"""

Evan Caplinger, (c)2025

Sept. 2025

Description: This code looks at the output from a slurm batch job output file and generates a .csv of runtime or other metrics for the run.

Inputs:
    filename        the name of the output file we read from
    indirect        choose the type of indirect sum we want to read. expect 'indirect_sum' or 'indirect_sum_seed'
    trial           choose the indirect sum trial we want. must be an integer that is found in the output file
    transformation  if you want to calculate a statistic other than runtime, state that here. accepts 'runtime', 'mflops_per_s', 'avg_latency', 'bandwidth', 'pct_bandwidth'
    average         set this flag if you want to also calculate the average of all problem sizes

Outputs: a .csv file with filename <original_filename>_<indirect>_<trial>_<transformation>.csv

Dependencies: argparse

"""

import re
import argparse
import os

PEAK_FLOPS = 3.92e10
PEAK_BANDWIDTH = 2.048e11

TRANSFORM_LUT = {
    'runtime':      lambda n, t: t,
    'mflops':       lambda n, t: 2 * n * n / (t * 1000000),
    'bandwidth':    lambda n, t: (8 * (n * (2 + 2 * n)) / t) / 1e9,
    'pct_bandwidth':lambda n, t: 100 * ((8 * (n * (2 + 2 * n)) / t) / PEAK_BANDWIDTH),
    'avg_latency':  lambda n, t: t / (n * (2 + 2 * n))
}

parser = argparse.ArgumentParser(prog='summarize.py')
parser.add_argument('-f', '--filename', default='')
# parser.add_argument('-c', '--categories', default='BLAS,Basic')
parser.add_argument('-d', '--directory', default='no-metrics')
# parser.add_argument('-l', '--likwid', default='')
# parser.add_argument('-x', '--suffix', default='basic')
# parser.add_argument('indirect')
# parser.add_argument('trial')
parser.add_argument('-t', '--transformation', default='runtime')
parser.add_argument('-g', '--g', default='1')
parser.add_argument('-s', '--speedup', action='store_true')
# parser.add_argument('-a', '--normalize', action='store_true')
args = parser.parse_args()

# if args.transformation not in TRANSFORM_LUT.keys() \
#         and args.transformation != 'speedup':
#     raise Exception('not a recognized transformation')

transformation = args.transformation

data = {}
categories = {
    'BLAS' : 'job-blas.out',
    'Basic': 'job-basic-omp.out',
    'Blocked; B=4': 'job-blocked-omp.out',
    'Blocked; B=16': 'job-blocked-omp.out'
}

gs = [1, 2, 3]
selected_g = int(args.g)
metrics = ['Scatter time', 'Sobel time', 'Gather time']
ps = [4, 9, 16, 25, 36, 49, 64, 81]
data = [[[0, 0] for p in ps] for g in gs]
g = None
p = None

with open(f'{args.filename}') as fh:
    for line in fh.readlines():
        m = re.search('Working on method M=(\d+), concurrency P=(\d+)', line)
        if m:
            g = int(m.group(1))
            p = int(m.group(2))

        if args.transformation == 'runtime':
            if g == selected_g:
                m = re.search('\s+(.+\s.+):\s+(\d+\.\d+)', line)
                if m:
                    metric = m.group(1)
                    value = float(m.group(2))
                    data[metrics.index(metric)][ps.index(p)] = float(f'{value:.2f}')
        elif args.transformation == 'data_movement':
            m = re.search('sending (\d+) bytes from rank (\d+)', line)
            if m:
                data[gs.index(g)][ps.index(p)][0] += int(m.group(1)) * 4 / (2 ** 20)
                data[gs.index(g)][ps.index(p)][1] += 1


if args.speedup:
    for pval in reversed(ps):
        for i in range(len(metrics)):
            print(f'working {data[i][ps.index(pval)]}')
            data[i][ps.index(pval)] = float(f'{data[i][ps.index(4)] / data[i][ps.index(pval)]:.2f}')
            print(f'worked {data[i][ps.index(pval)]}')

# print(data)
# if args.normalize:
#     data['BLAS'] = {k: 1 for k in data['BLAS'].keys()}

if args.transformation == 'runtime':
    to_write = []
    to_write.append('P,Scatter time,Sobel time,Gather time\n')
    for pidx in range(len(ps)):
        s = f'{ps[pidx]},{data[0][pidx]},{data[1][pidx]},{data[2][pidx]}\n'
        print(s)
        to_write.append(s)

elif args.transformation == 'data_movement':
    to_write = []
    to_write.append('Problem & Row & Column & Tile \\\\\n')
    to_write.append('Size (P) & (MB / Messages) & (MB / Messages) & (MB / Message)')
    for pidx in range(len(ps)):
        s = f'{ps[pidx]} & {data[0][pidx][1]} / {data[0][pidx][0]:.2f} & {data[1][pidx][1]} / {data[1][pidx][0]:.2f} & {data[2][pidx][1]} / {data[2][pidx][0]:.2f} \\\\\n'
        print(s)
        to_write.append(s)

fn_out = f'{args.directory}/g{selected_g}.csv'
with open(fn_out, 'w+') as f:
    f.writelines(to_write)
