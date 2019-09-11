#############################################
############# PCA Compression ###############
#############################################

import sys
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import normalize

from decoder import encode_hit, decode_hit, encode_sector, decode_sector, encode_wc_sector, encode_wc_sector_no_pixel

from progressbar import ProgressBar
pbar = ProgressBar()

########################################################################################
## Define custom datatypes #############################################################
########################################################################################

## 'pattern datatype'

pattern_datatype = []
pattern_datatype.append(('dict_index', 'i4'))
pattern_datatype.append(('pattern_index','i4'))
for layer in range(0,8):
    pattern_datatype.append(('hit_L' + str(layer),'uint16'))

## 'dict datatype'

dict_datatype = []
dict_datatype.append(('sector_index', 'i4'))
for layer in range(0,8):
    dict_datatype.append(('hit_L' + str(layer),'i4'))

## 'mean datatype'

mean_datatype = []
mean_datatype.append(('dict_index', 'i4'))
#mean_datatype.append(('pixel_position', 'int8'))
mean_datatype.append(('col', 'int8'))
mean_datatype.append(('pix_row', 'int8'))
for layer in range(7):
    mean_datatype.append(('hit_L' + str(layer+1), 'int8'))
mean_dt = np.dtype(mean_datatype)

## 'linked' and 'unlinked datatypes'

linked_datatype = [('complete_sector_index', 'i4'), ('incomplete_sector_index', 'i4')]
unlinked_datatype = [('incomplete_sector_index', 'i4')]

## 'compressed datatype'

num_components = int(sys.argv[5])
compressed_dt_list = []
compressed_dt_list.append(('dict_index', 'i4'))
compressed_dt_list.append(('pattern_index', 'i4'))
for layer in range(num_components):
    compressed_dt_list.append(('lambda_' + str(layer+1), 'int8'))
compressed_dt = np.dtype(compressed_dt_list)

## 'variance datatype'

variance_dt_list = []
variance_dt_list.append(('sector_index', 'i4'))
variance_dt_list.append(('explained_variance', 'float'))
variance_dt = np.dtype(variance_dt_list)

########################################################################################
## Read in files #######################################################################
########################################################################################

pattern_records = np.fromfile(sys.argv[1], pattern_datatype)
pattern_df = pd.DataFrame(pattern_records)

dict_records = np.fromfile(sys.argv[2], dict_datatype)
dict_df = pd.DataFrame(dict_records)

linked_sectors = np.fromfile(sys.argv[3], linked_datatype)
linked_df = pd.DataFrame(linked_sectors)

unlinked_sectors = np.fromfile(sys.argv[4], unlinked_datatype)
unlinked_df = pd.DataFrame(unlinked_sectors)

maxStripP = np.uint16(sys.argv[6])
maxCol = np.uint16(sys.argv[7])

########################################################################################
## Set labels for encoded, decoded & compressed patterns ###############################
########################################################################################

encoded_labels = []
for layer in range(8):
    encoded_labels.append('hit_L' + str(layer))

compressed_labels = []
compressed_labels.append('dict_index')
compressed_labels.append('pattern_index')
for component in range(num_components):
        compressed_labels.append('lambda' + str(component+1))

compressed_info_labels = []
compressed_info_labels.append('sectorIdx')
compressed_info_labels.append('col')
compressed_info_labels.append('pix_row')
for layer in range(7):
    compressed_info_labels.append('hit_L' + str(layer+1))

comp_labels = []
comp_labels.append('pix_row')
for layer in range(7):
    comp_labels.append('hit_L' + str(layer+1))

eigen_labels = compressed_info_labels[1:]

decoded_labels = []
decoded_labels.append('pix_row')
decoded_labels.append('pix_col')
for layer in range(7):
    decoded_labels.append('hit_L' + str(layer+1))

lambda_labels = []
for component in range(num_components):
        lambda_labels.append('lambda' + str(component+1))

