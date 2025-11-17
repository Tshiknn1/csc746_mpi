#!/bin/bash
#SBATCH -N 1
#SBATCH -C cpu
#SBATCH -q debug
#SBATCH -J csc746_f25_evan_caplinger_sum
#SBATCH --mail-user=ecaplinger@sfsu.edu
#SBATCH --mail-type=ALL
#SBATCH -t 00:05:00

for P in 1 2 4 8 16; do
    export OMP_NUM_THREADS=$P

    echo "Working on concurrency P=$P"

    srun -n 1 -c 64 build/sobel_cpu

done
