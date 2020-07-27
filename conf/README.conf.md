# About the conf folder

This folder is for the nginx conf file, and potentially other conf files, which are part of CKAN.  However, they are vital to the production CKAN as a whole, and if possible (if the conf file does not contain passwords or API keys) should be included here. 

We added a script to run email notifications. Runs weekly on Sundays.

We added a shell script to run backups of datastore and ckan databases. Script deletes previous backups from /tmp and exports backups with date in SQL format to /tmp. Runs every Friday at midnight.

We added 2 shell scripts to extract data maintainers information from the CKAN database and then email them if data has not been modified in 365 days or more. Scripts will run on 1st day of each month. 
