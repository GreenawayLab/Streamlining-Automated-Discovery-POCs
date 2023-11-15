#!/bin/zsh
#SBATCH --job-name=Cage_Opt    # Job name
#SBATCH --mail-type=END,FAIL          # Mail events (NONE, BEGIN, END, FAIL, ALL)
#SBATCH --mail-user=    # Where to send mail
#SBATCH --ntasks=36
#SBATCH --mem=20gb               # Run on a single CPU
#SBATCH --time=720:00:00               # Time limit hrs:min:sec
#SBATCH --output=Cage_Opt_%j.log   # Standard output and error log
#SBATCH --nodes=1                    # Run all processes on a single node

# Get random folder name
RANDOM_DIR=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1)

export OMP_NUM_THREADS=1

pwd; hostname; date

mkdir $RANDOM_DIR

cd $RANDOM_DIR

#source activate annabel_environment

echo "Running cage optimisation"

python ../cage_opt_100ns.py -db "enter_mongodb" -p 36

date