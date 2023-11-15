from binascii import b2a_base64
import stk
import pymongo
import pandas as pd
import rdkit
import rdkit.Chem.AllChem as rdkit
from rdkit.Chem.MolStandardize import standardize_smiles
from typing import List
from pathos.pools import _ProcessPool as ProcessPool
import argparse
from uuid import uuid4
import os
from tqdm import tqdm
from functools import partial
from pathlib import Path
from pymongo import MongoClient
import csv
import logging
from pymongo.errors import ServerSelectionTimeoutError
import random
import logging
from rdkit import Chem

def mongo_client():
    return MongoClient(
        'mongodb://path_to_mongo:27017/'
    )
db_url = 'mongodb://path_to_mongo:27017/'

def quick_conf_search(smiles):
    try:
        logging.info(f"Optimising {smiles}")
        mol = Chem.MolFromSmiles(smiles)
        mol = Chem.AddHs(mol)
        Chem.Kekulize(mol, clearAromaticFlags=True)
        # Perform conformer search using ETKDGv3
        params = Chem.rdDistGeom.ETKDGv3()
        random_seed = 0
        params.random_seed = random_seed
        num_confs = 500
        embed_res = Chem.rdDistGeom.EmbedMultipleConfs(mol, num_confs, params)
        if embed_res == -1:
            logging.warning(
                f"Embedding failed with random seed {random_seed}. "
                "Returning None."
            )
            return None
        # Optimise all conformers of the molecule.
        res = Chem.rdForceFieldHelpers.MMFFOptimizeMoleculeConfs(
            mol, numThreads=36
        )
        while True:
            if len(res) == 0:
                logging.warning(
                    "All force field optimisations could not converge. "
                    "Returning None."
                )
                return None
            e_min_ind = res.index(min(res, key=lambda x: x[1]))
            converged = res[e_min_ind][0]
            if converged == 0:
                for i in range(num_confs):
                    if i == e_min_ind:
                        continue
                    mol.RemoveConformer(i)
                # Update ID of conformer
                mol.GetConformer(-1).SetId(0)
                return mol
            res.pop(e_min_ind)
    except Exception as err:
        print(err)
        return None

# Triamines
TriA = 'NC1=NC(N)=NC(N)=N1'
TriB = 'CC1=C(CN)C(C)=C(CN)C(C)=C1CN'
TriC = 'NCCN(CCN)CCN'
TriD = 'NCC1=C(CC)C(CN)=C(CC)C(CN)=C1CC'
TriE = 'NCCCN(CCCN)CCCN'
TriF = 'N[C@H]1C[C@@H](N)C[C@@H](N)C1'

# Trialdehydes
TriG = 'O=CC1=CC(C=O)=CC(C=O)=C1'
TriH = 'O=CC(C=C1)=CC=C1C2=CC(C3=CC=C(C=O)C=C3)=CC(C4=CC=C(C=O)C=C4)=C2'
TriI = 'O=CC1=CC(C=O)=C(O)C(C=O)=C1'
TriJ = 'O=CC(C=C1)=CC=C1N(C2=CC=C(C=O)C=C2)C3=CC=C(C=O)C=C3'
TriK = 'O=CC(C=C1)=CC=C1C2=NC(C3=CC=C(C=O)C=C3)=NC(C4=CC=C(C=O)C=C4)=N2'
TriL = 'O=CC(C=C1)=CC=C1C#CC2=CC(C#CC3=CC=C(C=O)C=C3)=CC(C#CC4=CC=C(C=O)C=C4)=C2'

