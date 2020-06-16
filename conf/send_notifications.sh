#!/bin/bash
# Sends email notifications to users who are subscribed to dataset
# update notifications (and the user is following a given dataset).
# use the curl command instead of paster, which does not work on the server.
# https://github.com/genkimaps/gis-hub/issues/49
#
# Must have an environment var GISHUB_API with a sysadmin API key.
# This environment var is defined in /etc/environment, which should be picked up
# the user cron.
#
# More on the CKAN email notifications API:
# https://docs.ckan.org/en/ckan-2.7.3/maintaining/email-notifications.html

curl https://www.gis-hub.ca/api/action/send_email_notifications -H "Authorization:$GISHUB_API" -d '{}'
