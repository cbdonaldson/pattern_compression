####################################################################
## Compress patternData file with PCA ##############################
####################################################################
## First the dictionary based compression (producing reduced_patterns.bin
## and sector_dictionary.bin), then sector linking will be performed
## (linked_sectors.bin and unlinked_sectors.bin). Finally, PCA compression
## on the reduced pattern bank produces a lower-dimensional pattern bank with
## mean/eigenpatterns stored for each sector. Outputs are stored in
## ./outputs/<pattern_id>/bin/.
##
## The script takes the pattern_id, number of components for PCA, maxStripP
## value and maxCol value (from patternAnalysis.cpp) as arguments:
##
## Usage: source pattern_compression.sh <pattern_id> <num_components> <max_strip> <max_col>
##

export pattern_id=$1
export num_components=$2
export max_strip=$3
export max_col=$4

cd ../outputs/
mkdir $pattern_id/
cd $pattern_id
mkdir bin/
cd ../../scripts/

python dictionary_compression.py ../banks/patternData_$pattern_id.bin
mv *.bin ../outputs/$pattern_id/bin/
python sector_linking.py ../outputs/$pattern_id/bin/reduced_patterns.bin ../outputs/$pattern_id/bin/sector_dictionary.bin
mv *.bin ../outputs/$pattern_id/bin/
python pca_compression.py ../outputs/$pattern_id/bin/reduced_patterns.bin ../outputs/$pattern_id/bin/sector_dictionary.bin ../outputs/$pattern_id/bin/linked_sectors.bin ../outputs/$pattern_id/bin/unlinked_sectors.bin $num_components $max_strip $max_col
mv *.bin ../outputs/$pattern_id/bin/
cd ../

