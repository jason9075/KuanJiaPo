#!/bin/bash

xvfb-run -s "-screen 0 1024x768x24" node puppeteer-client.js
