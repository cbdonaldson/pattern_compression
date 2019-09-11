##################################################
## Dictionary-based compression ##################
##################################################
## This script will factorise a patternData bank into
## a reduced pattern bank and sector dictionary.
##
## Usage: python dictionary_compression.py <patternDatafile>
##
##################################################

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import itertools as it

if len(sys.argv) < 2 :
	print('Usage: python factorise_patterns.py <patternData>')
	sys.exit(0)

## Create a custom numpy data type to describe pattern data as follows
## patternIndex | layer_0 detector element index | layer_0 hit data | ... | layer_7 detector element index | layer_7 hit data |

dtype_list = []
dtype_list.append(('pIdx', 'int32'))
for layer in range(0,8) :
	layer_string = str(layer)
	dtype_list.append(('detId_L'+layer_string,'int32'))
	dtype_list.append(('hit_L'+layer_string,'uint16'))

## Load data from binary file according to custom data type

print('Reading data from file...')

pattern_data_type = np.dtype(dtype_list)
pattern_records = np.fromfile(sys.argv[1], pattern_data_type)
pattern_df = pd.DataFrame(pattern_records)

## Group data by sector

print('Grouping into sectors...')

grouped = pattern_df.groupby(['detId_L0','detId_L1','detId_L2','detId_L3','detId_L4','detId_L5','detId_L6','detId_L7'])
sector_dict = grouped.groups

sector_list = []
patterns = []
sorted_dict = sorted(sector_dict, key=lambda k: len(sector_dict[k]), reverse=True)
for sector in sorted_dict:
    sector_list.append(sector)
    mygroup = grouped.get_group(sector)
    mygroup = mygroup.drop(mygroup.columns[[1,3,5,7,9,11,13,15]], axis=1)
    patterns.append(mygroup)

print("Number of sectors: "+str(len(sector_list)))

## Make a cumulative plot

#x = list(range(len(sector_list)))
#y = []
#pattern_sum = 0
#for sector in patterns:
#    pattern_sum += len(sector)
#    y.append(pattern_sum)
#
#plt.plot(#x,y)
#plt.title('Cumulative sum of patterns vs sector number in list') 
#plt.xlabel('Sector number')
#plt.ylabel('Cumulative sum of patterns')
#plt.savefig('cumulative_plot.png')
#
#print('Cumulative plot made!')

## Create custom data type

datatype_list = []
datatype_list.append(('dict_entry_index','int32'))
datatype_list.append(('pattern_index','int32'))
for layer in range(0,8):
    layer_string = str(layer)
    datatype_list.append(('hit_L'+layer_string,'uint16'))
dt = np.dtype(datatype_list)

## Write sector dictionary to binary file

sector_array = []
reduced_pattern_array = []

for sector in range(len(sector_list)):
    sector_row = [sector+1] + list(sector_list[sector])
    sector_array.append(sector_row)
	
    list_of_values = patterns[sector].values.tolist()
    
    for pattern_index in range(len(patterns[sector].index)):
        pattern_row = tuple([sector+1] + list_of_values[pattern_index])
        reduced_pattern_array.append(pattern_row)

print('Length of pattern array is:', len(reduced_pattern_array))

sector_dictionary = np.array(sector_array,dtype=np.int32)
reduced_patterns_final = np.array(reduced_pattern_array, dtype = dt)

for pattern in range(len(reduced_pattern_array)):
    reduced_patterns_final[pattern] = reduced_pattern_array[pattern]

print('Writing to files...')

sector_fileobject = open('sector_dictionary.bin','wb')
pattern_fileobject = open('reduced_patterns.bin','wb')
sector_dictionary.tofile(sector_fileobject)
reduced_patterns_final.tofile(pattern_fileobject)
sector_fileobject.close()
pattern_fileobject.close()

print('Done!')
print('')
print('')

