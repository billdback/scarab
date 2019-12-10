"""
Copyright (C) 2019 William D. Back

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This module is a generator of simulations from YAML.
"""
import argparse
import os

from scarab.io import SimulationYAMLReader, SimulationWriter
from scarab.util import eprint


def main():
    """
    Read a YAML file and write the simulation.
    """
    args = get_args()
    print(args)

    if valid(args):
        sim_repr = SimulationYAMLReader().read_yaml_from_file(args.yaml_file)
        issues = sim_repr.check_for_issues()
        if issues:
            for issue in issues:
                print(issue)
        SimulationWriter().write_simulation_module(simulation_repr=sim_repr, filename=args.sim_file)


def get_args():
    """
    Returns command line arguments.
    :return: The command line arguments for the simulation run.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(description="Generates Scarab simulation files from YAML.")

    parser.add_argument("--yaml_file", type=str, help="path to the YAML file")
    parser.add_argument("--sim_file", type=str, help="optional path to the output file")
    parser.add_argument("--overwrite", type=str, action="store_true", help="overwrites previous sim files if set")

    return parser.parse_args()


def valid(args):
    """
    Checks the args for validity.
    :param args: The arguments to validate.
    :type args: argparse.Namespace
    :returns: True if valid.
    :rtype: bool
    """
    is_valid = True

    if not os.path.exists(args.yaml_file):
        eprint(f"YAML file {args.yaml_file} doesn't exist.")
        is_valid = False
    if args.sim_file and not args.overwrite and os.path.exists(args.sim_file):
        eprint(f"Simulation file {args.yaml_file} exist and overwrite is not specified.")
        is_valid = False

    return is_valid


if __name__ == "__main__":
    main()
