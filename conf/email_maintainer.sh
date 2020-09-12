#!/bin/bash
# Activates the virtual environment and executes the python script to email data maintainers referencing the csv file 'maintainer_details.csv' in /tmp

cd /home/tk/ckanext-dfo/ckanext/dfo && /home/tk/venv/bin/python /home/tk/ckanext-dfo/ckanext/dfo/dfo_data_maintainer.py
