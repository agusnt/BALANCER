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
dScript="$pwd/../../lib/py"
dOut="$pwd/out"
dspec="" # CPU2006 binary folder 

#### Disable Turbo-Boost / Enable PF
$damdCon/disable_turbo.sh
$damdCon/enable_pf.sh

#### Prepare output folder
mkdir -p $dOut > /dev/null 2>&1

# Compile triad
cd ../c
gcc -O3 triad.c -o triad
cd ../sh

#### Benchmarks
declare -A bench
bench=(
["401.bzip2.3"]="bzip2 liberty.jpg 30"
["403.gcc.7"]="gcc g23.in -o g23.s"
["410.bwaves.1"]="bwaves"
["429.mcf.1"]="mcf inp.in"
["433.milc.1"]="milc"
["434.zeusmp.1"]="zeusmp"
["436.cactusADM.1"]="cactusADM benchADM.par"
["437.leslie3d.1"]="leslie3d"
["447.dealII.1"]="dealII 23"
["450.soplex.2"]="soplex -m3500 ref.mps"
["459.GemsFDTD.1"]="GemsFDTD"
["462.libquantum.1"]="libquantum 1397 8"
["470.lbm.1"]="lbm 3000 reference.dat 0 0 100_100_130_ldc.of"
["471.omnetpp.1"]="omnetpp omnetpp.ini"
["473.astar.1"]="astar BigLakes2048.cfg"
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
["503.bwaves_r.1"]="bwaves_1.in"
["503.bwaves_r.2"]="bwaves_2.in"
["503.bwaves_r.3"]="bwaves_3.in"
["503.bwaves_r.4"]="bwaves_4.in"
["554.roms_r.1"]="ocean_benchmark2.in.x"
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

declare -A nTriad=(
    [0]="N" 
    [3]="8 16 24"
    [7]="32 40 48 56"
    [14]="12 20 28 36 44 52 60"
)

# Save actual dir
dAct=$(pwd)
for k in $(seq 0 14); do
    if [[ -z ${nTriad[$k]} ]];then
        continue
    fi

    if [[ "${nTriad[$k]}" != "N" ]]; then
        for core in ${nTriad[$k]}; do
            taskset -c $core ../c/triad &
        done
    fi
    sleep 1
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
            outName=$dOut/$j/$i-Triads_$k.out
            # Move to spec dir
            cd $dspec/
            echo $outName
            # Execute command
            $dScript/hwCounters.py 0 $i $dAct/tmp.json ${nTriad2[$k]} > $outName
            # Move again to de work dir
            cd $dAct
            # Remove temporal file
            rm tmp.json
        done
    done
done
pkill -9 triad
rm tmp.json

dspec="" # CPU2017 binary folder
bench=(
["500.perlbench_r.3"]="./perlbench_r -I./lib splitmail.pl 6400 12 26 16 100 0"
["502.gcc_r.5"]="./cpugcc_r ref32.c -O3 -fselective-scheduling -fselective-scheduling2 -o f"
["503.bwaves_r.3"]="./bwaves_r"
["505.mcf_r.1"]="./mcf_r inp.in"
["507.cactuBSSN_r.1"]="./cactusBSSN_r spec_ref.par"
["510.parest_r.1"]="./parest_r ref.prm"
["519.lbm_r.1"]="./lbm_r 3000 reference.dat 0 0 100_100_130_ldc.of"
["520.omnetpp_r.1"]="./omnetpp_r -c General -r 0"
["521.wrf_r.1"]="./wrf_r"
["523.xalancbmk_r.1"]="./cpuxalan_r -v t5.xml xalanc.xsl"
["526.blender_r.1"]="./blender_r sh3_no_char.blend --render-output sh3_no_char_ --threads 1 -b -F RAWTGA -s 849 -e 849 -a"
["527.cam4_r.1"]="./cam4_r"
["549.fotonik3d_r.1"]="./fotonik3d_r"
["557.xz_r.1"]="./xz_r cld.tar.xz 160 19cf30ae51eddcbefda78dd06014b4b96281456e078ca7c13e1c0c9e6aaea8dff3efb4ad6b0456697718cede6bd5454852652806a657bb56e07d61128434b474 59796407 61004416 6"
["554.roms_r.1"]="./roms_r"
)

for k in $(seq 0 14); do
    if [[ -z ${nTriad[$k]} ]];then
        continue
    fi

    if [[ "${nTriad[$k]}" != "N" ]]; then
        for core in ${nTriad[$k]}; do
            taskset -c $core ../c/triad &
        done
    fi
    sleep 1
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
            outName=$dOut/$j/$i-Triads_$k.out
            # Move to spec dir
            cd $dspec/$name
            echo $outName
            # Execute command
            $dScript/hwCounters.py 0 $i $dAct/tmp.json ${nTriad2[$k]} > $outName
            # Move again to de work dir
            cd $dAct
            # Remove temporal file
            rm tmp.json
        done
    done
done
pkill -9 triad
rm tmp.json

# Enable TurboBoost/PF
$damdCon/enable_turbo.sh
$damdCon/enable_pf.sh
