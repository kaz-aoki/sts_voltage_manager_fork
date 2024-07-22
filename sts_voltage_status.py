#!/usr/bin/python3
import subprocess
import time
import datetime

import sys
MIN_PYTHON = (3,0)

ip='192.168.48.46'

nch=4

class bcolors:
    Non = '\033[34m' #BLUE
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

class lvstat:
    def __init__(self,channel = 'u999'):
        self.channel = channel
        self.outputVoltage = 0.0
        self.outputSupervisionMaxTerminalVoltage = 0.0
        self.outputMeasurementSenseVoltage = 0.0
        self.outputMeasurementTerminalVoltage = 0.0
        self.outputMeasurementCurrent = 0.0
        self.outputUserConfig = 0
    def show(self):
        output_0 = self.channel
        output_1 = '\t' + self.outputVoltage
        output_1 += '\t' + str(self.outputSupervisionMaxTerminalVoltage)
        output_1 += '\t' + self.outputMeasurementSenseVoltage
        output_1 += '\t' + self.outputMeasurementTerminalVoltage
        output_1 += '\t' + self.outputMeasurementCurrent
        output_2 = '\t' + str(self.outputUserConfig)

        if (float(self.outputMeasurementCurrent) > 0.00000000) or (float(self.outputMeasurementCurrent) < -0.00000000):
            print(output_0 + bcolors.OK + output_1 +output_2+ bcolors.RESET)
        else:
            print(bcolors.Non + output_0 + output_1 +output_2+ bcolors.RESET)
        if (((self.channel[-1] == '3') and (self.channel[-4] == 'N')) or (self.channel[-1] == '0') or (self.channel[-1] == '9')):
                print('----------------------------------------------------------------------------------------------')
#       print(self.channel + ' ' + self.outputVoltage
#              + ' ' + self.outputConfigMaxTerminalVoltage + ' ' + self.outputMeasurementSenseVoltage)
        #+ self.outputMeasurementSenseVoltage )

    def show_names(self):
        print('==============================================================================================')
        print('Name\t\tout_V[V] \tMaxTerm_V[V]\tMeasSense_V[V]\tMeasTerm_V[V]\tMeasCurrent[A|uA]\tOutputUserC')
        print('----------------------------------------------------------------------------------------------')
lvstats = {}

def run_snmpwalk(name):
    result = subprocess.run('snmpwalk -v 2c -m +WIENER-CRATE-MIB -c guru ' + ip + ' '+name,shell=True, stdout = subprocess.PIPE)
    return result.stdout.decode("utf8")

def convert_ch():
    Vch_name = {}
    path = './Vch_name.txt'
    with open(path) as f:
        for line in f:
            (i,j) = line.split(',')
            Vch_name[i] = j.rstrip()
    return Vch_name

def get_info():
        #ch->modle名
    Vch_name = convert_ch()

    #1.outputVoltage
    results = run_snmpwalk_float('outputVoltage')#'ret'の値、つまり、nameで指定したすべてのchannelの情報が並んだリストをresultに入れる。
    for item in results:
        lvtmp = lvstat()#class lvstatusで定義した関数を用いる
        try:
            lvtmp.channel = Vch_name[item[0]]#item[0]はchannnel名。item[1]はnameの値
        except:
            print('e')
        lvtmp.outputVoltage = item[1]
        lvstats[Vch_name[item[0]]] =lvtmp#lvstatusという辞書の中に、[module名:name]の値を入れる。※.outputVoltageなどで区別されているため、OIDは混ざらない。

    #2.outputSupervisionMaxTerminalVoltage
    results = run_snmpwalk_float('outputSupervisionMaxTerminalVoltage')
    for item in results:
        lvstats[Vch_name[item[0]]].outputSupervisionMaxTerminalVoltage = item[1]

    #3.outputMeasurementSenseVoltage
    results = run_snmpwalk_float('outputMeasurementSenseVoltage')
    for item in results:
        lvstats[Vch_name[item[0]]].outputMeasurementSenseVoltage = item[1]

    #4.outputMeasurementTerminalVoltage
    results = run_snmpwalk_float('outputMeasurementTerminalVoltage')
    for item in results:
        lvstats[Vch_name[item[0]]].outputMeasurementTerminalVoltage = item[1]

    #5.outputMeasurementCurrent
    results = run_snmpwalk_float('outputMeasurementCurrent')
    for item in results:
        if Vch_name[item[0]][-2] == 'H':
            lvstats[Vch_name[item[0]]].outputMeasurementCurrent = str(float(item[1])*1000000) #uA
        else:
            lvstats[Vch_name[item[0]]].outputMeasurementCurrent = item[1]

    #6.outputUserConfig
    if Vch_name[item[0]][-2] != 'H':
        results = run_snmpwalk_int('outputUserConfig')
        for item in results:
            lvstats[Vch_name[item[0]]].outputUserConfig = item[1]

def run_snmpwalk_float(name):
    result = run_snmpwalk(name)
    result_strs = result.splitlines()

    ret = []
    for item in result_strs:
        line = item.split()
        tmp = line[0].split('.')
        channel = tmp[-1]
        var = line[-2]
        ret.append([channel,var])
    return ret

def run_snmpwalk_int(name):
    result = run_snmpwalk(name)
    result_strs = result.splitlines()

    ret = []
    for item in result_strs:
        line = item.split()
        tmp = line[0].split('.')
        channel = tmp[-1]
        var = line[-1]
        ret.append([channel,var])
    return ret



def print_status():
    get_info()
    Done = False
    for item in lvstats.keys():
        #        print (item)
        l = lvstats[item]
        if ( not Done ) :
            l.show_names()
            Done = True
        l.show()

if __name__ == '__main__':
    if sys.version_info < MIN_PYTHON:
        sys.exit("Python %s.%s or later is required.\n" % MIN_PYTHON)
    while True:
        print_status()
        dt_now = datetime.datetime.now()
        print(dt_now)
        time.sleep(1)
