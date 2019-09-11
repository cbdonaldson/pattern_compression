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
## The script takes the pattern_id, number of components for PCA and maxStripP
## value (from patternAnalysis.cpp) as arguments:
##
## Usage: source run_approximation.sh <pattern_id> <num_components> <max_strip>
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

python split_bank.py ../banks/patternData_$pattern_id.bin
mkdir temp_banks/
mv *.bin temp_banks/

for region in 0 1 2 3
do

	mkdir ../outputs/$pattern_id/bin/region_$region/
	mv temp_banks/patternData_region_$region.bin ../outputs/$pattern_id/bin/region_$region/


	python dictionary_compression.py ../outputs/$pattern_id/bin/region_$region/patternData_region_$region.bin
	mv *.bin ../outputs/$pattern_id/bin/region_$region/
	python sector_linking.py ../outputs/$pattern_id/bin/region_$region/reduced_patterns.bin ../outputs/$pattern_id/bin/region_$region/sector_dictionary.bin
	mv *.bin ../outputs/$pattern_id/bin/region_$region/
	python pca_compression.py ../outputs/$pattern_id/bin/region_$region/reduced_patterns.bin ../outputs/$pattern_id/bin/region_$region/sector_dictionary.bin ../outputs/$pattern_id/bin/region_$region/linked_sectors.bin ../outputs/$pattern_id/bin/region_$region/unlinked_sectors.bin $num_components $max_strip $max_col
	mv *.bin ../outputs/$pattern_id/bin/region_$region/
	

done

mv temp_banks/ ../outputs/$pattern_id/bin/ 

python join_banks.py ../outputs/$pattern_id/bin/region_0/restored_patterns_full.bin ../outputs/$pattern_id/bin/region_1/restored_patterns_full.bin ../outputs/$pattern_id/bin/region_2/restored_patterns_full.bin ../outputs/$pattern_id/bin/region_3/restored_patterns_full.bin

mv *.bin ../outputs/$pattern_id/bin/

