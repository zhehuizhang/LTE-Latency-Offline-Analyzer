
"""
This script will calculate pdcp layer end-to-ed delay.
Usage: python getPdcpRtt.py [dir name] # Default dir name is current dir.
Output: ul_size, ul_fn_sfn, ul_timestamp, dl_size, dl_fn_sfn, dl_timestamp, first_dl_fn_sfn, dl_trans_delay, e2e_delay
Sample:
RECORD PDCP DL 3 119229453.521 39 3 2740 61 2019-05-26 05:17:33.520914
RECORD PDCP UL 3 119229453.566 42 4 2639 1030 2019-05-26 05:17:33.565919
"""

import sys
import os

START_SN = 49
END_SN = 79

def get_filepaths(directory):

    file_paths = []
    for root, directories, files in os.walk(directory):
        for filename in files:
            if filename[-8:] == "pdcp.txt":
                filepath = os.path.join(root, filename)
                file_paths.append(filepath)
    return file_paths

if __name__ == "__main__":
    if len(sys.argv) > 1:
        dir = sys.argv[1]
    else:
        dir = os.getcwd()
    # filenames = get_filepaths(dir)
    # print sys.argv
    filenames = [sys.argv[1]]
    # print filenames

    ul_pkt = []
    dl_pkt = []
    last_sfn_ul = []
    last_sfn_dl = []
    for filename in filenames:
        with open(filename, 'r') as f:
            for line in f:
                blocks = line.split(' ')
                size = int(blocks[8])
                fn = int(blocks[5])
                sfn = int(blocks[6])
                timestamp = float(blocks[4])
                
                if blocks[2] == 'DL':
                    if size > 1000:
                        if len(last_sfn_dl) < 1:
                            last_sfn_dl.append(fn*10 + sfn)
                        else:
                            last_sfn_dl.pop()
                            last_sfn_dl.append(fn*10 + sfn)
                    if START_SN - 1 < size < END_SN + 1:
                        last_ts = last_sfn_dl[0] if last_sfn_dl != [] else (fn * 10 + sfn)
                        last_sfn_dl = []
                        dl_pkt.append([size, fn * 10 + sfn, timestamp, last_ts, fn * 10 + sfn - last_ts])
                else:
                    if size > 1000:
                        if len(last_sfn_ul) < 1:
                            last_sfn_ul.append(fn*10 + sfn)
                        else:
                            last_sfn_ul.pop()
                            last_sfn_ul.append(fn*10 + sfn)
                    if START_SN - 1 < size < END_SN + 1:
                        last_ts = last_sfn_ul[0] if last_sfn_ul != [] else (fn * 10 + sfn)
                        last_sfn_ul = []
                        # if len(ul_pkt)>0 and (size - ul_pkt[-1][0]) > 6:
                            # sys.stderr.write("Gap {} {} {}\n".format(size, fn * 10 + sfn, timestamp))
                        ul_pkt.append([size, fn * 10 + sfn, timestamp, last_ts, fn * 10 + sfn - last_ts])

    # print ul_pkt[0:120]
    # print dl_pkt[0:120]
    ul_pointer = 100 # [82, 111, 5, 77161.461]
    dl_pointer = 100 # [82, 113, 1, 77161.466]
    joint_delay = []
    while ul_pointer < len(ul_pkt) and dl_pointer < len(dl_pkt):
        # print ul_pkt[ul_pointer] + dl_pkt[dl_pointer]
        ul_ts = ul_pkt[ul_pointer][2]
        dl_ts = dl_pkt[dl_pointer][2]
        

        ul_sfn = ul_pkt[ul_pointer][1]
        dl_sfn = dl_pkt[dl_pointer][1]

        if dl_ts - ul_ts > 0.9:
            ul_pointer += 1
            # print ul_pkt[ul_pointer] + dl_pkt[dl_pointer], 1
            continue
        elif ul_ts - dl_ts > 0.9:
            # print ul_pkt[ul_pointer] + dl_pkt[dl_pointer], 11
            dl_pointer += 1
            continue

        # if ul_sfn - dl_sfn > 500 or (-9740 < ul_sfn - dl_sfn < -8000):
        if 2000 > ul_sfn - dl_sfn > 500 or (ul_sfn < 1000 and dl_sfn > 9000 and (ul_sfn - dl_sfn + 10240 > 500)):
            dl_pointer += 1
            # print ul_pkt[ul_pointer] + dl_pkt[dl_pointer], 111
            continue
        elif 2000 > dl_sfn - ul_sfn > 500 or (dl_sfn < 1000 and ul_sfn > 9000 and (dl_sfn - ul_sfn + 10240 > 500)):
            ul_pointer += 1
            # print ul_pkt[ul_pointer] + dl_pkt[dl_pointer], 1111
            continue

        ul_size = ul_pkt[ul_pointer][0]
        dl_size = dl_pkt[dl_pointer][0]
        if ul_size == dl_size:
            # print ul_pkt[ul_pointer] + dl_pkt[dl_pointer]
            joint_delay.append(ul_pkt[ul_pointer] + dl_pkt[dl_pointer])
            dl_pointer += 1
            ul_pointer += 1
        elif (dl_size < ul_size and dl_ts < ul_ts) or (ul_size < START_SN + 5 and dl_size > END_SN - 5):
            dl_pointer += 1
            # print ul_pkt[ul_pointer] + dl_pkt[dl_pointer], 11111
            continue
        else:
            ul_pointer += 1
            # print ul_pkt[ul_pointer] + dl_pkt[dl_pointer], 111111
            continue

    # print "ul_size, ul_fn_sfn, ul_timestamp, first_ul_fn_sfn, ul_trans_delay, dl_size, dl_fn_sfn, dl_timestamp, first_dl_fn_sfn, dl_trans_delay, e2e_delay"
    import sys
    sys.stderr.write("{} effetive samples\n".format(len(joint_delay)/float(len(ul_pkt))))
    for i in joint_delay:
        if 0 < i[6] - i[1] < 1000:
            print ','.join(map(str, i + [i[6] - i[1]]))