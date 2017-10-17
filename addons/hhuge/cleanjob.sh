#!/bin/bash

if [ "x$JOB_ID" != "x" ]; then
  if [ "x$SGE_TASK_ID" == "xundefined" ]; then
    SGE_TASK_ID=1
  fi
  rm -rf /scratch/$JOB_ID.$SGE_TASK_ID
  echo "Cleaned job $JOB_ID.$SGE_TASK_ID"
else
  echo "Error: No JOB_ID variable set"
fi
