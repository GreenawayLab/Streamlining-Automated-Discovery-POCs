from ast import Pass
#from types import NoneType
import stk
import pymongo
from rdkit.Chem.MolStandardize import standardize_smiles
import pandas as pd
import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem as rdkit
from rdkit.Chem import PyMol as rdkit
import rdkit.Chem.AllChem as rdkit
from rdkit.Chem.PyMol import MolViewer as v
import itertools as it
import json
import pywindow as pw
from os import system
from pywindow import MolecularSystem
from pymongo import MongoClient
import xmlrpc.client as cmd
import xmlrpc.server
import os
import csv
import numpy as np
import pandas as pd
import logging


import warnings
warnings.filterwarnings('ignore')

def mongo_client(url):
    return MongoClient(
        'mongodb://path_to_mongo:27017/'
    )

db_url = 'mongodb://path_to_mongo:27017/'

def unqiue_cage_key(mol):
    k = ""
    if isinstance(mol, stk.ConstructedMolecule):
        for bb in mol.get_building_blocks():
            k+=standardize_smiles(rdkit.MolToSmiles(bb.to_rdkit_mol()))
            k+=','
        k = k[:-1]
        return k
    elif isinstance(mol, stk.BuildingBlock):
        return standardize_smiles(rdkit.MolToSmiles(mol.to_rdkit_mol()))
    
    
cage_key = stk.MoleculeKeyMaker(key_name='cage_key', get_key=unqiue_cage_key)

db23_10ns = stk.ConstructedMoleculeMongoDb(
    mongo_client=mongo_client(db_url), 
    database='cage_opt_100ns', 
    molecule_collection='2+3', 
    position_matrix_collection='2+3_position_matrices', 
    building_block_position_matrix_collection= '2+3_building_block_position_matrices',
    constructed_molecule_collection='2+3_constructed_molecules',
    jsonizer=stk.ConstructedMoleculeJsonizer(key_makers = [cage_key]),
)

db46_10ns = stk.ConstructedMoleculeMongoDb(
    mongo_client=mongo_client(db_url), 
    database='cage_opt_100ns',
    molecule_collection='4+6', 
    position_matrix_collection='4+6_position_matrices', 
    building_block_position_matrix_collection= '4+6_building_block_position_matrices',
    constructed_molecule_collection='4+6_constructed_molecules',
    jsonizer=stk.ConstructedMoleculeJsonizer(key_makers = [cage_key]),
)

db69_10ns = stk.ConstructedMoleculeMongoDb(
    mongo_client=mongo_client(db_url), 
    database='cage_opt_100ns',
    molecule_collection='6+9', 
    position_matrix_collection='6+9_position_matrices', 
    building_block_position_matrix_collection= '6+9_building_block_position_matrices',
    constructed_molecule_collection='6+9_constructed_molecules',
    jsonizer=stk.ConstructedMoleculeJsonizer(key_makers = [cage_key]),
)

db812_10ns = stk.ConstructedMoleculeMongoDb(
    mongo_client=mongo_client(db_url), 
    database='cage_opt_100ns',
    molecule_collection='8+12', 
    position_matrix_collection='8+12_position_matrices',
    building_block_position_matrix_collection= '8+12_building_block_position_matrices',
    constructed_molecule_collection='8+12_constructed_molecules',
    jsonizer=stk.ConstructedMoleculeJsonizer(key_makers = [cage_key]),
)

def get_cages(smiles_code):
    smiles_code_l = [smiles_code]
    molecules_test = []
    for i in smiles_code_l:
        try:
            a = db23_10ns.get({'cage_key': i})
            molecules_test.append(a)
        except KeyError:
            a = None
        try:
            b = db46_10ns.get({'cage_key': i})
            molecules_test = molecules_test+[b]
        except KeyError:
            b = None
        try:
            c = db69_10ns.get({'cage_key': i})
            molecules_test = molecules_test+[c]
        except KeyError:
            c = None 
        try:
            d = db812_10ns.get({'cage_key': i})
            molecules_test = molecules_test+[d]
        except KeyError:
            d = None
    cage_topology = {'smiles': (smiles_code),
                    '2+3': (
                        a
                        ),
                    '4+6': (
                        b
                        ),
                    '6+9': (
                        c
                        ),
                    '8+12': (
                        d
                        )
                    }
    
    return cage_topology