pattern_labels = []
pattern_labels.append('dict_index')
pattern_labels.append('pattern_index')
for layer in range(8):
    pattern_labels.append('hit_L' + str(layer))

variance_labels = ['sector_index', 'explained_variance']


#######################################################################################
## Initiate compressed banks and begin looping through sectors  #######################
#######################################################################################

restored_pattern_bank = pd.DataFrame([], columns=pattern_labels)
compressed_pattern_bank = pd.DataFrame([], columns=compressed_labels)
compressed_info_bank = pd.DataFrame([], columns=compressed_info_labels)

explained_variance_df = pd.DataFrame([], columns=variance_labels)


#complete_sector_ids = pattern_df.dict_index.unique().tolist()

complete_sector_ids = dict_df.ix[dict_df.isin([-1]).sum(1) == 0].sector_index.values

print('looping through complete_sector_ids...')

for sectorIdx in pbar(complete_sector_ids):

    ## select sector

    group = pattern_df.loc[pattern_df['dict_index']==sectorIdx]
    sector_data = group.drop(['dict_index'], axis=1).drop(['pattern_index'], axis=1)

    ## select the corresponding incomplete sectors

    linked_sectors = linked_df[linked_df.complete_sector_index == sectorIdx].values[:,1]
    linked_groups = pattern_df[pattern_df.dict_index.isin(linked_sectors)]

    ## apply decoder to entire sector

    pattern_values = sector_data.values
    pattern_list = decode_sector(pattern_values, maxStripP)

    ## split by column

    hit_df = pd.DataFrame(pattern_list, columns=decoded_labels)
    hit_df.insert(0, 'pattern_index', group['pattern_index'].values)

    column_list = []
    
    for col in range(maxCol + 1):

        subset = hit_df[hit_df.pix_col == col].drop('pix_col', axis=1)

        subset_patterns = subset.drop('pattern_index', axis=1)
        subset_values = subset_patterns.values
        column_list.append(subset_patterns)
    
        if (len(subset_values) > num_components):

            patt_pca = PCA(num_components)
            subset_values_proj = patt_pca.fit_transform(subset_values).round().astype(int)

            ## store the compressed patterns

            compressed_patterns = np.array(subset_values_proj)
            compressed_patterns_df = pd.DataFrame(compressed_patterns, columns=lambda_labels)

            compressed_patterns_df.insert(0, 'pattern_index', subset['pattern_index'].values)
            compressed_patterns_df.insert(0, 'dict_index', sectorIdx)
       
            compressed_pattern_bank = compressed_pattern_bank.append(compressed_patterns_df)

            ##

            restored_values = patt_pca.inverse_transform(subset_values_proj)
            encoded_patterns = encode_sector(restored_values, maxStripP, col)
    
            restored_pattern_df = pd.DataFrame(encoded_patterns, columns=encoded_labels)
            restored_pattern_df.insert(0, 'pattern_index', subset['pattern_index'].values)
            restored_pattern_df.insert(0, 'dict_index', sectorIdx)
    
            restored_pattern_bank = restored_pattern_bank.append(restored_pattern_df)    


            ## collect mean/eigenpatterns

            compressed_info = []
            p0 = patt_pca.mean_.round().astype(int)
            compressed_info.append(p0)
            for component in range(num_components):
                epattern = patt_pca.components_[component]
                eigenpattern = np.array([x*100 for x in epattern]).round().astype(int)
                compressed_info.append(eigenpattern)

            compressed_info_df = pd.DataFrame(compressed_info, columns=comp_labels)
            compressed_info_df.insert(0, 'col', col)
            compressed_info_df.insert(0, 'sectorIdx', sectorIdx)
            compressed_info_bank = compressed_info_bank.append(compressed_info_df)


    #####################################################################################
    ## begin looping over linked sectors ################################################
    ######################################################################################
    
    if len(linked_sectors) > 0:
        
        for sector_id in linked_sectors:
            
            ## find the wildcards
            
            sector = dict_df[dict_df.sector_index == sector_id]
            wildcards = []
            wildcard_layers = []
            wildcard_position = []
            counter = 0
            for column in sector.columns.drop('sector_index'):
                if (sector[column] == -1).all():
                    if column == 'hit_L0':
                        wildcards.append('pix_row')
                        wildcards.append('pix_col')
                        wildcard_layers.append('hit_L0')
                        wildcard_position.append(counter)
                    else:
                        wildcards.append(column)
                        wildcard_layers.append(column)
                        wildcard_position.append(counter)
                counter += 1
            
            num_wildcards = len(wildcard_layers)
            
            if 'hit_L0' in wildcard_layers:
                
                group = linked_groups[linked_groups.dict_index == sector_id]
                sector_data = group.drop(['dict_index'], axis=1).drop(
                                     ['pattern_index'], axis=1)
            
                pattern_values = sector_data.values
                pattern_list = decode_sector(pattern_values, maxStripP)
                linked_hit_df = pd.DataFrame(pattern_list, columns=decoded_labels)
                
                ## combine pattern sets
                
                complete_df = hit_df.drop('pattern_index', axis=1)
                combined_hit_df = pd.concat([complete_df, linked_hit_df])
                
                ## remove wildcard layers
                
                for wildcard in range(len(wildcards)):
                    combined_hit_df = combined_hit_df.drop(wildcards[wildcard], axis=1)
                cols = combined_hit_df.columns
         
                ## pca on reduced sector
                
                patt_pca = PCA(num_components)
                Y = combined_hit_df.values
                Y_proj = patt_pca.fit_transform(Y).round().astype(int)
                
                ## store compressed patterns

                compressed_patterns = np.array(Y_proj)
                compressed_patterns_df = pd.DataFrame(compressed_patterns, columns=lambda_labels)
                compressed_linked_df = compressed_patterns_df.tail(len(linked_hit_df))
                compressed_linked_df.insert(0, 'pattern_index', group.iloc[:,1].values)

                compressed_linked_df.insert(0, 'dict_index', sectorIdx)

                compressed_pattern_bank = compressed_pattern_bank.append(compressed_linked_df)

                ## restore patterns
                
                restored_patterns = patt_pca.inverse_transform(Y_proj)
                encoded_patterns = encode_wc_sector_no_pixel(restored_patterns, maxStripP, num_wildcards)
                restored_patterns_df = pd.DataFrame(encoded_patterns, columns=cols)
                incomplete_patterns_df = restored_patterns_df.tail(len(linked_hit_df))
                for wildcard in range(len(wildcard_layers)):
                    incomplete_patterns_df.insert(wildcard_position[wildcard], wildcard_layers[wildcard], 0)
                incomplete_patterns_df.insert(0, 'pattern_index', group['pattern_index'].values)
                incomplete_patterns_df.insert(0, 'dict_index', sector_id)
                
                restored_pattern_bank = restored_pattern_bank.append(incomplete_patterns_df)
                
            else:
                
                group = linked_groups[linked_groups.dict_index == sector_id]
                sector_data = group.drop(['dict_index'], axis=1).drop(
                                     ['pattern_index'], axis=1)
            
                pattern_values = sector_data.values
                pattern_list = decode_sector(pattern_values, maxStripP)
                linked_hit_df = pd.DataFrame(pattern_list, columns=decoded_labels)
                linked_hit_df.insert(0, 'pattern_index', group['pattern_index'].values)
                
                ## split by column

                for col in range(maxCol + 1):
               
                    column_wc = linked_hit_df[linked_hit_df.pix_col == col].drop('pix_col', axis=1)
                    column_wc_patterns = column_wc.drop('pattern_index', axis=1)
                    wc_values = column_wc_patterns.values
                
                    if len(wc_values) > num_components:
                    
                        combined_values_df = pd.concat([column_list[col], column_wc_patterns])
                    
                         ## remove wildcard layers
                
                        for wildcard in range(len(wildcards)):
                            combined_values_df = combined_values_df.drop(wildcards[wildcard], axis=1)
                        cols = combined_values_df.columns
                    
                        ## pca on reduced sector
                
                        patt_pca = PCA(num_components)
                        Y = combined_values_df.values
                        Y_proj = patt_pca.fit_transform(Y).round().astype(int)

                        ## store compressed patterns
        
                        compressed_patterns = np.array(Y_proj)
                        compressed_patterns_df = pd.DataFrame(compressed_patterns, columns=lambda_labels)
                        compressed_linked_df = compressed_patterns_df.tail(len(column_wc))
                        compressed_linked_df.insert(0, 'pattern_index', column_wc['pattern_index'].values)

                        compressed_linked_df.insert(0, 'dict_index', sectorIdx)

                        compressed_pattern_bank = compressed_pattern_bank.append(compressed_linked_df)
                    
                        ## restore patterns
                
                        restored_patterns = patt_pca.inverse_transform(Y_proj)
                        encoded_patterns = encode_wc_sector(restored_patterns, maxStripP, col, num_wildcards)
                        restored_patterns_df = pd.DataFrame(encoded_patterns, columns=cols)
                        restored_patterns_df = restored_patterns_df.rename(columns={'pix_row' : 'hit_L0'})
                        incomplete_patterns_df = restored_patterns_df.tail(len(column_wc))
                        for wildcard in range(len(wildcard_layers)):
                            incomplete_patterns_df.insert(wildcard_position[wildcard], wildcard_layers[wildcard], 0)
                        incomplete_patterns_df.insert(0, 'pattern_index', column_wc['pattern_index'].values)
                        incomplete_patterns_df.insert(0, 'dict_index', sector_id)
                    
                        restored_pattern_bank = restored_pattern_bank.append(incomplete_patterns_df)
               

