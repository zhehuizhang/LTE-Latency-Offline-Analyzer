#!/bin/bash
# Usage: ./plot_figure.sh [dir]
for i in output_pdcp/*.csv; do
# for i in output/*.txt; do
	echo $i
	./plot_general.sh $i 3 11 
        echo 'ploting'
done