def pw_function(smiles_code, calc_dir, topology):
    cage_dict = get_cages(smiles_code)
    name = cage_dict['smiles']
    molecule = cage_dict[topology]
    results = {}

    xyz_file = os.path.join(f'{name}_{topology}.xyz')
    json_file = os.path.join(f'{name}_{topology}.json')
    pdb_file = os.path.join(f'{name}_{topology}.pdb')

    if molecule == None:
        results = {
                'topology': topology,
                'molecular_weight': 0,
                'pore_diameter_opt':0,
                'pore_volume_opt':0,
                'windows':(),
                'windows':(),
            }
    elif molecule != None:
        pass

    # Read in host from xyz file.
    molecule.write(xyz_file)
    if os.path.exists(json_file):
        logging.info(f'loading {json_file}')
        with open(json_file, 'r') as f:
            results = json.load(f)
    else:
        logging.info(f'running pywindow on {name}:')
        molsys = pw.MolecularSystem.load_file(xyz_file)
        mol = molsys.system_to_molecule()
        mol_mass = mol.molecular_weight()
        try:
            mol.calculate_pore_diameter_opt()
            mol.calculate_pore_volume_opt()
            mol.calculate_windows()
            mol.calculate_centre_of_mass()
            results = {
                'topology': topology,
                'molecular_weight': mol_mass,
                'pore_diameter_opt': (
                    mol.properties['pore_diameter_opt']['diameter']
                ),
                'pore_volume_opt': (
                    mol.properties['pore_volume_opt']
                ),
                'windows': tuple(
                    i for i in mol.properties['windows']['diameters']
                ),
            }
            win_list = list(results['windows'])
            for i in win_list:
                if i >= 1000 or i == 0:
                    win_list.remove(i)
                results = {
                    'topology': topology,
                    'molecular_weight': mol_mass,
                    'pore_diameter_opt': (
                        mol.properties['pore_diameter_opt']['diameter']
                ),
                    'pore_volume_opt': (
                        mol.properties['pore_volume_opt']
                ),
                    'windows': tuple(
                    win_list
                ),
            }                    
            mol.dump_molecule(
                pdb_file,
                include_coms=True,
                override=True,
            )
        except Exception:
            results = {
                'topology': topology,
                'molecular_weight': mol_mass,
                'pore_diameter_opt': 0,
                'pore_volume_opt':0,
                'windows':(),
                'windows':(),
            }

    return results
def full_cage_analysis(smiles_code, calc_dir):
    ""  
    "conduct get_pw_result for all topologies and return a dictionary of the results."
    cage_dict = get_cages(smiles_code)
    name = cage_dict['smiles']
    
    results23 = pw_function(smiles_code, calc_dir, '2+3')
    results46 = pw_function(smiles_code, calc_dir, '4+6')
    results69 = pw_function(smiles_code, calc_dir, '6+9')
    results812 = pw_function(smiles_code, calc_dir, '8+12')

    cage_full_analysis = {'cage': name,
                            '2+3': results23,
                            '4+6': results46,
                            '6+9': results69,
                            '8+12': results812
                         }

    with open(f'{name}.json', 'w') as f:
        json.dump(cage_full_analysis, f, indent=4)

    return cage_full_analysis
    