## Finally, need to consider "unlinked" sectors

unlinked_sectors = unlinked_df.incomplete_sector_index.values

print('looping through unlinked_sectors...')

for sector_id in unlinked_sectors:
    
    ## find the wildcards
            
    sector = dict_df[dict_df.sector_index == sector_id]
    wildcards = []
    wildcard_layers = []
    wildcard_position = []
    counter = 0
    for column in sector.columns.drop('sector_index'):
        if (sector[column] == -1).all():
            if column == 'hit_L0':
                wildcards.append('pix_row')
                wildcards.append('pix_col')
                wildcard_layers.append('hit_L0')
                wildcard_position.append(counter)
            else:
                wildcards.append(column)
                wildcard_layers.append(column)
                wildcard_position.append(counter)
        counter += 1
            
    num_wildcards = len(wildcard_layers)
            
    if 'hit_L0' in wildcard_layers:
                
        group = pattern_df[pattern_df.dict_index == sector_id]
        sector_data = group.drop(['dict_index'], axis=1).drop(
                                     ['pattern_index'], axis=1)
            
        pattern_values = sector_data.values
        pattern_list = decode_sector(pattern_values, maxStripP)
        unlinked_hit_df = pd.DataFrame(pattern_list, columns=decoded_labels)
                
        ## remove wildcard layers
                
        for wildcard in range(len(wildcards)):
            unlinked_hit_df = unlinked_hit_df.drop(wildcards[wildcard], axis=1)
        cols = unlinked_hit_df.columns
         
        ## pca on reduced sector
                
        patt_pca = PCA(num_components)
        Y = unlinked_hit_df.values

        if len(Y) > num_components:

            Y_proj = patt_pca.fit_transform(Y).round().astype(int)
                
            ## restore patterns
                
            restored_patterns = patt_pca.inverse_transform(Y_proj)
            encoded_patterns = encode_wc_sector_no_pixel(restored_patterns, maxStripP, num_wildcards)
            restored_patterns_df = pd.DataFrame(encoded_patterns, columns=cols)
            for wildcard in range(len(wildcard_layers)):
                restored_patterns_df.insert(wildcard_position[wildcard], wildcard_layers[wildcard], 0)
            restored_patterns_df.insert(0, 'pattern_index', group['pattern_index'].values)
            restored_patterns_df.insert(0, 'dict_index', sector_id)
                
            restored_pattern_bank = restored_pattern_bank.append(restored_patterns_df)
                
    else:
                
        group = pattern_df[pattern_df.dict_index == sector_id]
        sector_data = group.drop(['dict_index'], axis=1).drop(
                                     ['pattern_index'], axis=1)
            
        pattern_values = sector_data.values
        pattern_list = decode_sector(pattern_values, maxStripP)
        unlinked_hit_df = pd.DataFrame(pattern_list, columns=decoded_labels)
        unlinked_hit_df.insert(0, 'pattern_index', group['pattern_index'].values)
                
        ## split by column
                
        for col in range(maxCol + 1):
               
            column_wc = unlinked_hit_df[unlinked_hit_df.pix_col == col].drop('pix_col', axis=1)
            column_wc_patterns = column_wc.drop('pattern_index', axis=1)
            wc_values = column_wc_patterns.values
                
            if len(wc_values) > num_components:
                                        
                ## remove wildcard layers
                
                for wildcard in range(len(wildcards)):
                    column_wc_patterns = column_wc_patterns.drop(wildcards[wildcard], axis=1)
                cols = column_wc_patterns.columns
                    
                ## pca on reduced sector
                
                patt_pca = PCA(num_components)
                Y = column_wc_patterns.values
                Y_proj = patt_pca.fit_transform(Y).round().astype(int)
                
                ## store compressed patterns


                compressed_patterns = np.array(Y_proj)
                compressed_patterns_df = pd.DataFrame(compressed_patterns, columns=lambda_labels)

                compressed_patterns_df.insert(0, 'pattern_index', column_wc.pattern_index.values)
                compressed_patterns_df.insert(0, 'dict_index', sector_id)
            
                compressed_pattern_bank = compressed_pattern_bank.append(compressed_patterns_df)

                ## restore patterns
                
                restored_patterns = patt_pca.inverse_transform(Y_proj)
                encoded_patterns = encode_wc_sector(restored_patterns, maxStripP, col, num_wildcards)
                restored_patterns_df = pd.DataFrame(encoded_patterns, columns=cols)
                restored_patterns_df = restored_patterns_df.rename(columns={'pix_row' : 'hit_L0'})
                for wildcard in range(len(wildcard_layers)):
                    restored_patterns_df.insert(wildcard_position[wildcard], wildcard_layers[wildcard], 0)
                restored_patterns_df.insert(0, 'pattern_index', column_wc['pattern_index'].values)
                restored_patterns_df.insert(0, 'dict_index', sector_id)
                
                    
                restored_pattern_bank = restored_pattern_bank.append(restored_patterns_df)


eigen_mean_patterns = [tuple(pattern) for pattern in compressed_info_bank.values]
eigen_array = np.array(eigen_mean_patterns, dtype = mean_dt)
eigen_fileobject = open('compressed_info.bin', 'wb')
eigen_array.tofile(eigen_fileobject)
eigen_fileobject.close()

compressed_patterns = [tuple(pattern) for pattern in compressed_pattern_bank.values]
compressed_array = np.array(compressed_patterns, dtype=compressed_dt)
pattern_bank_fileobject = open('compressed_patterns.bin', 'wb')
compressed_array.tofile(pattern_bank_fileobject)
pattern_bank_fileobject.close()

restored_patterns = [tuple(pattern) for pattern in restored_pattern_bank.values]
restored_pattern_array = np.array(restored_patterns, dtype=pattern_datatype)
bank_fileobject = open('restored_patterns_full.bin', 'wb')
restored_pattern_array.tofile(bank_fileobject)
bank_fileobject.close()


