from opentrons.simulate import simulate, format_runlog
import argparse


def run_simulation(path):
    protocol_file = open(path)
    runlog, _bundle = simulate(protocol_file)
    # print(format_runlog(runlog))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Simulate an Opentrons experiment."
    )
    parser.add_argument("-i", help="Path to the Opentron simulation script.")
    args = parser.parse_args()
    run_simulation(args.i)
