#!/usr/bin/bash

uwsgi -s localhost:5555 --manage-script-name --mount /=gallery.ui.app:app
