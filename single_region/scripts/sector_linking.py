#########################################
#######  SECTOR LINKING #################
#########################################
# This script will link sectors with wildcards to
# 'complete' sectors (those with no wildcards) in
# preparation for PCA.

import sys
import numpy as np
import pandas as pd
import time

##########################################################################################

t1 = time.time()

## Script requires filename argument

if len(sys.argv) < 3 :
    print('Usage: python link_sectors.py <reduced_patterns> <sector_dictionary>')
    sys.exit(0)

## Define custom datatype to read the sectors in from dictionary

dict_data_type = []
dict_data_type.append(('sector_index', 'i4'))
for layer in range(0,8):
    layer_string = str(layer)
    dict_data_type.append(('hashId_L'+layer_string,'i4'))

dict_records = np.fromfile(sys.argv[2], dict_data_type)
dict_df = pd.DataFrame(dict_records)
dict_df_copy = dict_df.copy()

dtype_list = []
dtype_list.append(('dict_index', 'i4'))
dtype_list.append(('pattern_index','i4'))
for layer in range(0,8):
    layer_string = str(layer)
    dtype_list.append(('hit_L'+layer_string,'uint16'))
pattern_data_type = dtype_list

pattern_records = np.fromfile(sys.argv[1], pattern_data_type)
pattern_df = pd.DataFrame(pattern_records)

##########################################################################################
## Don't need sectors with only one pattern - no good for PCA ############################
##########################################################################################

original_len = len(dict_df)

#first_single_pattern = len(dict_df) - (pattern_df.dict_index.value_counts() == 1).sum()
#dict_df = dict_df[dict_df.sector_index <= first_single_pattern]

#new_len = len(dict_df)

print('Total number of sectors', original_len)
#print('')
#print('Number of sectors with one pattern', original_len - new_len)
#print('Remaining number of sectors', new_len)

##########################################################################################
# First, link all the sectors with only one wildcard to a complete sector ################
##########################################################################################


## Construct dataframes containing complete sectors and sectors with one wildcard

layers = dict_df.columns[1:].tolist()

complete_sectors = dict_df.ix[dict_df.isin([-1]).sum(1) == 0].rename(
        columns={'sector_index' : 'complete_sector_index'})
one_wildcard_sectors = dict_df.ix[dict_df.isin([-1]).sum(1) == 1].rename(
        columns={'sector_index' : 'incomplete_sector_index'})

print('Number of complete sectors', len(complete_sectors))

## Select all the sectors that contain wildcards in each layer and store as separate dataframes

one_wildcard_sectors_list = []
for layer in range(8):
    wildcards = one_wildcard_sectors.loc[one_wildcard_sectors['hashId_L'+str(layer)]==-1]
    one_wildcard_sectors_list.append(wildcards)

linked_sector_list = []

for layer in range(8):
    
    ## Create subsets of dictionary - one with wildcard sectors, one without

    wildcard_df = one_wildcard_sectors_list[layer]

    ## Remove wildcard layer from all sectors in the original dict_df and subset_df

    wildcard_df_edit = wildcard_df.copy().drop('hashId_L' + str(layer), axis=1)
    complete_sectors_edit = complete_sectors.copy().drop('hashId_L' + str(layer), axis=1)

    ## Merge the two dataframes together such that, if the remaining 7 layers are the same,
    ## the complete sector ID is matched with the incomplete sector ID

    layer_subset = layers.copy().remove('hashId_L' + str(layer))
    merged = complete_sectors_edit.merge(wildcard_df_edit, on=layer_subset, how='inner')

    final = merged.drop_duplicates('incomplete_sector_index', keep='first')[[
        'complete_sector_index', 'incomplete_sector_index']]

    ## Fill a list with the matched sector indices

    linked_sector_list.append(final)

## Collect all the linked results

linked_sectors_one_wc = pd.concat(linked_sector_list).sort_values(by=['complete_sector_index'])
#print(linked_sectors_one_wc)

## Collect un-linked sectors

linked_ids = linked_sectors_one_wc.incomplete_sector_index
all_ids = one_wildcard_sectors.incomplete_sector_index
unlinked_ids_one = list(set(all_ids) - set(linked_ids))

print('There are', len(unlinked_ids_one), 'unlinked sectors with one wildcard')



##########################################################################################
# Now, a similar method can be used to link sectors with two wildcards ###################
##########################################################################################

## Once again, construct the dataframe of sectors with two wildcards

two_wildcard_sectors = dict_df.ix[dict_df.isin([-1]).sum(1) == 2].rename(
        columns={'sector_index' : 'incomplete_sector_index'})

## Store separate dataframes of sectors corresponding to where the first wildcard is.
## Unlike before, this step requires the removal of sectors once they have been loaded
## into one of the dataframes to avoid double-counting.

