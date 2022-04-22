#!/bin/bash

#
#
#

# Test if this is script is running has root
if [ "$EUID" -ne 0 ]; then
	echo "Please run as root"
	exit 1
fi

#### Dir
home="$HOME"
damdCon="$pwd/../../lib/sh"
dOut="$pwd/out/pf-2k6"
dScript="$pwd/../../lib/py"
dspec="" # Benchmarks binary folder 

#### Disable Turbo-Boost / Enable PF
$damdCon/disable_turbo.sh
$damdCon/enable_pf.sh

#### Prepare output folder
mkdir -p $dOut > /dev/null 2>&1

#### Benchmarks
declare -A bench
bench=(
["400.perlbench.1"]="perlbench -Ilib checkspam.pl 2500 5 25 11 150 1 1 1 1"
["400.perlbench.2"]="perlbench -Ilib diffmail.pl 4 800 10 17 19 300"
["400.perlbench.3"]="perlbench -Ilib splitmail.pl 1600 12 26 16 4500"
["401.bzip2.1"]="bzip2 input.source 280"
["401.bzip2.2"]="bzip2 chicken.jpg 30"
["401.bzip2.3"]="bzip2 liberty.jpg 30"
["401.bzip2.4"]="bzip2 input.program 280"
["401.bzip2.5"]="bzip2 text.html 280"
["401.bzip2.6"]="bzip2 input.combined 200"
["403.gcc.1"]="gcc 166.in -o 166.s"
["403.gcc.2"]="gcc 200.in -o 200.s"
["403.gcc.3"]="gcc c-typeck.in -o c-typeck.s"
["403.gcc.4"]="gcc cp-decl.in -o cp-decl.s"
["403.gcc.5"]="gcc expr.in -o expr.s"
["403.gcc.6"]="gcc expr2.in -o expr2.s"
["403.gcc.7"]="gcc g23.in -o g23.s"
["403.gcc.8"]="gcc s04.in -o s04.s"
["403.gcc.9"]="gcc scilab.in -o scilab.s"
["410.bwaves.1"]="bwaves"
["416.gamess.1"]="gamess"
["416.gamess.2"]="gamess"
["416.gamess.3"]="gamess"
["429.mcf.1"]="mcf inp.in"
["433.milc.1"]="milc"
["434.zeusmp.1"]="zeusmp"
["435.gromacs.1"]="gromacs -silent -deffnm gromacs -nice 0"
["436.cactusADM.1"]="cactusADM benchADM.par"
["437.leslie3d.1"]="leslie3d"
["444.namd.1"]="namd --input namd.input --iterations 38 --output namd.out"
["445.gobmk.1"]="gobmk --quiet --mode gtp"
["445.gobmk.2"]="gobmk --quiet --mode gtp"
["445.gobmk.3"]="gobmk --quiet --mode gtp"
["445.gobmk.4"]="gobmk --quiet --mode gtp"
["445.gobmk.5"]="gobmk --quiet --mode gtp"
["447.dealII.1"]="dealII 23"
["450.soplex.1"]="soplex -s1 -e -m45000 pds-50.mps"
["450.soplex.2"]="soplex -m3500 ref.mps"
["453.povray.1"]="povray SPEC-benchmark-ref.ini"
["454.calculix.1"]="calculix -i hyperviscoplastic"
["456.hmmer.1"]="hmmer nph3.hmm swiss41"
["456.hmmer.2"]="hmmer --fixed 0 --mean 500 --num 500000 --sd 350 --seed 0 retro.hmm"
["458.sjeng.1"]="sjeng ref.txt"
["459.GemsFDTD.1"]="GemsFDTD"
["462.libquantum.1"]="libquantum 1397 8"
["464.h264ref.1"]="h264ref -d foreman_ref_encoder_baseline.cfg"
["464.h264ref.2"]="h264ref -d foreman_ref_encoder_main.cfg"
["464.h264ref.3"]="h264ref -d sss_encoder_main.cfg"
["465.tonto.1"]="tonto"
["470.lbm.1"]="lbm 3000 reference.dat 0 0 100_100_130_ldc.of"
["471.omnetpp.1"]="omnetpp omnetpp.ini"
["473.astar.1"]="astar BigLakes2048.cfg"
["473.astar.2"]="astar rivers.cfg"
["481.wrf.1"]="wrf"
["482.sphinx3.1"]="sphinx_livepretend ctlfile . args.an4"
["483.xalancbmk.1"]="Xalan -v t5.xml xalanc.xsl"
)

# Input for some programas

declare -A inp
inp=(
["416.gamess.1"]="cytosine.2.config"
["416.gamess.2"]="h2ocu2+.gradient.config"
["416.gamess.3"]="triazolium.config"
["433.milc.1"]="su3imp.in"
["437.leslie3d.1"]="leslie3d.in"
["445.gobmk.1"]="13x13.tst"
["445.gobmk.2"]="nngs.tst"
["445.gobmk.3"]="score2.tst"
["445.gobmk.4"]="trevorc.tst"
["445.gobmk.5"]="trevord.tst"
)

### Get started time
t_start=$(date +%s)

# Declare Mask to Applies
declare -a llcMask
llcMask=(0x0 
    0x1000 0x3000 0x7000 0xF000 
    0xF100 0xF300 0xF700 0xFF00
    0xFF10 0xFF30 0xFF70 0xFFF0
    0xFFF1 0xFFF3 0xFFF7 0xFFFF)

# Save actual dir
dAct=$(pwd)

for i in "${llcMask[@]}"; do
    for j in "${!bench[@]}"; do
        # Name Dir
        name=${j::-2}
        # Get CMD to execute
        if [ ! -z ${inp[$j]} ]; then
            cmd="./${bench[$j]} < ${inp[$j]} > /dev/null 2>&1"
        else
            cmd="./${bench[$j]} > /dev/null 2>&1"
        fi
        # Generate template
        echo "{" > tmp.json
        echo "    \"cmd\": \"$cmd\"," >> tmp.json
        cat template.json >> tmp.json
        # Generate outfolder
        mkdir $dOut/$j > /dev/null 2>&1
        outName=$dOut/$j/$i.out
        # Move to spec dir
        cd $dspec/
        echo $outName
        # Execute command
        $dScript/hwCounters.py 0 $i $dAct/tmp.json > $outName
        # Move again to de work dir
        cd $dAct
        # Remove temporal file
        rm tmp.json
    done
done

rm tmp.json

# Enable TurboBoost/PF
$damdCon/enable_turbo.sh
$damdCon/enable_pf.sh
