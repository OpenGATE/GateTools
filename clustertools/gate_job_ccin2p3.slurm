#!/bin/bash -x
#SBATCH --mem=12000              # Memory in MB per default
#SBATCH --ntasks=1               # Exécute 1 job
#SBATCH --time=2-00:00:00        # Max time: 2 days
#SBATCH --output=Seq%j.out       # nom du fichier de sortie
#SBATCH --error=Seq%j.out        # nom du fichier d'erreur (ici en commun avec la sortie)


function transferJobData {
    echo "Copying data back"
    pwd
    echo ${OUTPUTDIR}
    mkdir "${OUTPUTDIR}/output.${SLURM_JOB_ID%%.*}"
    rsync -av --remove-source-files output/ "${OUTPUTDIR}/output.${SLURM_JOB_ID%%.*}"
    echo "Cleanup"
    unlink "${LOCALMACRODIR}"/data
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
echo "RELEASEDIR=${RELEASEDIR:?"unknown RELEASEDIR"}"
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

if test "$RELEASEDIR" = "NONE"
then
	  echo Using $(which Gate)
	  ldd $(which Gate)
else
	  test -d "${RELEASEDIR}" || error "can't find release"
	  md5sum ${RELEASEDIR}/Gate
          ldd ${RELEASEDIR}/Gate
fi
test -d "${MACRODIR}" && test -d "${MACRODIR}/mac" || error "invalid macro"


echo "Copying inputs"
echo "coucou0"
cd $TMPDIR
echo "coucou1"
LOCALMACRODIR=$(mktemp -d -p .)
echo "coucou2"
trap "wait ; transferJobData ; exit 1" 1 2 3 15
cd ${LOCALMACRODIR}
cp -r -L "${MACRODIR}"/mac .
ln -s "${MACRODIR}"/data ./data
mkdir output

# Enforce one thread
ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=1

echo "Lauching macro"
date
if test "$RELEASEDIR" = "NONE"
then
	  Gate ${PARAM} ${MACROFILE} || error "gate failed"
else
	 ${RELEASEDIR}/Gate ${PARAM} ${MACROFILE} || error "gate failed"
fi

date
rm $PARAMFILE
transferJobData
date

echo "Success!!!"
