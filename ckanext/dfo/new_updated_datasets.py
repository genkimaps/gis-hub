import hub-geo-api.ckanapi as ck
import json

test = ck.get_dataset('seamounts')

with open ('/tmp/seamounts.json', 'w') as out_file:
    json.dump(test, out_file)