P1 = ["Nc1nc(N)nc(N)n1,O=Cc1cccc(C=O)c1",
      "Nc1nc(N)nc(N)n1,CC(C)(C)c1cc(C=O)c(O)c(C=O)c1",
      "Nc1nc(N)nc(N)n1,O=Cc1cc2sc(C=O)cc2s1",
      "Nc1nc(N)nc(N)n1,O=Cc1ccc(C=O)cc1",
      "Nc1nc(N)nc(N)n1,O=Cc1c(F)c(F)c(C=O)c(F)c1F",
      "Nc1nc(N)nc(N)n1,O=Cc1ccc(-c2ccc(C=O)cc2)cc1",
      "Nc1nc(N)nc(N)n1,O=Cc1c2ccccc2c(C=O)c2ccccc12",
      "Nc1nc(N)nc(N)n1,O=Cc1ccc2ccc3ccc(C=O)nc3c2n1", 
      "Cc1c(CN)c(C)c(CN)c(C)c1CN,O=Cc1cccc(C=O)c1",
      "Cc1c(CN)c(C)c(CN)c(C)c1CN,CC(C)(C)c1cc(C=O)c(O)c(C=O)c1",
      "Cc1c(CN)c(C)c(CN)c(C)c1CN,O=Cc1cc2sc(C=O)cc2s1",
      "Cc1c(CN)c(C)c(CN)c(C)c1CN,O=Cc1ccc(C=O)cc1",
      "Cc1c(CN)c(C)c(CN)c(C)c1CN,O=Cc1ccc2ccc3ccc(C=O)nc3c2n1",
      "Cc1c(CN)c(C)c(CN)c(C)c1CN,O=Cc1c(F)c(F)c(C=O)c(F)c1F",
      "Cc1c(CN)c(C)c(CN)c(C)c1CN,O=Cc1ccc(-c2ccc(C=O)cc2)cc1",
      "Cc1c(CN)c(C)c(CN)c(C)c1CN,O=Cc1c2ccccc2c(C=O)c2ccccc12",
      "NCCN(CCN)CCN,O=Cc1cccc(C=O)c1",
      "NCCN(CCN)CCN,CC(C)(C)c1cc(C=O)c(O)c(C=O)c1",
      "NCCN(CCN)CCN,O=Cc1cc2sc(C=O)cc2s1",
      "NCCN(CCN)CCN,O=Cc1ccc(C=O)cc1",
      "NCCN(CCN)CCN,O=Cc1ccc2ccc3ccc(C=O)nc3c2n1",
      "NCCN(CCN)CCN,O=Cc1c(F)c(F)c(C=O)c(F)c1F",
      "NCCN(CCN)CCN,O=Cc1ccc(-c2ccc(C=O)cc2)cc1",
      "NCCN(CCN)CCN,O=Cc1c2ccccc2c(C=O)c2ccccc12",
      "CCc1c(CN)c(CC)c(CN)c(CC)c1CN,O=Cc1cccc(C=O)c1",
      "CCc1c(CN)c(CC)c(CN)c(CC)c1CN,CC(C)(C)c1cc(C=O)c(O)c(C=O)c1",
      "CCc1c(CN)c(CC)c(CN)c(CC)c1CN,O=Cc1cc2sc(C=O)cc2s1",
      "CCc1c(CN)c(CC)c(CN)c(CC)c1CN,O=Cc1ccc(C=O)cc1",
      "CCc1c(CN)c(CC)c(CN)c(CC)c1CN,O=Cc1ccc2ccc3ccc(C=O)nc3c2n1",
      "CCc1c(CN)c(CC)c(CN)c(CC)c1CN,O=Cc1c(F)c(F)c(C=O)c(F)c1F",
      "CCc1c(CN)c(CC)c(CN)c(CC)c1CN,O=Cc1ccc(-c2ccc(C=O)cc2)cc1",
      "CCc1c(CN)c(CC)c(CN)c(CC)c1CN,O=Cc1c2ccccc2c(C=O)c2ccccc12",
      "NCCCN(CCCN)CCCN,O=Cc1cccc(C=O)c1",
      "NCCCN(CCCN)CCCN,CC(C)(C)c1cc(C=O)c(O)c(C=O)c1",
      "NCCCN(CCCN)CCCN,O=Cc1cc2sc(C=O)cc2s1",
      "NCCCN(CCCN)CCCN,O=Cc1ccc(C=O)cc1",
      "NCCCN(CCCN)CCCN,O=Cc1ccc2ccc3ccc(C=O)nc3c2n1",
      "NCCCN(CCCN)CCCN,O=Cc1c(F)c(F)c(C=O)c(F)c1F",
      "NCCCN(CCCN)CCCN,O=Cc1ccc(-c2ccc(C=O)cc2)cc1",
      "NCCCN(CCCN)CCCN,O=Cc1c2ccccc2c(C=O)c2ccccc12",
      "NC1CC(N)CC(N)C1,O=Cc1cccc(C=O)c1",
      "NC1CC(N)CC(N)C1,CC(C)(C)c1cc(C=O)c(O)c(C=O)c1",
      "NC1CC(N)CC(N)C1,O=Cc1cc2sc(C=O)cc2s1",
      "NC1CC(N)CC(N)C1,O=Cc1ccc(C=O)cc1",
      "NC1CC(N)CC(N)C1,O=Cc1ccc2ccc3ccc(C=O)nc3c2n1",
      "NC1CC(N)CC(N)C1,O=Cc1c(F)c(F)c(C=O)c(F)c1F",
      "NC1CC(N)CC(N)C1,O=Cc1ccc(-c2ccc(C=O)cc2)cc1",
      "NC1CC(N)CC(N)C1,O=Cc1c2ccccc2c(C=O)c2ccccc12"
     ]

P1_dict = []
for i in P1:
    x = full_cage_analysis(i, '/path_to_calc_dir/')
    P1_dict = P1_dict+[x]

df = pd.DataFrame(data=P1_dict)
df.to_csv('P1_pw_100ns.csv',index=False)
