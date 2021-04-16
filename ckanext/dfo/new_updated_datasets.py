# Use sys.append since hub-geo-api not set up as a module.
# https://stackoverflow.com/questions/22955684/how-to-import-py-file-from-another-directory
import sys
sys.path.append('/home/dfo/hub-geo-api/ckanapi.py')
import ckanapi as ck

test = ck.get_dataset('seamounts')

with open('/tmp/seamounts.json', 'w') as out_file:
    json.dump(test, out_file)