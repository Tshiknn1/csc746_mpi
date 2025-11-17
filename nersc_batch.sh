#!/bin/bash
#SBATCH -N 4
#SBATCH -C cpu
#SBATCH -q debug
#SBATCH -J csc746_f25_evan_caplinger_sum
#SBATCH --mail-user=ecaplinger@sfsu.edu
#SBATCH --mail-type=ALL
#SBATCH -t 00:15:00

cd build

for M in 1 2 3; do

    for P in 4 9 16 25 36 49 64 81; do
        echo "Working on method M=$M, concurrency P=$P"

        srun -n $P ./mpi_2dmesh -g $M -i ../data/zebra-gray-int8-4x -x 7112 -y 5146 -o ../data/output-g$M-p$P.dat -a 1

    done

done
