# Use sys.append since hub-geo-api not set up as a module.
# https://stackoverflow.com/questions/22955684/how-to-import-py-file-from-another-directory
import sys
import json
sys.path.append('/home/dfo/hub-geo-api')
import ckanapi as ck
import settings

logger = settings.setup_logger()


def process(group_name):
    datasets_group = ck.package_search(group_name)
    return datasets_group


def main():
    # CLI arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("group_id", type=str, help="Group name or ID to query and retrieve datasets.")
    args = parser.parse_args()

    group_datasets = process(args.group_id)


if __name__ == "__main__":
    main()