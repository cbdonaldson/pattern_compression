# Pattern Compression
## Installation

Python 3.6.8  
Pandas 0.24.2

```git clone https://github.com/cbdonaldson/pattern_compression```


To run, choose either ```single_region/run/``` or ```multi_region/run```  
then ```source pattern_compression.sh <patternbank_id> <num_components> <max_strip> <max_col>```  

The max_strip and max_col values must be known for the chosen pattern bank, with the num_components being optional (2 components recommended). The associated max_strip and max_col values can be found in ```banks/max.txt```.  E.g.

``` cd single_region/run/```
```source ATLAS-P2-ITK-05-00-00_eta0.1_6of8_pt4-400_30M-pix+strips-mixed21111122 2 21 1``` 

For an example of multi_region:

``` cd multi_region/run/```
``` source ATLAS-P2-ITK-05-00-00_eta1.2_6of8_pt4-400_30M-pix+strips-mixed21111122 2 21 1```

Results will be stored in ```outputs/<patternbank_id>/bin/```

## PatternBank

This project uses two methods of compression to optimise the representation and storage of ATLAS ITK pattern banks. The first is a lossless dictionary-based compression to remove redundancies in the pattern banks. Then, principal component analysis (PCA) is used to lower the dimensionality of the patterns. The input pattern banks are generated from an associated C++ framework (link) and stored in ```banks/``` ; the format of the banks is as follows:


![](https://github.com/cbdonaldson/pattern_compression/blob/master/images/pattern_format.png)

Pattern compression can be performed on banks in different eta regions, with barrel-endcap transition regions (\eta = 1.2-1.4) requiring a different workflow. In this case, the 'multi_region' pathway is used and the bank is split into different sub-banks corresponding to different layer combinations. The compression is then performed on each bank separately before combining the results. For other regions containing only one layer combination, the 'single_region' pathway should be used.

## Compression Workflow

The compression workflow begins by grouping patterns into sectors, defined by a common set of detector element IDs. The output is a sector dictionary containing the full list of sectors with associated sector indicies, and a reduced pattern bank in which patterns are described only in terms of the pattern index and hits.

![](https://github.com/cbdonaldson/pattern_compression/blob/master/images/dictionary_compression.png)

Due to the presence of missing hits in many patterns, some sectors contain one/two empty detector elements and are referred to as single/double wildcard sectors. A sector-linking algorithm will match these incomplete sectors to the corresponding complete sectors, choosing the most populous sector if ambiguities arise. The resulting output 'linked_sectors.bin' contains, for each complete sector, the set of corresponding incomplete sectors. Additionally, a file 'unlinked_sectors.bin' is created, listing those sectors that have no corresponding complete sectors.

![](https://github.com/cbdonaldson/pattern_compression/blob/master/images/sector_linking.png)

The number of components can be chosen for PCA compression to reduce the dimensionality of the patterns. The patterns are decoded before applying PCA so that input patterns to the compression algorithm are of the form:

![](https://github.com/cbdonaldson/pattern_compression/blob/master/images/decoded_pattern.png)

where the range of values for each component depends on the eta region of the pattern bank. In general, the column value is a categorical variable with which the sectors are split into multiple sub-sectors. The PCA compression is then performed on these sub-sectors, storing the compressed patterns, eigenpatterns and mean pattern for each one.For wildcard sectors, the patterns are merged with the corresponding complete sector, the wildcard layer is dropped and the PCA parameters calculated using the combined pattern set. After this, only those patterns belonging to original wildcard sector are selected and stored, with the wildcard inserted back into the pattern. A similar approach is taken with the unlinked sectors without the added benefit of merging patterns to improve statistics.  









