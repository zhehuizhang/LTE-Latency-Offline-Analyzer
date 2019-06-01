__all__ = ["KeyMetricAnalyzer"]

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from mobile_insight.analyzer.analyzer import *
from mobile_insight.analyzer import *

import time
import dis
import json
from datetime import datetime
# import threading



class KeyMetricAnalyzer(Analyzer):
    def __init__(self):
        Analyzer.__init__(self)
        self.add_source_callback(self.__msg_callback)
        self.intvl = 0.2 # period to analyze throughput

        self.last_dl_pdu = {} # {idx: xx}
        self.last_ul_pdu = {}

        # PDCP stats
        self.cur_ts = {} # {idx: {0:xx, 1:xx}} 0 denotes uplink and 1 denotes downlink 
        self.cum_bytes = {} # {idx: {0:xx, 1:xx}} 0 denotes uplink and 1 denotes downlink 

        # PHY stats
        self.cur_ts_phy = {0: None, 1:None} # {0:xx, 1:xx} 0 denotes uplink and 1 denotes downlink 
        self.cum_err_block = {0:0, 1:0} # {0:xx, 1:xx} 0 denotes uplink and 1 denotes downlink 
        self.cum_block = {0:0, 1:0} # {0:xx, 1:xx} 0 denotes uplink and 1 denotes downlink 

        self.since = datetime( 2015, 8, 15, 6, 0, 0 )

    def set_source(self, source):
        """
        Set the trace source. Enable the cellular signaling messages

        :param source: the trace source (collector).
        """
        Analyzer.set_source(self, source)

        # Phy-layer logs
        source.enable_log("LTE_PHY_PUSCH_Tx_Report")
        source.enable_log("LTE_PHY_PDSCH_Stat_Indication")

        # PDCP layer logs
        source.enable_log("LTE_PDCP_DL_Cipher_Data_PDU")
        source.enable_log("LTE_PDCP_UL_Cipher_Data_PDU")

    def time_diff(self, pdu1, pdu2):
        return (pdu2['Sys FN'] * 10 + pdu2['Sub FN']) - (pdu1['Sys FN'] * 10 + pdu1['Sub FN'])

    def __msg_callback(self, msg):

        if msg.type_id == "LTE_PDCP_DL_Cipher_Data_PDU":
            log_item = msg.data.decode()
            if 'Subpackets' in log_item and 'PDCPDL CIPH DATA' in log_item['Subpackets'][0]:
                for pduItem in log_item['Subpackets'][0]['PDCPDL CIPH DATA']:
                    idx = pduItem['Cfg Idx']
                    if idx not in self.cum_bytes:
                        self.cum_bytes[idx] = {0:0, 1:0}
                        self.last_dl_pdu[idx] = None
                        self.last_ul_pdu[idx] = None
                        self.cur_ts[idx] = {0:None, 1:None}

                    sn = int(pduItem['SN'])
                    sys_fn = int(pduItem['Sys FN'])
                    sub_fn = int(pduItem['Sub FN'])
                    pdu_size = int(pduItem['PDU Size'])
                    self.cum_bytes[idx][1] += pdu_size
                    print "RECORD PDCP DL {} {} {} {} {} {} {}".format(idx, (log_item['timestamp']-self.since).total_seconds(), sys_fn, sub_fn, sn, pdu_size, log_item['timestamp'])


                    if self.last_dl_pdu[idx]:
                      lap = self.time_diff(self.last_dl_pdu[idx], pduItem)
                      self.last_dl_pdu[idx] = pduItem
                      if lap > 5:
                        print "DEBUG Downlink", lap
                    else:
                      self.last_dl_pdu[idx] = pduItem


                    # self.pdcp_buffer.append([log_item['timestamp'], sys_fn, sub_fn, pdu_size, pdu_size])
                if self.cur_ts[idx][1]:
                    lap = (log_item['timestamp'] - self.cur_ts[idx][1]).total_seconds()
                    if lap > 0.1:
                        self.cur_ts[idx][1] = log_item['timestamp']
                        tput = self.cum_bytes[idx][1]*8/lap
                        self.cum_bytes[idx][1] = 0
                        print "KPI PDCP idx {} DL throughput at {} is {} kbps".format(idx, self.cur_ts[idx][1], tput/1000)
                else:
                    self.cur_ts[idx][1] = log_item['timestamp']


        elif msg.type_id == "LTE_PDCP_UL_Cipher_Data_PDU":
            log_item = msg.data.decode()
            if 'Subpackets' in log_item and 'PDCPUL CIPH DATA' in log_item['Subpackets'][0]:
                for pduItem in log_item['Subpackets'][0]['PDCPUL CIPH DATA']:
                    idx = pduItem['Cfg Idx']
                    if idx not in self.cum_bytes:
                        self.cum_bytes[idx] = {0:0, 1:0}
                        self.last_ul_pdu[idx] = None
                        self.last_dl_pdu[idx] = None
                        self.cur_ts[idx] = {0:None, 1:None}

                    sn = int(pduItem['SN'])
                    sys_fn = int(pduItem['Sys FN'])
                    sub_fn = int(pduItem['Sub FN'])
                    pdu_size = int(pduItem['PDU Size'])
                    print "RECORD PDCP UL {} {} {} {} {} {} {}".format(idx, (log_item['timestamp']-self.since).total_seconds(), sys_fn, sub_fn, sn, pdu_size, log_item['timestamp'])
                    self.cum_bytes[idx][0] += pdu_size


                    if self.last_ul_pdu[idx]:
                      lap = self.time_diff(self.last_ul_pdu[idx], pduItem)
                      self.last_ul_pdu[idx] = pduItem
                      if lap > 5:
                        print "DEBUG uplink", lap
                    else:
                      self.last_ul_pdu[idx] = pduItem


                    # self.pdcp_buffer.append([log_item['timestamp'], sys_fn, sub_fn, pdu_size, pdu_size])
                if self.cur_ts[idx][0]:
                    lap = (log_item['timestamp'] - self.cur_ts[idx][0]).total_seconds()
                    if lap > 0.1:
                        self.cur_ts[idx][0] = log_item['timestamp']
                        tput = self.cum_bytes[idx][0]*8/lap
                        self.cum_bytes[idx][0] = 0
                        print "KPI PDCP idx {} UL throughput at {} is {} kbps".format(idx, self.cur_ts[idx][0], tput/1000)
                else:
                    self.cur_ts[idx][0] = log_item['timestamp']

        elif msg.type_id == "LTE_PHY_PUSCH_Tx_Report":
            log_item = msg.data.decode()
            if 'Records' in log_item:
                for record in log_item['Records']:
                    # print record
                    if record['Re-tx Index'] == 'First':
                        self.cum_block[0] += 1
                    else:
                        self.cum_err_block[0] += 1

            if self.cur_ts_phy[0] and self.cum_block[0] > 0:
                lap = (log_item['timestamp'] - self.cur_ts_phy[0]).total_seconds()
                if lap > 0.1:
                    self.cur_ts_phy[0] = log_item['timestamp']
                    bler = self.cum_err_block[0]/float(self.cum_block[0]+self.cum_err_block[1])
                    self.cum_block[0] = 0
                    self.cum_err_block[0] = 0
                    print "KPI PHY UL BLER at {} is {} %".format(self.cur_ts_phy[0], bler*100)
            else:
                self.cur_ts_phy[0] = log_item['timestamp']

            # print log_item
        elif msg.type_id == "LTE_PHY_PDSCH_Stat_Indication":
            log_item = msg.data.decode()
            if 'Records' in log_item:
                for record in log_item['Records']:
                    if 'Transport Blocks' in record:
                        for pduItem in record['Transport Blocks']:
                            if pduItem['CRC Result'][-2:] == "ss":
                                self.cum_block[1] += 1
                            else:
                                self.cum_err_block[1] += 1

            if self.cur_ts_phy[1]:
                lap = (log_item['timestamp'] - self.cur_ts_phy[1]).total_seconds()
                if lap > 0.1 and self.cum_block[1] > 0:
                    self.cur_ts_phy[1] = log_item['timestamp']
                    bler = self.cum_err_block[1]/float(self.cum_block[1]+self.cum_err_block[1])
                    self.cum_block[1] = 0
                    self.cum_err_block[1] = 0
                    print "KPI PHY DL BLER at {} is {} %".format(self.cur_ts_phy[1], bler*100)
            else:
                self.cur_ts_phy[1] = log_item['timestamp']
                            
            # print log_item
               
                            
                