TriM = 'O=CC1=CC(C2=CC(C3=CC=CC(C=O)=C3)=CC(C4=CC(C=O)=CC=C4)=C2)=CC=C1'
TriN = 'O=CC1=C(C2=CC(C3=C(C=O)C=CC=C3)=CC(C4=CC=CC=C4C=O)=C2)C=CC=C1'
TriO = 'O=CC1=CC(C2=CC(C3=CSC(C=O)=C3)=CC(C4=CSC(C=O)=C4)=C2)=CS1'
TriP = 'O=CC1=CC=C(C2=CC(C3=CC=C(C=O)O3)=CC(C4=CC=C(C=O)O4)=C2)O1'
TriQ = 'O=C/C=C/C1=CC=C(C2=CC(C3=CC=C(/C=C/C=O)C=C3)=CC(C4=CC=C(/C=C/C=O)C=C4)=C2)C=C1'
TriR = 'O=CC(C=C1)=CC=C1OCC2=CC(COC3=CC=C(C=O)C=C3)=CC(COC4=CC=C(C=O)C=C4)=C2'
TriS = 'O=CC1=CC=C(C=C1)C#CC2=CC(C=O)=CC(C=O)=C2'
TriT = 'O=CC1=C(O)C(C=O)=C(O)C(C=O)=C1O'
TriU = 'O=CC(C=C1)=CC=C1/C=C/C2=CC(/C=C/C3=CC=C(C=O)C=C3)=CC(/C=C/C4=CC=C(C=O)C=C4)=C2'

# Dialdehydes
Di1 = 'O=CC1=CC(C=O)=CC=C1'
Di2 = 'O=CC1=C(O)C(C=O)=CC(C(C)(C)C)=C1'
Di3 = 'O=CC1=CC2=C(C=C(C=O)S2)S1'
Di4 = 'O=CC1=CC=C(C=O)C=C1'
Di5 = 'O=CC1=C(F)C(F)=C(C=O)C(F)=C1F'
Di6 = 'O=CC1=CC=C(C2=CC=C(C=O)C=C2)C=C1'
Di7 = 'O=CC1=C2C(C=CC=C2)=C(C=O)C3=CC=CC=C31'
Di8 = 'O=CC1=NC2=C(C=CC3=C2N=C(C=O)C=C3)C=C1'

# Diamines
Di9 = 'NCCN'
Di10 = 'NCC(C)(C)CN'
Di11 = 'N[C@@H]1[C@@H](N)CN(CC2=CC=CC=C2)C1'
Di12 = 'N[C@H](C1=CC=CC=C1)[C@H](N)C2=CC=CC=C2'
Di13 = 'NC(C=C1)=CC=C1OC2=CC=C(N)C=C2'
Di14 = 'NC1=NON=C1N'
Di15 = 'N[C@H]1CCC[C@@H](N)C1'
Di16 = 'N[C@H]1[C@H](N)CCCC1'

Di25 = 'NCCCCCCNCCCCCCN'
Di26 = 'NCCCCCCN'
Di27 = 'NCC1=CC=C(CN)C=C1'
Di28 = 'NCC1CCC(CC1)CN'
Di29 = 'CN(CCCN)CCCN'
Di30 = 'NCCOCCN'
Di31 = 'NCC1=CC(CN)=CC=C1'
Di32 = 'NCC(O)CN'
Di33 = 'NCCCC[C@@H](C(O)=O)N'
Di34 = 'N[C@H]1CC[C@@H](CC1)N'

#Dialdehydes
Di17 = 'O=CC1=C(C=O)C=CS1'
Di18 = 'O=CC1=CC=CC=C1C=O'
Di19 = 'O=CC1=CC(C2=CC=C(C=O)C=C2)=NN1C'
Di20 = 'O=C/C(C)=C\C1=CC=C(/C=C(C)\C=O)C=C1'
Di21 = 'O=CC1=CC=C(OCCOC2=CC=C(C=O)C=C2OC)C(OC)=C1'
Di22 = 'O=CC1=C2C=CC=C(C=O)C2=NN1C'
Di23 = 'O=CC1=CC=C(OCCCOC2=CC=C(C=C2)C=O)C=C1'
Di24 = 'O=CC1=CC(OCC(CC)CCCC)=C(C=O)C=C1OC'

