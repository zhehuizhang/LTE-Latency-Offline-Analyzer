#!/bin/bash
#inputs  1 output name, 2 PF file name, 3 MLWDF file name, 4 EXP/PF file name, 5 Title, 6 x label, 7 Y label

# echo "set terminal svg size 600,400 dynamic enhanced fname 'arial'  fsize 11 butt solid" >> plot.gnu
# echo "set terminal svg size 600,400" >> plot.gnu
# echo "set output 'bitmap2.svg'" >> plot.gnu

echo 'target file '$1

awk 'BEGIN{n=1}{if ($2=="PDCP" && $4==3 && $5=="UL") {print n,$11; n+=1}}' $1 | head -1000 > .temp_pdcp_ul.dat
awk 'BEGIN{n=1}{if ($2=="PDCP" && $4==3 && $5=="DL") {print n,$11; n+=1}}' $1 | head -1000 > .temp_pdcp_dl.dat
awk 'BEGIN{n=1}{if ($2=="PHY" && $3=="UL") {print n,$9; n+=1}}' $1 | head -1000 > .temp_phy_ul.dat
awk 'BEGIN{n=1}{if ($2=="PHY" && $3=="DL") {print n,$9; n+=1}}' $1 | head -1000 > .temp_phy_dl.dat

echo 'generating files'
filename=.temp.plot1
echo "set title \"$1\"" >> $filename
echo "set terminal jpeg size 1024,768;" > $filename
echo "set output '$1_pdcp_ul.jpg';">> $filename
echo "set style  data linespoints" >> $filename
echo "set xlabel \"Sample #\"" >> $filename
echo "set ylabel \"Value\"" >> $filename
echo "plot  '.temp_pdcp_ul.dat' using 2:xtic(1) title 'Throughput UL'" >>$filename
gnuplot $filename
rm -Rf $filename

filename=.temp.plot2
echo "set title \"$1\"" >> $filename
echo "set terminal jpeg size 1024,768;" > $filename
echo "set output '$1_pdcp_dl.jpg';">> $filename
echo "set style  data linespoints" >> $filename
echo "set xlabel \"Sample #\"" >> $filename
echo "set ylabel \"Value\"" >> $filename
echo "plot  '.temp_pdcp_dl.dat' using 2:xtic(1) title 'Throughput DL'" >>$filename
gnuplot $filename
rm -Rf $filename

filename=.temp.plot3
echo "set title \"$1\"" >> $filename
echo "set terminal jpeg size 1024,768;" > $filename
echo "set output '$1_bler.jpg';">> $filename
echo "set style  data linespoints" >> $filename
echo "set xlabel \"Sample #\"" >> $filename
echo "set ylabel \"Value\"" >> $filename
echo "plot  '.temp_phy_ul.dat' using 2:xtic(1) title 'BLER UL', '.temp_phy_dl.dat' using 2:xtic(1) title 'BLER DL' " >>$filename
gnuplot $filename
rm -Rf $filename

base=$(basename $1)
mkdir tmp/$base
cp .temp* 'tmp/'$base'/'

# echo "set style histogram cluster gap 1" >> $filename
# echo "set xtics border in scale 1,0.5 nomirror rotate by -90  offset character 0, 0, 0" >> $filename
# echo "set xtics ($labelxtic)" >> $filename
# echo "set grid" >> $filename
# echo "set boxwidth 0.5 absolute" >> $filename
# echo "set style fill solid 1.0 noborder" >> $filename
# echo "set key inside right" >> $filename
# echo "set xlabel \"Sample #\"" >> $filename
# echo "set ylabel \"Value\"" >> $filename
  
#echo  "set format y \"%.0t*10^%+03T\"" >> $filename #Pour le PLR

#echo "set yrange [ *:* ] noreverse nowriteback" >> $filename
#echo "set xrange [ *:* ] noreverse nowriteback" >> $filename
#echo "plot  '$2' using 2:xtic(1) title 'PF', '$3' using 2:xtic(1) title 'MLWDF', '$4' using 2:xtic(1) title 'EXP/PF'" >>$filename