two_wildcard_sectors_list = []
wc_copy = two_wildcard_sectors.copy()
for layer in range(8):
    wildcards = wc_copy.loc[wc_copy['hashId_L'+str(layer)]==-1]
    wc_copy = wc_copy[~wc_copy.incomplete_sector_index.isin(wildcards.incomplete_sector_index)]
    two_wildcard_sectors_list.append(wildcards)

linked_sector_list = []

for layer_one in range(8):

    ## Select the dataframe of sectors whose first wildcard is in 'layer_one'
    
    wildcard_df = two_wildcard_sectors_list[layer_one]
    
    lower_level_sector_list = []
    partial_linked_sector_list = []

    ## All sectors with wildcards in 'layer_one' are now separated into another list of
    ## dataframes corresponding to where the second wildcard is. In this way, the same
    ## approach used for single-wildcard sectors can be used to link the all the sectors
    ## in the first dataframe. Looping through this list, the method is implemented 8 
    ## times to link all double-wildcard sectors

    for layer_two in range(8):

        if layer_one == layer_two:
            lower_level_sector_list.append('ignore') ## can't have both wildcards in the same layer
            continue

        wildcards = wildcard_df.loc[wildcard_df['hashId_L' + str(layer_one)] == -1]
        lower_level_sector_list.append(wildcards)


    ## New loop started to avoid building this list at each iteration

    for layer_two in range(8):

        if layer_one == layer_two:
            continue ## to avoid trying to remove the same layer twice


        ## Remove both wildcard positions from complete and incomplete sectors

        wildcard_df_edit = wildcard_df.copy().drop('hashId_L' + str(layer_one), axis=1).drop(
                'hashId_L' + str(layer_two), axis=1)
        complete_sectors_edit = complete_sectors.copy().drop('hashId_L' + str(layer_one), 
                axis=1).drop('hashId_L' + str(layer_two), axis=1)

        ## Again, merge the dataframes on the remaining six layers to link sector indices

        layers = dict_df.columns[1:].tolist()
        layers.remove('hashId_L' + str(layer_one))
        layers.remove('hashId_L' + str(layer_two))

        merged = complete_sectors_edit.merge(wildcard_df_edit, on=layers, how='inner')
        final = merged.drop_duplicates('incomplete_sector_index', keep='first')[[
            'complete_sector_index', 'incomplete_sector_index']]

        partial_linked_sector_list.append(final)

    ## Collect the results from each iteration

    partial_linked_sectors = pd.concat(partial_linked_sector_list).sort_values(by=[
        'complete_sector_index'])

    linked_sector_list.append(partial_linked_sectors)

linked_sectors_two_wc = pd.concat(linked_sector_list).sort_values(by=['complete_sector_index'])
#print(linked_sectors_two_wc)

## Find unlinked sectors with two wildcards

linked_ids = linked_sectors_two_wc.incomplete_sector_index
all_ids = two_wildcard_sectors.incomplete_sector_index
unlinked_ids_two = list(set(all_ids) - set(linked_ids))

print('There are', len(unlinked_ids_two), 'unlinked sectors with two wildcards')



##########################################################################################
# Combine the results from one- and two-wildcard linking #################################
##########################################################################################



all_linked_sectors_list = [linked_sectors_one_wc, linked_sectors_two_wc]
all_linked_sectors = pd.concat(all_linked_sectors_list).sort_values(
        by=['complete_sector_index'])

print(all_linked_sectors)

unlinked_sectors_list = unlinked_ids_one + unlinked_ids_two
unlinked_sectors = pd.DataFrame(unlinked_sectors_list, columns=['incomplete_sector_index'])

print(unlinked_sectors)

print('')
print('There are', len(unlinked_ids_one), 'unlinked sectors with one wildcard')
print('')
print('There are', len(unlinked_ids_two), 'unlinked sectors with two wildcards')
print('')
print('In total,', len(unlinked_sectors), 'unlinked sectors and', len(
    all_linked_sectors), 'linked sectors')
print('')
print('Completed in:', time.time() - t1, 'seconds')
print('')

unlinked_patterns = pattern_df[pattern_df.dict_index.isin(unlinked_sectors_list)]

print('Number of unlinked patterns =', len(unlinked_patterns))

##########################################################################################
# Saving results to file #################################################################
##########################################################################################


linked_array = np.array(all_linked_sectors, dtype=np.int32)
unlinked_array = np.array(unlinked_sectors, dtype=np.int32)


linked_fileobject = open('linked_sectors.bin', 'wb')
unlinked_fileobject = open('unlinked_sectors.bin', 'wb')
linked_array.tofile(linked_fileobject)
unlinked_array.tofile(unlinked_fileobject)
linked_fileobject.close()
unlinked_fileobject.close()


##########################################################################################

