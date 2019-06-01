#!/bin/bash
for i in output_pdcp/*_pdcp.txt; do
	echo $i
	filename=$i'.csv'
	argv="getPdcpRtt.py $i"
	python $argv > $filename
	awk -F',' 'BEGIN{sum=0}{sum+=$11}END{print sum/NR}' $filename
	awk -F',' 'BEGIN{max=0}{if ($11>max) max=$11}END{print max}' $filename
	awk -F',' 'BEGIN{min=1000}{if ($11<min) min=$11}END{print min}' $filename

done
