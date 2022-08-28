#!/bin/bash 
#SBATCH -J test   
##SBATCH -n 24
#SBATCH -n 1
#SBATCH -c 24
#SBATCH -t 00:30:00   
#SBATCH -A p0020160
#SBATCH --export=ALL
###SBATCH -C avx512
#SBATCH --mem-per-cpu=3800

pg_ctl -D /home/bz43nogu/mylocal_db stop
rabbitmqctl stop

pg_ctl -D /home/bz43nogu/mylocal_db stop
rabbitmqctl stop
