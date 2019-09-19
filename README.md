# Pattern Compression

This project uses two methods of compression to optimise the representation and storage of ATLAS ITK pattern banks. The first is a lossless dictionary-based compression to remove redundancies in the pattern banks. Then, principal component analysis (PCA) is used to lower the dimensionality of the patterns. The input pattern banks can be generated from an associated C++ framework (link); the format of the banks is as follows:


![](https://github.com/cbdonaldson/pattern_compression/blob/master/images/pattern_format.png)


Pattern compression can be performed on banks in different eta regions, with barrel-endcap transition regions (\eta = 1.2-1.4) requiring a different workflow. In this case, the bank is split into different sub-banks corresponding to different layer combinations, and the compression is performed on each bank separately before combining the results. For other regions containing only one layer combination, the 'single_region' pathway should be used.

## Compression Workflow

The compression workflow begins by grouping patterns into sectors, defined by a common set of detector element IDs. The output is a sector dictionary containing the full list of sectors with associated sector indicies, and a reduced pattern bank whereby patterns are described only in terms of the pattern index and hits.

![](https://github.com/cbdonaldson/pattern_compression/blob/master/images/dictionary_compression.png)

Due to the presence of missing hits in many patterns, some sectors contain one/two empty detector elements and are referred to as single/double wildcard sectors.









