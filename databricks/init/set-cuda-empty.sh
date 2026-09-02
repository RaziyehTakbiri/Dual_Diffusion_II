#!/bin/bash
set -euo pipefail

printf '%s\n' "export CUDA_VISIBLE_DEVICES=''" \
  >> /databricks/spark/conf/spark-env.sh
