#!/bin/bash

        for i in $( ls -d ../../*_*); do
#        	python getRetrxDelay.py $i > $i"_retrx.txt"
		echo $i
		python offline_example.py $i | grep 'KPI' > output/${i:6}"_stats.txt"
		python offline_example.py $i | grep 'RECORD' > output_pdcp/${i:6}"_pdcp.txt"
		# python getRRCpara.py $i > $i"_rrcpara.txt"

        done

#	for i in $( find /mnt/hgfs/VRlog/ -wholename '*exp56_*.qmdl'); do
#		echo $i
#		python lte-delay-dl.py $i > $i"_dldelay.txt"	
#		python getSrDelay.py $i > $i"_sr.txt"
#		python getRRCpara.py 
#	done
