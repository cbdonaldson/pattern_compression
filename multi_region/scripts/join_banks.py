import sys
import numpy as np
import pandas as pd

dtype_list = []
dtype_list.append(('dict_index', 'i4'))
dtype_list.append(('pattern_index','i4'))
for layer in range(0,8):
    layer_string = str(layer)
    dtype_list.append(('hit_L'+layer_string,'uint16'))
pattern_data_type = dtype_list

region_0 = np.fromfile(sys.argv[1], pattern_data_type)
region_1 = np.fromfile(sys.argv[2], pattern_data_type)
region_2 = np.fromfile(sys.argv[3], pattern_data_type)
region_3 = np.fromfile(sys.argv[4], pattern_data_type)

region_0_df = pd.DataFrame(region_0)
region_1_df = pd.DataFrame(region_1)
region_2_df = pd.DataFrame(region_2)
region_3_df = pd.DataFrame(region_3)

dfs = [region_0_df, region_1_df, region_2_df, region_3_df]
df = pd.concat(dfs)

approx_patterns = [tuple(pattern) for pattern in df.values]
approx_pattern_bank_array = np.array(approx_patterns, dtype=pattern_data_type)
pattern_bank_fileobject = open('restored_patterns_joined.bin', 'wb')
approx_pattern_bank_array.tofile(pattern_bank_fileobject)
pattern_bank_fileobject.close()
