#!/bin/bash -x
#SBATCH --mem=5000               # Memory in MB per default
#SBATCH --time=1-00:00:00
#SBATCH --ntasks=1
#SBATCH --output=Seq%j.out       # nom du fichier de sortie
#SBATCH --error=Seq%j.out        # nom du fichier d'erreur (ici en commun avec la sortie)


function transferJobData {
    echo "Copying data back"
    pwd
    echo ${OUTPUTDIR}
    mkdir "${OUTPUTDIR}/output.${SLURM_JOB_ID%%.*}"
    rsync -av --remove-source-files output/ "${OUTPUTDIR}/output.${SLURM_JOB_ID%%.*}"
    echo "Cleanup"
    rm -r ${LOCALMACRODIR}
}

function error {
    echo "ERROR: $1"
    exit 1
}

function warning {
    echo "WARNING: $1"
}

date
test -f ${HOME}/.bashrc && echo "Sourcing bashrc" && source ${HOME}/.bashrc
set -u

echo "Checking"
uname -a
echo "MACRODIR=${MACRODIR:?"unknown MACRODIR"}"
echo "MACROFILE=${MACROFILE:?"unknown MACROFILE"}"
echo "OUTPUTDIR=${OUTPUTDIR:?"unknown OUTPUTDIR"}"
echo "ENVCOMMAND=${ENVCOMMAND:?"unknown ENVCOMMAND"}"
echo "JOB_ID=$SLURM_JOB_ID"
echo "INDEX=${INDEX}"
echo "INDEXMAX=${INDEX}"
PARAMFILE=${PARAM}
PARAM=`cat ${PARAMFILE}`
echo "PARAM= ${PARAM}"

if test "$ENVCOMMAND" = "NONE"
then
  echo General environment
else
  echo Load user environment
  source "$ENVCOMMAND"
fi

echo Using $(which python)
test -d "${MACRODIR}"  || error "invalid macro"


echo "Copying inputs"
cd $TMPDIR
LOCALMACRODIR=$(mktemp -d -p .)
trap "wait ; transferJobData ; exit 1" 1 2 3 15
cd ${LOCALMACRODIR}
cp -r -L "${MACRODIR}"/* .
rm -rf output
mkdir output

# Enforce one thread
ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=1

echo "Lauching macro"
date
python ${MACROFILE} ${PARAM} || error "gate failed"
date
rm $PARAMFILE
transferJobData
date

echo "Success!!!"
