#!/bin/bash
set -e
set -x

python3 -c 'from jumpscale import j;print(j.application.getMemoryUsage())'