triamines = [TriA, TriB, TriC, TriD, TriE, TriF]
dialdehydes = [Di1, Di2, Di3, Di4, Di5, Di6, Di7, Di8, Di17, Di18, Di19, Di20, Di21, Di22, Di23, Di24]
trialdehydes = [TriG, TriH, TriI, TriJ, TriK, TriL, TriM, TriN, TriO, TriP, TriQ, TriR, TriS, TriT, TriU]
diamines = [Di9, Di10, Di11, Di12, Di13, Di14, Di15, Di16, Di25, Di26, Di27, Di28, Di29, Di30, Di31, Di32, Di33, Di34]

def get_smiles(bb: stk.BuildingBlock):
    key = standardize_smiles(rdkit.MolToSmiles(bb.to_rdkit_mol()))
    return key

class std_smiles(stk.MoleculeKeyMaker):
    """
    Used to get the standardized SMILES of BBs.
    Will be aromatic and include lower case letters. 
    """
    def get_smiles(bb: stk.BuildingBlock):
        key = standardize_smiles(rdkit.MolToSmiles(bb.to_rdkit_mol()))

    def __init__(self):
        """
        Initialize a :class:`.Smiles` instance.
        """
        super().__init__('SMILES', get_smiles)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return 'std_smiles()'

client = mongo_client()
precursors_triamines = stk.MoleculeMongoDb(
    mongo_client=client, database='cage_precursors', molecule_collection='Triamines', position_matrix_collection='triamines_postmat',
    jsonizer=stk.MoleculeJsonizer(
        key_makers = (stk.InchiKey(), std_smiles())), indices=('SMILES')
)
precursors_diamines = stk.MoleculeMongoDb(
    mongo_client=client, database='cage_precursors', molecule_collection='Diamines', position_matrix_collection='diamines_postmat',
    jsonizer=stk.MoleculeJsonizer(
        key_makers = (stk.InchiKey(), std_smiles())), indices=('SMILES')
)
precursors_trialdehydes = stk.MoleculeMongoDb(
    mongo_client=client, database='cage_precursors', molecule_collection='Trialdehydes', position_matrix_collection='trialdehydes_postmat',
    jsonizer=stk.MoleculeJsonizer(
        key_makers = (stk.InchiKey(), std_smiles())), indices=('SMILES')
)
precursors_dialdehydes = stk.MoleculeMongoDb(
    mongo_client=client, database='cage_precursors', molecule_collection='Dialdehydes', position_matrix_collection='dialdehydes_postmat',
    jsonizer=stk.MoleculeJsonizer(
        key_makers = (stk.InchiKey(), std_smiles())), indices=('SMILES')
)



# Create precursor building block and optimise using quick conformer search
# Make an rdkit molecule then a stk building block again
# Store in collection of functionality within same precursor molecule mongodb 

Triam = []
for precursor in triamines:
    #check why this is needed line 159
    x = rdkit.MolToSmiles(quick_conf_search(precursor), kekuleSmiles=True)
    BB = stk.BuildingBlock(x, [stk.PrimaryAminoFactory()])
    Triam.append(BB)
for i in Triam:
    precursors_triamines.put(i)

Diam = []
for precursor in diamines:
    x = rdkit.MolToSmiles(quick_conf_search(precursor), kekuleSmiles=True)
    BB = stk.BuildingBlock(x, [stk.PrimaryAminoFactory()])
    Diam.append(BB)
for i in Diam:
    precursors_diamines.put(i)

Trial = []
for precursor in trialdehydes:
    x = rdkit.MolToSmiles(quick_conf_search(precursor), kekuleSmiles=True)
    BB = stk.BuildingBlock(x, [stk.AldehydeFactory()])
    Trial.append(BB)
for i in Trial:
    precursors_trialdehydes.put(i)

Dial = []
for precursor in dialdehydes:
    x = rdkit.MolToSmiles(quick_conf_search(precursor), kekuleSmiles=True)
    BB = stk.BuildingBlock(x, [stk.AldehydeFactory()])
    Dial.append(BB) 
for i in Dial:
    precursors_dialdehydes.put(i)
