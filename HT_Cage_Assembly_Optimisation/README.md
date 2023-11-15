## HT_Cage_Assembly_Optimisation

Precursor Optimisation

A mixture of tri-topic and di-topic aldehydes and amines were selected as imine cage precursors.
Initially precursors were loaded in via their SMILES strings and a lowest energy conformer search is conducted using ETKDGv3. Kekulization of the aromatic bonds is also undertaken to ensure bond orders are correct for usage in stk as building blocks.
Precursors were then stored in a MoleculeMongoDB with their standarized SMILES strings as a key.
A mixture of tri-topic and di-topic aldehydes and amines were selected as imine cage precursors.

Cage Formation and Optimisation

Precursors were combined as complimentary tri-topic and di-topic amines and aldehdyes. Precursors were called from the MoleculeMongoDB and used as stk building blocks.
From one precursor pair, four cages were assembled using stk of the topologies: TwoPlusThree, FourPlusSix, SixPlusNine and EightPlusTwelve.

Once assembled, a three-step optimisation was conducted on each cage:
1. Restricted FF optimisation of the imine bonds 
2. Unrestricted FF optimisation of the whole molecule 
3. Molecular dynamics simulation to find the lowest energy conformer 

The lowest energy conformer of the constructed molecule was then stored in a ConstructedMoleculeMongoDB using a 'cage_key' formed of the catenated SMILES strings of the component precursors, along with a unique _id. Within the database, cages are stored in collections, grouped by topology: '2+3', '4+6', '6+9' and '8+12'. 

Porosity Properties Calculations

Each precursor combination is called from the ConstructedMoleculeMongoDB by its 'cage_key' from all four collections of topology using the 'get_cages' function. 
Then each cage in each topology of the precursor pair is written as a xyz and pdb file. The xyz file is loaded using pywindow as a molecular system (molsys) and then written as a pywindow molecule. 
The molecular weight, pore diameter, pore volume, number of and size of windows and centre of mass is calculated and stored as a dictionary. 
The function 'full_cage_analysis' combines the results of each cage topology of teh same precursor pair into one dictionary and writes a JSON file of the results.
