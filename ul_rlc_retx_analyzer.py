__all__ = ["UlRLCReyxAnalyzer"]

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from mobile_insight.analyzer import *
from mobile_insight.analyzer.analyzer import *

import time
import dis
import json
# import threading



class UlRLCReyxAnalyzer(Analyzer):
    def __init__(self):
        Analyzer.__init__(self)
        self.add_source_callback(self.__msg_callback)
        self.pdu_pkts = []
        self.pkt_size = 0
        self.start_ts = 0
        self.pdu_seg = False
        self.rlc_round = 0 
        self.rlc_cur_fn = 0
        self.rlc_ts_dict = {}

        

        self.idx = 3

        self.mac_cur_fn = 0
        self.mac_round = 0 
        self.receive_buffer = [] # queue: [increasing packet size, timestamp]
        self.receive_buffer_backup = [] #use for generate plot
        self.send_buffer = [] # queue : [decrease packet size, timestamp]
        self.pdcp_pdu = [] # queue : [pdu size, timestamp]
        self.mac_pdu = []
        self.pdcp_rx = []
        self.mac_cur_fn = 0 # mac sys fn timestamp 
        self.pdcp_cur_fn = 0 # pdcp sys fn timestamp
        self.buffer_bytes = 0
        self.pdcp_round = 0
        self.mac_round = 0
        # self.mac_ts_dict = {}

        self.count = 0
        self.match = 0
        self.total_wait_delay = 0
        self.total_tx_delay = 0


    def set_source(self, source):
        """
        Set the trace source. Enable the cellular signaling messages

        :param source: the trace source (collector).
        """
        Analyzer.set_source(self, source)

        # Phy-layer logs
        source.enable_log("LTE_RLC_UL_AM_All_PDU")
    def set_idx(self, i):
        self.idx = i
        
    def enable_mapping(self):
        self.mapping = True

    def __del_lat_stat(self):
        """
        Delete one lat_buffer after it is matched with rlc packet
        :return:
        """
        del self.lat_stat[0]
    def __fun_timer(self):
        print('Hello Timer!')

    def __msg_callback(self, msg):
        # fake online analysis
     
        if msg.type_id == "LTE_RLC_UL_AM_All_PDU":
            self.count += 1
            log_item = msg.data.decode()
            # print log_item
            if 'Subpackets' in log_item and len(log_item['Subpackets']) > 0:
                if log_item['Subpackets'][0]['RB Cfg Idx']==self.idx :
                    
                    # print log_item['Subpackets']
                    for pdu in log_item['Subpackets'][0]['RLCUL PDUs']:
                        print pdu
                        
                        if pdu['PDU TYPE'] == 'RLCUL DATA' and pdu['RF'] == '0':
                            sys_fn = pdu['sys_fn']
                            sub_fn = pdu['sub_fn']
                            sn = pdu['SN']

                            prev_time = self.rlc_cur_fn
                            sys_time = sys_fn*10 + sub_fn
                            self.rlc_cur_fn = sys_time
                            if prev_time > sys_time:
                                self.rlc_round += 1
                            
                            pdu_bytes = pdu['pdu_bytes']-pdu['logged_bytes']
                            FI = pdu['FI']
                            lists = []
                            if 'RLC DATA LI' in pdu:
                                LI = pdu['RLC DATA LI']
                                lists.append([FI[0]+'0',LI[0]['LI'], sn])
                                pdu_bytes -= LI[0]['LI']
                                for i in range(1,len(LI)):
                                    lists.append(['00',LI[i]['LI'], sn])
                                    pdu_bytes -= LI[i]['LI']
                                lists.append(['0'+FI[1],pdu_bytes, sn])
                            else:
                                lists.append([FI,pdu_bytes, sn])
                            # print lists

                            for l in lists:
                                if l[0] == '00':
                                    if not self.rlc_ts_dict.has_key(l[1]):
                                        self.rlc_ts_dict[l[1]] = []
                                    self.rlc_ts_dict[l[1]].append([sys_time, sys_time])

                                    # print 'RLC',log_item['timestamp'],10240*self.rlc_round+sys_time, 10240*self.rlc_round+sys_time, l[1]
                                    self.pdu_pkts.append([sys_time, sys_time, l[1], l[2]])
                                    self.pkt_size = 0
                                    self.start_ts = 0
                                elif l[0] == '01':
                                    self.start_ts = sys_time
                                    self.pkt_size += l[1]
                                elif l[0] == '11':
                                    self.pkt_size += l[1]
                                elif l[0] == '10':
                                    self.pkt_size += l[1]

                                    if not self.rlc_ts_dict.has_key(self.pkt_size):
                                        self.rlc_ts_dict[self.pkt_size] = []
                                    self.rlc_ts_dict[self.pkt_size].append([self.start_ts, sys_time])

                                    # print 'RLC',log_item['timestamp'],self.start_ts, 10240*self.rlc_round+sys_time, self.pkt_size
                                    self.pdu_pkts.append([self.start_ts, sys_time, self.pkt_size, l[2]])
                                    self.pkt_size = 0
                                    self.start_ts = 0
                    
                        elif pdu['PDU TYPE'] == 'RLCUL DATA' and pdu['RF'] == '1':
                            sys_fn = pdu['sys_fn']
                            sub_fn = pdu['sub_fn']
                            prev_time = self.rlc_cur_fn
                            sys_time = sys_fn*10 + sub_fn
                            self.rlc_cur_fn = sys_time
                            if prev_time > sys_time:
                                self.rlc_round += 1
                            
                            pdu_bytes = pdu['pdu_bytes']-pdu['logged_bytes']
                            # print str(sys_time+self.rlc_round*10240)+','+str(pdu_bytes)
                            self.pdcp_rx.append([sys_time+self.rlc_round*10240,pdu_bytes])

            if len(self.pdu_pkts) > 20:
                self.pdu_pkts = self.pdu_pkts[-20:]
            print 'rlc', self.pdu_pkts
            print 'retx', self.pdcp_rx
        elif msg.type_id == "LTE_MAC_UL_Buffer_Status_Internal":
            self.count += 1            
            log_item = msg.data.decode()

            if 'Subpackets' in log_item and len(log_item['Subpackets']) > 0:
                pkt_version = log_item['Subpackets'][0]['Version']
                for sample in log_item['Subpackets'][0]['Samples']:

                     # Count current system time
                    sub_fn = int(sample['Sub FN'])
                    sys_fn = int(sample['Sys FN'])
                    sys_time = sys_fn*10 + sub_fn

                    
                    if sys_time < 10240:
                         # valid sys fn
                        if self.mac_cur_fn > 0:
                            self.mac_cur_fn = sys_time
                    elif self.mac_cur_fn >=0:
                        self.mac_cur_fn = (self.mac_cur_fn + 1) % 10240
                    else:
                        continue
                   

                    for lcid in sample['LCIDs']:
                        idx = lcid['Ld Id']

                        if idx != self.idx:
                            continue

                        if pkt_version == 24:
                            new_bytes = lcid.get('New Compressed Bytes', 0)
                        else:
                            new_bytes = lcid.get('New bytes', 0)
                        ctrl_bytes = lcid.get('Ctrl bytes', 0)
                        retx_bytes = lcid.get('Retx bytes',0)
                        total_bytes = new_bytes +retx_bytes# if 'Total Bytes' not in lcid else int(lcid['Total Bytes'])
                        

                        if total_bytes > self.buffer_bytes:
                            # if buffer increase --> new packet adding in the buffer
                            increase_bytes = total_bytes - self.buffer_bytes
                 
                            if len(self.receive_buffer_backup)>0 and self.receive_buffer_backup[-1][1] > self.mac_cur_fn+10240*self.mac_round:
                                self.mac_round += 1
                            
                            self.receive_buffer.append([increase_bytes,self.mac_cur_fn+10240*self.mac_round])
                            self.receive_buffer_backup.append([increase_bytes,self.mac_cur_fn+10240*self.mac_round])
    


                        elif total_bytes < self.buffer_bytes:
                            # print "Recieve Buffer",log_item['timestamp'], str(self.mac_cur_fn +self.mac_round*10240) +','+ str(self.buffer_bytes - total_bytes)
                            send_bytes = self.buffer_bytes - total_bytes
                            self.send_buffer.append([send_bytes,self.mac_cur_fn+10240*self.mac_round])


                                    
                        
                        self.buffer_bytes = total_bytes

        elif msg.type_id == "LTE_PDCP_UL_Cipher_Data_PDU":
            log_item = msg.data.decode()
            if 'Subpackets' in log_item:
                for pkt in log_item['Subpackets'][0]['PDCPUL CIPH DATA']:
                    idx = pkt['Cfg Idx']
                    if idx != self.idx:
                        continue

                    fn = int(pkt['Sys FN'])
                    sfn = int(pkt['Sub FN'])
                    prev_time = self.pdcp_cur_fn

                    self.pdcp_cur_fn = fn*10 + sfn

                    if prev_time > self.pdcp_cur_fn:
                        self.pdcp_round += 1


                    pdu_size = pkt['PDU Size']
               
                            
                
