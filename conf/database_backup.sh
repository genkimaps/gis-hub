#!/bin/bash
#
# Delete previous backup if any exist from /tmp directory.
# Delete looks for files in /tmp containing the string ckan.202 or datastore.202.
# Make a backup of ckan and datastore_default postgres databases. 
# Use pg_dump utility to backup a PostgreSQL database into a script file in SQL format.
# Export to /tmp where data can be stored temporarily before being copied to an external storage device.
#
# More on pg_dump utility and CKAN database management:
# https://docs.ckan.org/en/ckan-2.7.3/maintaining/database-management.html
# https://postgresql.org/docs/12/app-pg_dump.html

## Get current date ##
_now=$(date +"%Y%m%d")

## Appending a current date from a $_now to a filename stored in $_ckanfile ##
_ckanfile="/tmp/ckan.$_now.dump"

## Appending a current date from a $_now to a filename stored in $_datastorefile ##
_datastorefile="/tmp/datastore.$_now.dump"

rm /tmp/**ckan.202**
rm /tmp/**datastore.202**

sudo -u postgres pg_dump ckan > "$_ckanfile"
sudo -u postgres pg_dump datastore_default > "$_datastorefile"
