#!/bin/bash
# Queries the ckan database and extracts/transforms data to get the number of days since metadata has been modified. Exports csv file to /tmp

psql -U postgres -d ckan -f maintainer_email.sql
