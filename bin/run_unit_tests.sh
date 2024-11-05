#!/bin/bash

for dir in $(find . -type d -name "tests"); do
    echo "Running tests in directory: $dir"
    pytest $dir
done
