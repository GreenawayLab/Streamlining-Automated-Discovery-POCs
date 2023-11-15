from types import prepare_class
import stk
from rdkit.Chem.MolStandardize import standardize_smiles
from rdkit.Chem import AllChem as rdkit
import numpy as np
from stk.databases.mongo_db.molecule import MoleculeMongoDb
from tqdm import tqdm
import argparse
import logging
import itertools as it
import pymongo
from functools import partial
from pathlib import Path
from uuid import uuid4
from pathos.multiprocessing import ProcessingPool as Pool
import stko
import json

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

db_url = 'mongodb://path_to_mongo:27017/' # change this to your own path to mongo

def get_client(db_url):
    return pymongo.MongoClient(db_url)
if "rds" in str(Path.cwd()):
    macromodel_path = 'PATH/schrodinger2021-2'
else:
    macromodel_path = 'PATH/schrodinger2021-3'
print(macromodel_path)

def get_db(db_url, collection_name):
    standardize_smiles_km = stk.MoleculeKeyMaker(
        key_name="cage_key", get_key=get_cage_key,
    )
    jsonizer = stk.ConstructedMoleculeJsonizer(
        key_makers=(standardize_smiles_km,)
    )
    client = get_client(db_url)
    db = stk.ConstructedMoleculeMongoDb(
        client,
        constructed_molecule_collection=f"{collection_name}_constructed_molecules",
        position_matrix_collection=f"{collection_name}_position_matrices",
        building_block_position_matrix_collection=f"{collection_name}_building_block_position_matrices",
        database="cage_opt_100ns",
        molecule_collection=collection_name,
        jsonizer=jsonizer,
    )
    return db
    print('made db')

def get_precursors(db_url, collection_name):
    client = get_client(db_url)
    db = stk.MoleculeMongoDb(
        client,
        database="cage_precursors",
        molecule_collection=collection_name,
        position_matrix_collection=f"{collection_name.lower()}_postmat",
    )
    for entry in get_client(db_url)["cage_precursors"][
        collection_name
    ].find():
        smiles = entry["SMILES"]
        mol = db.get({"SMILES": smiles})
        print(mol)
        assert mol is not None
        yield mol
    #raise Exception
    print('got precursors')


def get_cage(precursors, topology):
    """
    Returns a cage from an iterable of precursors.

    Parameters
    ----------
    precursors : iterable of [stk.BuildingBlock, stk.BuildingBlock]
        The precursors to use to construct the cage.

    topology : stk.cage.Topology
        The topology of the cage.

    Returns
    ------
    cage : stk.ConstructedMolecule
        The constructed cage.
    """
    return stk.ConstructedMolecule(
        topology_graph=topology(building_blocks=precursors)
    )
    print('forming cage topology')


def main(args):
    # Load optimised precursors
    triamines = [
        stk.BuildingBlock.init_from_molecule(
            mol, functional_groups=[stk.PrimaryAminoFactory()]
        )
        for mol in get_precursors(db_url=args.db, collection_name="Triamines")
    ]
    diamines = [
        stk.BuildingBlock.init_from_molecule(
            mol, functional_groups=[stk.PrimaryAminoFactory()]
        )
        for mol in get_precursors(db_url=args.db, collection_name="Diamines")
    ]
    trialdehydes = [
        stk.BuildingBlock.init_from_molecule(
            mol, functional_groups=[stk.AldehydeFactory()]
        )
        for mol in get_precursors(db_url=args.db, collection_name="Trialdehydes")
    ]
    dialdehydes = [
        stk.BuildingBlock.init_from_molecule(
            mol, functional_groups=[stk.AldehydeFactory()]
        )
        for mol in get_precursors(db_url=args.db, collection_name="Dialdehydes")
    ]
    topologies = {
        "2+3": stk.cage.TwoPlusThree,
        "4+6": stk.cage.FourPlusSix,
        "6+9": stk.cage.SixPlusNine,
        "8+12": stk.cage.EightPlusTwelve,
    }
    # Check molecules are Kekulized
    for mol in it.chain(triamines, dialdehydes):
        for bond in mol.to_rdkit_mol().GetBonds():
            # Double check for any non-Kekulized bonds
            assert bond.GetBondTypeAsDouble() != 1.5

    # Check molecules are Kekulized
    for mol in it.chain(diamines, trialdehydes):
        for bond in mol.to_rdkit_mol().GetBonds():
            # Double check for any non-Kekulized bonds
            assert bond.GetBondTypeAsDouble() != 1.5
    
    print('checking kekulization')
    print(len(diamines))
    print(len(dialdehydes))
    print(len(triamines))
    print(len(trialdehydes))

    it1 = it.product(diamines, trialdehydes, topologies.values())
    it2 = it.product(dialdehydes, triamines, topologies.values())
    total_combs = (len(diamines) * len(trialdehydes) * len(topologies))+(len(triamines) * len(dialdehydes) * len(topologies))
    #print(total_combs)
    combinations = list(it.chain(it1, it2))
    print(len(combinations))
    # Generate a unique identifier for each run
    identifiers = [uuid4().int for _ in range(total_combs)]
    run_name = uuid4().int

    with Pool(processes=args.p) as pool:
        print(args.p)
        for res in tqdm(
            pool.uimap(
                partial(cage_opt, db_url=args.db, topologies=topologies,),
                combinations,
                identifiers,
            ),
            total=total_combs,
            desc="Optimising cages",
        ):
            if res is not None:
                cage, collection_name, identifier, topology_str = res
                write_cage(
                    mol=cage,
                    db_url=args.db,
                    collection_name=collection_name,
                    identifier=identifier,
                    run_name=run_name,
                    topology_str=topology_str,
                )
                logging.info(f"Writing {cage}")
                print('res not none so opt cages not in db')
            else:
                print('cage in db optimised')
    pool.close()

