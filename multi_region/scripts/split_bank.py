import sys
import numpy as np
import pandas as pd

dtype_list = []
dtype_list.append(('pIdx', 'int32'))
dtype_list.append(('region', 'int32'))
for layer in range(0,8) :
	layer_string = str(layer)
	dtype_list.append(('detId_L'+layer_string,'int32'))
	dtype_list.append(('hit_L'+layer_string,'uint16'))

pattern_data_type = np.dtype(dtype_list)
pattern_records = np.fromfile(sys.argv[1], pattern_data_type)
pattern_df = pd.DataFrame(pattern_records)

dt_list = []
dt_list.append(('pIdx', 'int32'))
for layer in range(0,8) :
	layer_string = str(layer)
	dt_list.append(('detId_L'+layer_string,'int32'))
	dt_list.append(('hit_L'+layer_string,'uint16'))

dt = np.dtype(dt_list)

for region in range(4):
    df = pattern_df[pattern_df.region == region].drop('region', axis=1)
    patterns = [tuple(pattern) for pattern in df.values]
    pattern_array = np.array(patterns, dt)
    pattern_bank_fileobject = open('patternData_region_' + str(region) + '.bin', 'wb')
    pattern_array.tofile(pattern_bank_fileobject)
    pattern_bank_fileobject.close()

