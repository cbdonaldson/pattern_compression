# Pattern Compression

This project uses two methods of compression to optimise the representation and storage of ATLAS ITK pattern banks. The first is a lossless dictionary-based compression to remove redundancies in the pattern banks. Then, principal component analysis (PCA) is used to lower the dimensionality of the patterns. The format of the banks is as follows:

patternIndex  |  hashId_L0  |  hit_L0  |  hashId_L1  |  hit_L1  |  ...  |  hashId_L7  |  hit_L7  


![image](https://github.com/cbdonaldson/pattern_compression/blob/master/pb.png)

any change