def cage_opt(combination, identifier, db_url, topologies):
    p1, p2, topology = combination
    cage = get_cage([p1, p2], topology)
    topology_str = list(topologies.keys())[
        list(topologies.values()).index(topology)
    ]
    opt = stko.OptimizerSequence(
        stko.MacroModelForceField(
            output_dir=f"{identifier}_FF_Restricted",
            macromodel_path=macromodel_path,
            force_field=16,
            restricted=True,
        ),
        stko.MacroModelForceField(
            output_dir=f"{identifier}_FF_Unrestricted",
            macromodel_path=macromodel_path,
            force_field=16,
            restricted=False,
        ),
        stko.MacroModelMD(
            output_dir=f"{identifier}_MD",
            macromodel_path=macromodel_path,
            temperature=700,
            conformers=50,
            simulation_time=100000,
            time_step=1,
            eq_time=100,
        ),
    )
    print('done the MD opt')
    # For debugging
    collection_name = f"{topology_str}"
    # Check if cage already in database
    if cage_in_db(cage, db_url=db_url, collection_name=collection_name,):
        return
    cage.write(f"{identifier}_Unopt.mol")
    try:
        cage = opt.optimize(cage)
    except Exception as e:
        logging.error(f"{e}")
        logging.error(f"Cage {cage} with identifier {identifier} failed.")
        return None
    cage.write(f"{identifier}_Opt.mol")
    return cage, collection_name, identifier, topology_str


def cage_in_db(mol, db_url, collection_name):
    db = get_db(db_url=db_url, collection_name=collection_name)
    try:
        db.get({"cage_key": get_cage_key(mol)})
        return True
    except:
        return False
        print('cage key search')

def get_cage_key(mol):
    """
    Returns a unique key for an `stk.ConstructedMolecule`, or an `stk.BuildingBlock`.
    """
    if isinstance(mol, stk.ConstructedMolecule):
        key = ""
        for bb in mol.get_building_blocks():
            key += standardize_smiles(rdkit.MolToSmiles(bb.to_rdkit_mol()))
            if "," not in key:
                key += ","
    elif isinstance(mol, stk.BuildingBlock):
        key = standardize_smiles(rdkit.MolToSmiles(mol.to_rdkit_mol()))
    else:
        raise TypeError(
            "Molecule must be an stk.BuildingBlock or an stk.ConstructedMolecule"
        )
    return key
    print('help the key')

def write_cage(
    mol, db_url, collection_name, identifier, run_name, topology_str
):
    db = get_db(db_url=db_url, collection_name=collection_name)
    db.put(mol)
    # Update run JSON file
    if Path(f"Run_{run_name}.json").exists():
        with open(f"Run_{run_name}.json", "r") as f:
            data = json.load(f)
    else:
        data = {}
    data.update({get_cage_key(mol): identifier})
    data[f"{get_cage_key(mol)}_{topology_str}"] = identifier
    with open(f"Run_{run_name}.json", "w") as f:
        json.dump(data, f)
    print('writing cage to db')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Precursor optimisation script."
    )
    parser.add_argument("-db", help="Contains URL for MongoDB.", required=True)
    parser.add_argument(
        "-p", help="Number of CPU cores to use.", required=True, type=int,
    )
    args = parser.parse_args()
    main(args)
