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
dOut="$pwd/out/pf-2k17"
dspec="" # Benchmarks binary folder

#### Disable Turbo-Boost / Enable PF
$damdCon/disable_turbo.sh
$damdCon/enable_pf.sh

#### Prepare output folder
mkdir -p $dOut > /dev/null 2>&1


#### Benchmarks
declare -A bench
bench=(
["500.perlbench_r.1"]="./perlbench_r -I./lib checkspam.pl 2500 5 25 11 150 1 1 1 1"
["500.perlbench_r.2"]="./perlbench_r -I./lib diffmail.pl 4 800 10 17 19 300"
["500.perlbench_r.3"]="./perlbench_r -I./lib splitmail.pl 6400 12 26 16 100 0"
["502.gcc_r.1"]="./cpugcc_r gcc-pp.c -O3 -finline-limit=0 -fif-conversion -fif-conversion2 -o file"
["502.gcc_r.2"]="./cpugcc_r gcc-pp.c -O2 -finline-limit=36000 -fpic -o file"
["502.gcc_r.3"]="./cpugcc_r gcc-smaller.c -O3 -fipa-pta -o f"
["502.gcc_r.4"]="./cpugcc_r ref32.c -O5 -o f"
["502.gcc_r.5"]="./cpugcc_r ref32.c -O3 -fselective-scheduling -fselective-scheduling2 -o f"
["503.bwaves_r.1"]="./bwaves_r"
["503.bwaves_r.2"]="./bwaves_r"
["503.bwaves_r.3"]="./bwaves_r"
["503.bwaves_r.4"]="./bwaves_r"
["505.mcf_r.1"]="./mcf_r inp.in"
["507.cactuBSSN_r.1"]="./cactusBSSN_r spec_ref.par"
["508.namd_r.1"]="./namd_r --input apoa1.input --output apoa1.ref.output --iterations 65 "
["520.omnetpp_r.1"]="./omnetpp_r -c General -r 0"
["510.parest_r.1"]="./parest_r ref.prm"
["511.povray_r.1"]="./povray_r SPEC-benchmark-ref.ini"
["519.lbm_r.1"]="./lbm_r 3000 reference.dat 0 0 100_100_130_ldc.of"
["521.wrf_r.1"]="./wrf_r"
["523.xalancbmk_r.1"]="./cpuxalan_r -v t5.xml xalanc.xsl"
["525.x264_r.1"]="./x264_r --pass 1 --stats x264_stats.log --bitrate 1000 --frames 1000 -o BuckBunny_New.264 BuckBunny.yuv 1280x720"
["525.x264_r.2"]="./x264_r --pass 2 --stats x264_stats.log --bitrate 1000 --dumpyuv 200 --frames 1000 -o BuckBunny_New.264 BuckBunny.yuv 1280x720"
["525.x264_r.3"]="./x264_r --seek 500 --dumpyuv 200 --frames 1250 -o BuckBunny_New.264 BuckBunny.yuv 1280x720"
["526.blender_r.1"]="./blender_r sh3_no_char.blend --render-output sh3_no_char_ --threads 1 -b -F RAWTGA -s 849 -e 849 -a"
["527.cam4_r.1"]="./cam4_r"
["531.deepsjeng_r.1"]="./deepsjeng_r ref.txt"
["538.imagick_r.1"]="./imagick_r -limit disk 0 refrate_input.tga -edge 41 -resample 181% -emboss 31 -colorspace YUV -mean-shift 19x19+15% -resize 30% refrate_output.tga"
["541.leela_r.1"]="./leela_r ref.sgf"
["544.nab_r.1"]="./nab_r 1am0 1122214447 122"
["548.exchange2_r.1"]="./exchange2_r 6"
["549.fotonik3d_r.1"]="./fotonik3d_r"
["557.xz_r.1"]="./xz_r cld.tar.xz 160 19cf30ae51eddcbefda78dd06014b4b96281456e078ca7c13e1c0c9e6aaea8dff3efb4ad6b0456697718cede6bd5454852652806a657bb56e07d61128434b474 59796407 61004416 6"
["557.xz_r.2"]="./xz_r cpu2006docs.tar.xz 250 055ce243071129412e9dd0b3b69a21654033a9b723d874b2015c774fac1553d9713be561ca86f74e4f16f22e664fc17a79f30caa5ad2c04fbc447549c2810fae 23047774 23513385 6e"
["557.xz_r.3"]="./xz_r input.combined.xz 250 a841f68f38572a49d86226b7ff5baeb31bd19dc637a922a972b2e6d1257a890f6a544ecab967c313e370478c74f760eb229d4eef8a8d2836d233d3e9dd1430bf 40401484 41217675 7"
["554.roms_r.1"]="./roms_r"
)

# Input for some programas

declare -A inp
inp=(
["503.bwaves_r.1"]="bwaves_1.in"
["503.bwaves_r.2"]="bwaves_2.in"
["503.bwaves_r.3"]="bwaves_3.in"
["503.bwaves_r.4"]="bwaves_4.in"
["554.roms_r.1"]="ocean_benchmark2.in.x"
)

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
            echo $cmd
        fi
        # Generate template
        echo "{" > tmp.json
        echo "    \"cmd\": \"$cmd\"," >> tmp.json
        cat template.json >> tmp.json
        # Generate outfolder
        mkdir $dOut/$j > /dev/null 2>&1
        outName=$dOut/$j/$i.out
        # Move to spec dir
        cd $dspec/$name
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
