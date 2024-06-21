#!/usr/bin/python3
import subprocess
import time
from datetime import datetime

import sys

import tkinter as tk
from tkinter import simpledialog
from tkinter import font
import tkinter.ttk as ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

display_nrow = 5
display_ncol = 2
window_width = 1550
window_height =800

file_name = "./Vch_name.txt"

ip = '192.168.48.46'

d_sens = {0:'101', 1:'102', 2:'103', 3:'104', 4:'106', 5:'107', 6:'109', 7:'207', 8:'RP', 9:'GBT'}

update_time = 1 #second

number_to_name = {}
name_to_number = {}

all_snmp_walk_status = {}

int_ramptask_value = False
graph_update_running_graph = False

gbt_s_nm = 0
rp_s_nm = 0

gbt_sensors = []
rp_sensors = []

hv_sensors = []

object_list = ['outputVoltage','outputSwitch','outputUserConfig','outputMeasurementSenseVoltage','outputMeasurementCurrent', 'outputSupervisionMaxTerminalVoltage','outputMeasurementTerminalVoltage']

for obj in object_list:
    all_snmp_walk_status[obj]={}

with open(file_name, 'r') as file:
    for line in file:
        parts = line.strip().split(',')
        if len(parts) == 2:
            key, value = parts
            if ('GBT' in value) or ('RP' in value):
                term = value.split('_')
                sensors = term[-1]
                if 'GBT' in value:
                    gbt_sensors.append(sensors)#[101/102]
                    gbt_s_nm += 1
                else:
                    rp_sensors.append(sensors)
                    rp_s_nm += 1
                sensors = value.strip('_')
            elif 'HV' in value:
                term = value.split('_')
                pol = term[1]
                if pol == 'P':
                    hv_sensor = term[0]
                    hv_sensors.append(hv_sensor)
            number_to_name[key] = value

name_to_number = {v: k for k, v in number_to_name.items()}

by_sensor_ramptask_running = [int_ramptask_value] *len(hv_sensors)

def hv_sensor_index(target_sensor):
    if target_sensor in hv_sensors:
        index = hv_sensors.index(target_sensor)
        #by_sensor_ramptask_running[index] = True  # 対応する要素を1に更新
    else:
        print(f"{target_sensor} not found in hv_sensors list.")
    return index

def search_ch_number(search_value):
    search_value_str = str(search_value)
    ch_number = 0
    if search_value_str in name_to_number:
        ch_number = name_to_number[search_value_str]
    return ch_number

def search_HVch_number(search_value):
    search_value_str = str(search_value)
    search_str_p = search_value_str +'_P_HV'
    search_str_n = search_value_str +'_N_HV'

    # 対応するキーを検索
    if search_str_p in name_to_number:
        p_HVch_number = name_to_number[search_str_p]
    else:
        print(f' {search_str_p} is nothing!')

    if search_str_n in name_to_number:
        n_HVch_number = name_to_number[search_str_n]
    else:
        print(f' {search_str_n} is nothing!')

    return p_HVch_number,n_HVch_number

def snmp_set(oid, var, ch_number):#var=str
    if oid == 'outputUserConfig' or oid == 'outputSwitch':
        output = subprocess.run('snmpset -v 2c -m +WIENER-CRATE-MIB -c guru' +' '+ ip + ' '+oid + '.'+ch_number+' i '+ var,shell=True, stdout = subprocess.PIPE)
    else:
        output = subprocess.run('snmpset -v 2c -m +WIENER-CRATE-MIB -c guru' +' '+ ip + ' '+oid + '.'+ch_number+' F '+ var,shell=True, stdout = subprocess.PIPE)

    print(ch_number)
    print(output)


def snmp_hvset(voltage, ch_number):

    voltage_float = float(voltage)
    if voltage_float != 0.0:
        output = subprocess.run('snmpset -v 2c -m +WIENER-CRATE-MIB -c guru' +' '+ ip + ' outputVoltage.'+ch_number+' F '+voltage,shell=True, stdout = subprocess.PIPE)
        output_on_off = subprocess.run('snmpset -v 2c -m +WIENER-CRATE-MIB -c guru' +' '+ ip + ' outputSwitch.'+ch_number+' i 1',shell=True, stdout = subprocess.PIPE)
    else:
        output = subprocess.run('snmpset -v 2c -m +WIENER-CRATE-MIB -c guru' +' '+ ip + ' outputVoltage.'+ch_number+' F '+voltage,shell=True, stdout = subprocess.PIPE)
        output_on_off = subprocess.run('snmpset -v 2c -m +WIENER-CRATE-MIB -c guru' +' '+ ip + ' outputSwitch.'+ch_number+' i 0',shell=True, stdout = subprocess.PIPE)

    print(ch_number)
    print(output)
    print(output_on_off)

def snmp_walk_all():
    for obj in object_list:
        result_command = subprocess.run('snmpwalk -v 2c -m +WIENER-CRATE-MIB -c guru ' + ip + ' ' + obj ,shell=True, stdout = subprocess.PIPE)
        result = result_command.stdout.decode("utf8")
        result_strs = result.splitlines()

        for result_of_item in result_strs:
            term = result_of_item.split()
            term_ini = term[0].split('.')
            ch_number = term_ini[-1]

            if obj != 'outputUserConfig' and obj != 'outputSwitch':
                item_satus = term[-2]
            elif obj == 'outputSwitch':
                term_fin = list(term[-1])
                item_satus = term_fin[-2]
            else:
                item_satus = term[-1]

            all_snmp_walk_status[obj][ch_number]= item_satus

    root.after(update_time*1000, snmp_walk_all)

def get_value_use_all(ch_name,oid_name):#strで入れてstrで返す。
    ch_number = str(search_ch_number(ch_name))
    item_status = 0
    item_status_raw = all_snmp_walk_status.get(oid_name,{}).get(ch_number, '0')

    if oid_name != 'outputSwitch' and oid_name != 'outputUserConfig':
        item_status_raw_float = float(item_status_raw)
        if 'HV' in ch_name:
            if oid_name != 'outputMeasurementCurrent':
                item_status_raw_float_2 = "{:.2f}".format(item_status_raw_float)
                item_status = str(item_status_raw_float_2)
            else:
                var_micro = "{:.2f}".format(item_status_raw_float*1000000)
                item_status = str(var_micro)
        else:
            item_status_raw_float_2 = "{:.2f}".format(item_status_raw_float)
            item_status = str(item_status_raw_float_2)
    else:
        item_status = item_status_raw

    return item_status

####################################################################################################################################################
def gui_value(row,sens_name,oid_name):
    if row == 1:
        ch_name = str(sens_name) + '_P2.5'
    elif row == 2:
        ch_name = str(sens_name) + '_P2.3'
    elif row == 3:
        ch_name = str(sens_name) + '_N2.5'
    elif row == 4:
        ch_name = str(sens_name) + '_N2.3'
    elif row == 6:
        ch_name = str(sens_name) + '_N_HV'
    elif row == 7:
        ch_name = str(sens_name) + '_P_HV'

    label_text = f"{get_value_use_all(ch_name,oid_name)}"
    return label_text

def on_off_value(row,sens_name):
    on_off = gui_value(row,sens_name,'outputSwitch')

    if on_off == '1':
        on_off_label = 'ON'
        button_bg = 'green'
    elif on_off == '0':
        on_off_label = 'OFF'
        button_bg = 'gray80'
    else :
        on_off_label = 'none'
        button_bg = 'gray80'

    return on_off_label,button_bg


def on_off_device_value(ch_name):
    on_off = get_value_use_all(ch_name,'outputSwitch')
    if on_off == '1':
        on_off_label = 'ON'
        button_bg = 'green'
    elif on_off == '0':
        on_off_label = 'OFF'
        button_bg = 'gray80'
    else :
        on_off_label = 'none'
        button_bg = 'gray80'

    return on_off_label,button_bg

def userconfig_device_value(ch_name):
    on_off = get_value_use_all(ch_name,'outputUserConfig')

    if on_off == '2':
        on_off_label = 'ON'
        button_bg = 'deep sky blue'
    elif on_off == '8':
        on_off_label = 'OFF'
        button_bg = 'gray80'
    else :
        on_off_label = 'none'
        button_bg = 'gray80'

    return on_off_label,button_bg

def userconfig_value(row,sens_name):
    on_off = gui_value(row,sens_name,'outputUserConfig')

    if on_off == '2':
        on_off_label = 'ON'
        button_bg = 'deep sky blue'
    elif on_off == '8':
        on_off_label = 'OFF'
        button_bg = 'gray80'
    else :
        on_off_label = 'none'
        button_bg = 'f"{window_height}"f"{window_height}"gray80'

    return on_off_label,button_bg

#POWER & SW mode ON/OFF#######################################################################################################################################################
def on_off_window(row,sens_name,oid):
    def on_click():
        ch_number=search_ch_number(ch_name)
        if oid == 'outputSwitch':
            on_judge = '1'
        else:
            on_judge = '2'
        snmp_set(oid, on_judge, ch_number)
        on_off_wd.destroy()

    def off_click():
        ch_number=search_ch_number(ch_name)
        if oid == 'outputSwitch':
            off_judge = '0'
        else:
            off_judge = '8'
        snmp_set(oid, off_judge, ch_number)
        on_off_wd.destroy()

    # 新規ウィンドウを表示
    on_off_wd = tk.Toplevel(root)
    on_off_wd.title("Fix window")
    on_off_wd.geometry("300x80")

    if row == 1:
        ch_name = str(sens_name) + '_P2.5'
    elif row == 2:
        ch_name = str(sens_name) + '_P2.3'
    elif row == 3:
        ch_name = str(sens_name) + '_N2.5'
    elif row == 4:
        ch_name = str(sens_name) + '_N2.3'

    if oid == 'outputSwitch':
        text_name = '【ON/OFF : '+ch_name+' LV】'
    else:
        text_name = '【ON/OFF : '+ch_name+' SW mode】'
    la = tk.Label(on_off_wd, text=text_name,font=14)
    la.pack(fill='x')

    frame1 = tk.Frame(on_off_wd,pady=10)
    frame1.pack()

    bt_on = tk.Button(frame1, text='ON', command=on_click, bg='green')
    bt_on.pack(side="left")
    bt_off = tk.Button(frame1, text='OFF', command=off_click, bg='gray80')
    bt_off.pack(side="left")

    on_off_wd.mainloop()

def on_off_device_wd(ch_name,oid):
    def on_click():
        ch_number=search_ch_number(ch_name)
        if oid == 'outputSwitch':
            on_judge = '1'
        else:
            on_judge = '2'
        snmp_set(oid, on_judge, ch_number)
        on_off_wd.destroy()

    def off_click():
        ch_number=search_ch_number(ch_name)
        if oid == 'outputSwitch':
            off_judge = '0'
        else:
            off_judge = '8'
        snmp_set(oid, off_judge, ch_number)
        on_off_wd.destroy()

    # 新規ウィンドウを表示
    on_off_wd = tk.Toplevel(root)
    on_off_wd.title("Fix window")
    on_off_wd.geometry("300x80")

    if oid == 'outputSwitch':
        text_name = '【ON/OFF : '+ch_name+' LV】'
    else:
        text_name = '【ON/OFF : '+ch_name+' SW mode】'
    la = tk.Label(on_off_wd, text=text_name,font=14)
    la.pack(fill='x')

    frame1 = tk.Frame(on_off_wd,pady=10)
    frame1.pack()

    bt_on = tk.Button(frame1, text='ON', command=on_click, bg='green')
    bt_on.pack(side="left")
    bt_off = tk.Button(frame1, text='OFF', command=off_click, bg='gray80')
    bt_off.pack(side="left")

    on_off_wd.mainloop()

#Low VOLTAGE#####################################################################################################################################################
def device_lv_fix_wd(ch_name):
    def enter_button_click():
        voltage = voltage_set.get()
        voltage_str = str(voltage)
        ch_number = search_ch_number(ch_name)
        snmp_set('outputVoltage' ,voltage_str, ch_number)
        fix_wd.destroy()

    fix_wd = tk.Toplevel(root)
    fix_wd.title("Fix window")
    fix_wd.geometry("300x110")

    text_name = '【Set Voltage : '+ch_name+' LV】'
    la = tk.Label(fix_wd, text=text_name,font=14)
    la.pack(fill='x')

    frame1 = tk.Frame(fix_wd,pady=10)
    frame1.pack()
    label_time = tk.Label(frame1,text="Voltage [V]:")
    label_time.pack(side="left")
    voltage_set = tk.Entry(frame1,justify="center",width=15)
    voltage_now = get_value_use_all(ch_name,'outputVoltage')
    voltage_set.insert(0, voltage_now)
    voltage_set.pack(side="left")

    bt = ttk.Button(fix_wd, text='ENTER', command=enter_button_click)
    bt.pack()

    fix_wd.mainloop()

def lv_fix_window(row,sens_name):
    def enter_button_click():
        voltage = voltage_set.get()
        voltage_str = str(voltage)
        ch_number = search_ch_number(ch_name)
        snmp_set('outputVoltage' ,voltage_str, ch_number)
        fix_wd.destroy()

    fix_wd = tk.Toplevel(root)
    fix_wd.title("Fix window")
    fix_wd.geometry("300x110")

    if row == 1:
        ch_name = str(sens_name) + '_P2.5'
    elif row == 2:
        ch_name = str(sens_name) + '_P2.3'
    elif row == 3:
        ch_name = str(sens_name) + '_N2.5'
    else:
        ch_name = str(sens_name) + '_N2.3'
    sens_name_str = ch_name+' '

    text_name = '【Set Voltage : '+sens_name_str+' LV】'
    la = tk.Label(fix_wd, text=text_name,font=14)
    la.pack(fill='x')

    frame1 = tk.Frame(fix_wd,pady=10)
    frame1.pack()
    label_time = tk.Label(frame1,text="Voltage [V]:")
    label_time.pack(side="left")
    voltage_set = tk.Entry(frame1,justify="center",width=15)
    voltage_now = gui_value(row,sens_name,'outputVoltage')
    voltage_set.insert(0, voltage_now)
    voltage_set.pack(side="left")

    bt = ttk.Button(fix_wd, text='ENTER', command=enter_button_click)
    bt.pack()

    fix_wd.mainloop()

#High VOLTAGE###################################################################################################################################################
def hv_fix_window(sens_name):
    def enter_button_click():
        voltage = voltage_set.get()
        p_HVch_number,n_HVch_number = search_HVch_number(sens_name)
        snmp_hvset(voltage, p_HVch_number)
        snmp_hvset(voltage, n_HVch_number)
        fix_wd.destroy()

    fix_wd = tk.Toplevel(root)
    fix_wd.title("Fix window")
    fix_wd.geometry("300x160")


    sens_name_str = str(sens_name)
    text_name = '【Set Voltage : '+sens_name_str+' HV】'
    la = tk.Label(fix_wd, text=text_name,font=14)
    la.pack(fill='x')

    text_name = '*Note that HV automatically \nswitches ON/OFF when voltage is set!'
    la = tk.Label(fix_wd, text=text_name)
    la.pack(fill='x')

    #Voltageの設定
    frame1 = tk.Frame(fix_wd,pady=10)
    frame1.pack()
    label_time = tk.Label(frame1,text="Voltage [V]:")
    label_time.pack(side="left")
    voltage_set = tk.Entry(frame1,justify="center",width=15)
    voltage_now = gui_value(6,sens_name,'outputVoltage')#row=6はN側
    voltage_set.insert(0, voltage_now)
    voltage_set.pack(side="left")

    bt = ttk.Button(fix_wd, text='ENTER', command=enter_button_click)
    bt.pack()

    fix_wd.mainloop()
#RAMP############################################################################################################################################
def click_close():
    pass

def stop_task(sens_name):
    global by_sensor_ramptask_running

    ramp_task_run_index = hv_sensor_index(sens_name)
    if by_sensor_ramptask_running[ramp_task_run_index]:
        stop_wd = tk.Toplevel(root)
        stop_wd.title("Fix window")
        stop_wd.geometry("400x150")
        stop_wd.configure(bg="red")
        la = tk.Label(stop_wd, text='【Interrupt button pressed】\nDo not operate until \nthe next window appears!', font=30, fg="red",bg = 'yellow')
        la.pack(anchor='center',expand=1)
        stop_wd.protocol("WM_DELETE_WINDOW", click_close)

        by_sensor_ramptask_running[ramp_task_run_index] = False
        stop_wd.mainloop()

def snmpwalk_hv_current(ch):
    result_command = subprocess.run('snmpwalk -Op +0.12 -v 2c -m +WIENER-CRATE-MIB -c guru ' + ip + ' outputMeasurementCurrent.'+ch,shell=True, stdout = subprocess.PIPE)
    result_strs = result_command.stdout.decode("utf8")
    term = result_strs.split()
    current = term[-2]
    current_float = float(current)*1000000
    return current_float

def get_hv_currents(p_HVch_number, n_HVch_number):
    current_p = snmpwalk_hv_current(p_HVch_number)
    current_n = snmpwalk_hv_current(n_HVch_number)
    return current_p, current_n

def update_graph(sens_name, p_HVch_number, n_HVch_number, p_side_currents, n_side_currents, canvas, fig, ax):
    if not graph_update_running_graph:
        return
    current_p, current_n = get_hv_currents(p_HVch_number, n_HVch_number)
    p_side_currents.append(current_p)
    n_side_currents.append(current_n)

    p_side_currents = p_side_currents[-30:]
    n_side_currents = n_side_currents[-30:]

    ax.clear()
    ax.axhline(y=0, color='gray', linestyle='--')
    ax.plot(p_side_currents, label='P-side Current')
    ax.plot(n_side_currents, label='N-side Current')

    # 図全体のレイアウトを調整（ここではサンプルとしてのみ示す）
    fig.subplots_adjust(right=0.85)

    # Y軸の最大値と最小値を設定
    all_currents = p_side_currents + n_side_currents  # 両方のリストを結合
    if all_currents:  # リストが空でない場合にのみ計算
        max_current = max(all_currents)
        min_current = min(all_currents)
        margin = (max_current - min_current) * 0.1  # 上下に少し余裕を持たせる
        ax.set_ylim(min_current - margin, max_current + margin)

    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Current [µA]')

    fig.text(0.5, 0.93, f'{sens_name}_HV', ha='center', transform=fig.transFigure, fontsize=12, color='green')

    if p_side_currents:
        ax.text(len(p_side_currents) - 1, p_side_currents[-1], f'{p_side_currents[-1]:.2f}', color='blue')
    if n_side_currents:
        ax.text(len(n_side_currents) - 1, n_side_currents[-1], f'{n_side_currents[-1]:.2f}', color='orange')

    ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
    canvas.draw()
    root.after(1000, lambda: update_graph(sens_name, p_HVch_number, n_HVch_number, p_side_currents, n_side_currents, canvas, fig, ax))

def stop_graph_update():
    global graph_update_running_graph
    graph_update_running_graph = False

def hv_current_graph(sens_name):
    global graph_update_running_graph
    graph_update_running_graph = True

    p_HVch_number, n_HVch_number = search_HVch_number(sens_name)
    graph_wd = tk.Toplevel(root)
    graph_wd.title("HV_Current_Graph")
    graph_wd.geometry("1200x530")

    p_side_currents = []
    n_side_currents = []

    fig = Figure(figsize=(15, 5), dpi=100)
    ax = fig.add_subplot(111)
    canvas = FigureCanvasTkAgg(fig, master=graph_wd)
    widget = canvas.get_tk_widget()
    widget.pack()

     # 中断ボタンの追加
    stop_button = tk.Button(graph_wd, text="Stop", command=stop_graph_update)
    stop_button.pack()

    update_graph(sens_name, p_HVch_number, n_HVch_number, p_side_currents, n_side_currents, canvas, fig, ax)

    graph_wd.mainloop()
#######################################################

def rampup(sens_name, time_int, voltage_int, vol_from, vol_to):
    p_HVch_number, n_HVch_number = search_HVch_number(sens_name)
    volt_int = float(voltage_int)
    tim_after = float(time_int) * 1000  # 秒からミリ秒に変換
    voltage_from = float(vol_from)
    voltage_to = float(vol_to)
    start_voltage = voltage_from+volt_int

    def ramp_up():
        global by_sensor_ramptask_running
        nonlocal start_voltage
        volt_str = str(start_voltage)
        ramp_task_run_index = hv_sensor_index(sens_name)

        if by_sensor_ramptask_running[ramp_task_run_index]:  # ramp_task_run が True の場合のみ実行
            if start_voltage < voltage_to:
                root.after(int(tim_after), ramp_up)
                snmp_hvset(volt_str, p_HVch_number)
                snmp_hvset(volt_str, n_HVch_number)
                start_voltage += volt_int
            else:
                snmp_hvset(vol_to, p_HVch_number)
                snmp_hvset(vol_to, n_HVch_number)
                by_sensor_ramptask_running[ramp_task_run_index] = False
                def enter_click():
                    for window in root.winfo_children():
                        if window.winfo_class() == "Toplevel":
                            window.destroy()
                res_wd = tk.Toplevel(root)
                res_wd.title("confirmation")
                res_wd.geometry("300x100")
                res_wd.configure(bg="deep sky blue")
                la = tk.Label(res_wd, text='RampUp is complete!', font=20, bg='deep sky blue')
                la.pack(anchor='center', expand=1)
                bt = ttk.Button(res_wd, text='OK', command=enter_click)
                bt.pack()
                res_wd.mainloop()
        else:
            by_sensor_ramptask_running[ramp_task_run_index] = False
            def enter_click():
                for window in root.winfo_children():
                    if window.winfo_class() == "Toplevel":
                        window.destroy()
            res_wd = tk.Toplevel(root)
            res_wd.title("confirmation")
            res_wd.geometry("300x100")
            res_wd.configure(bg="deep sky blue")
            la = tk.Label(res_wd, text='RampUp successfully interrupted', font=20, bg='deep sky blue')
            la.pack(anchor='center', expand=1)
            bt = ttk.Button(res_wd, text='OK', command=enter_click)
            bt.pack()
            res_wd.mainloop()

    ramp_up()

def rampup_window(sens_name):
    def enter_button_click():
        global by_sensor_ramptask_running
        ramp_task_run_index = hv_sensor_index(sens_name)
        by_sensor_ramptask_running[ramp_task_run_index] = True
        ti_int = time_interval.get()
        vol_int = voltage_interval.get()
        vol_from = voltage_from.get()
        vol_to = voltage_to.get()
        ramp_wd.destroy()
        rampup(sens_name, ti_int, vol_int, vol_from, vol_to)
        hv_current_graph(sens_name)

    ramp_wd = tk.Toplevel(root)
    ramp_wd.title("RampUp window")
    ramp_wd.geometry("300x210")

    sens_name_str = str(sens_name)
    text_name = '【Ramp UP : '+sens_name_str+'】'
    la = tk.Label(ramp_wd, text=text_name,font=14)
    la.pack(fill='x')

    #TimeIntervalの設定
    frame1 = tk.Frame(ramp_wd,pady=10)
    frame1.pack()
    label_time = tk.Label(frame1,text="Time Interval [s]:")
    label_time.pack(side="left")
    time_interval = tk.Entry(frame1,justify="center",width=15)
    time_interval.insert(0, '15')
    time_interval.pack(side="left")

    #VoltageIntervalの設定
    frame2 = tk.Frame(ramp_wd,pady=10)
    frame2.pack()
    label_voltage = tk.Label(frame2, text="Voltage Interval [V]:")
    label_voltage.pack(side="left")
    voltage_interval = tk.Entry(frame2,justify="center",width=15)
    voltage_interval.insert(0, '5')
    voltage_interval.pack(side="left")

    #VoltageFromToの設定
    frame3 = tk.Frame(ramp_wd,pady=10)
    frame3.pack()
    label_v = tk.Label(frame3, text="Voltage Range[V]:")
    label_v.pack(side="left")

    voltage_from = tk.Entry(frame3,justify="center", width=8)
    voltage_now = gui_value(6,sens_name,'outputVoltage')#row=6はN側
    voltage_from.insert(0, voltage_now)
    voltage_from.pack(side="left")

    label_from = tk.Label(frame3, text="→")
    label_from.pack(side="left")

    voltage_to = tk.Entry(frame3,justify="center",width=8)
    voltage_to.insert(0, '75')
    voltage_to.pack(side="left")


    bt = ttk.Button(ramp_wd, text='ENTER', command=enter_button_click)
    bt.pack()

    ramp_wd.mainloop()

#---DOWN---------------------------------------------------------------------
def rampdown(sens_name_dn, time_int_dn, voltage_int_dn, vol_from_dn, vol_to_dn):
    p_HVch_number_dn, n_HVch_number_dn = search_HVch_number(sens_name_dn)
    volt_int_dn = float(voltage_int_dn)
    tim_after_dn = float(time_int_dn) * 1000  # 秒からミリ秒に変換
    voltage_from_dn = float(vol_from_dn)
    voltage_to_dn = float(vol_to_dn)
    start_voltage_dn = voltage_from_dn-volt_int_dn

    def ramp_down():
        global by_sensor_ramptask_running
        nonlocal start_voltage_dn
        volt_str_dn = str(start_voltage_dn)
        ramp_task_run_index = hv_sensor_index(sens_name_dn)

        if by_sensor_ramptask_running[ramp_task_run_index]:
            if start_voltage_dn > voltage_to_dn:
                root.after(int(tim_after_dn), ramp_down)
                snmp_hvset(volt_str_dn, p_HVch_number_dn)
                snmp_hvset(volt_str_dn, n_HVch_number_dn)
                start_voltage_dn -= volt_int_dn
            else:
                snmp_hvset(vol_to_dn, p_HVch_number_dn)
                snmp_hvset(vol_to_dn, n_HVch_number_dn)
                by_sensor_ramptask_running[ramp_task_run_index] = False
                def enter_click():
                    for window in root.winfo_children():
                        if window.winfo_class() == "Toplevel":
                            window.destroy()
                res_wd = tk.Toplevel(root)
                res_wd.title("comfirm")
                res_wd.geometry("300x100")
                res_wd.configure(bg="deep sky blue")
                la = tk.Label(res_wd, text='RampDown is complete!', font=20, bg='deep sky blue')
                la.pack(anchor='center',expand=1)
                bt = ttk.Button(res_wd, text='OK', command=enter_click)
                bt.pack()
                res_wd.mainloop()
        else:
            by_sensor_ramptask_running[ramp_task_run_index] = False
            def enter_click():
                for window in root.winfo_children():
                    if window.winfo_class() == "Toplevel":
                        window.destroy()
            res_wd = tk.Toplevel(root)
            res_wd.title("comfirm")
            res_wd.geometry("300x100")
            res_wd.configure(bg="deep sky blue")
            la = tk.Label(res_wd, text='RampDown successfully interrupted', font=20, bg='deep sky blue')
            la.pack(anchor='center',expand=1)
            bt = ttk.Button(res_wd, text='OK', command=enter_click)
            bt.pack()
            res_wd.mainloop()
    ramp_down()

def rampdown_window(sens_name):
    def enter_button_click():
        global by_sensor_ramptask_running
        ramp_task_run_index = hv_sensor_index(sens_name)
        by_sensor_ramptask_running[ramp_task_run_index] = True
        ti_int = time_interval.get()
        vol_int = voltage_interval.get()
        vol_from = voltage_from.get()
        vol_to = voltage_to.get()
        ramp_wd.destroy()
        rampdown(sens_name, ti_int, vol_int, vol_from, vol_to)
        hv_current_graph(sens_name)

    ramp_wd = tk.Toplevel(root)
    ramp_wd.title("RampDown window")
    ramp_wd.geometry("300x210")

    sens_name_str = str(sens_name)
    text_name = '【Ramp DOWN : '+sens_name_str+'】'
    la = tk.Label(ramp_wd, text=text_name,font=14)
    la.pack(fill='x')

    #TimeIntervalの設定
    frame1 = tk.Frame(ramp_wd,pady=10)
    frame1.pack()
    label_time = tk.Label(frame1,text="Time Interval [s]:")
    label_time.pack(side="left")
    time_interval = tk.Entry(frame1,justify="center",width=15)
    time_interval.insert(0, '10')
    time_interval.pack(side="left")

    #VoltageIntervalの設定
    frame2 = tk.Frame(ramp_wd,pady=10)
    frame2.pack()
    label_voltage = tk.Label(frame2, text="Voltage Interval [V]:")
    label_voltage.pack(side="left")
    voltage_interval = tk.Entry(frame2,justify="center",width=15)
    voltage_interval.insert(0, '10')
    voltage_interval.pack(side="left")

    #VoltageFromToの設定
    frame3 = tk.Frame(ramp_wd,pady=10)
    frame3.pack()
    label_v = tk.Label(frame3, text="Voltage Range[V]:")
    label_v.pack(side="left")

    voltage_from = tk.Entry(frame3,justify="center", width=8)
    voltage_now = gui_value(6,sens_name,'outputVoltage')#row=6はN側
    voltage_from.insert(0,voltage_now)
    voltage_from.pack(side="left")

    label_from = tk.Label(frame3, text="→")
    label_from.pack(side="left")

    voltage_to = tk.Entry(frame3,justify="center",width=8)
    voltage_to.insert(0, '0')
    voltage_to.pack(side="left")

    bt = ttk.Button(ramp_wd, text='ENTER', command=enter_button_click)
    bt.pack()

    ramp_wd.mainloop()

#UPDATE#########################################################################################################################################
def update_text(label,row,sens_name,oid):
    global by_sensor_ramptask_running
    current_text = gui_value(row,sens_name,oid)
    try:
        float_current_text = float(current_text)
    except:
        print("error")
    if row == 6 or row ==7:
        if abs(float_current_text) !=0 and oid == 'outputMeasurementSenseVoltage':
            ramp_task_run_index = hv_sensor_index(sens_name)
            if by_sensor_ramptask_running[ramp_task_run_index]:
                bg_onoff = 'yellow'
            elif abs(float_current_text) > 1.5:
                bg_onoff = 'green'
            else:
                bg_onoff = 'gray90'
        else:
            bg_onoff = 'gray90'
    elif oid == 'outputMeasurementTerminalVoltage':
        if float_current_text > float(gui_value(row,sens_name,'outputSupervisionMaxTerminalVoltage'))-0.1 and abs(float_current_text) > 0.1:
            bg_onoff = 'yellow'
        else:
            bg_onoff = 'gray90'
    else:
        bg_onoff = 'gray90'
    label.config(text=current_text, bg=bg_onoff)
    root.after(update_time*1000, lambda: update_text(label,row,sens_name,oid))

def update_device_text(label,ch_name,oid):
    current_text = get_value_use_all(ch_name,oid)
    label.config(text=current_text)
    root.after(update_time*1000, lambda: update_device_text(label,ch_name,oid))

def update_on_off_button(button,row,sens_name):
    current_txt, current_bg = on_off_value(row,sens_name)
    button.config(text=current_txt ,bg=current_bg)
    root.after(update_time*1000, lambda: update_on_off_button(button,row,sens_name))

def update_on_off_device_button(button,ch_name):
    current_txt, current_bg = on_off_device_value(ch_name)
    button.config(text=current_txt ,bg=current_bg)
    root.after(update_time*1000, lambda: update_on_off_device_button(button,ch_name))

def update_userconfig_button(button,row,sens_name):
    current_txt, current_bg = userconfig_value(row,sens_name)
    button.config(text=current_txt ,bg=current_bg)
    root.after(update_time*1000, lambda: update_userconfig_button(button,row,sens_name))

def update_userconfig_device_button(button,ch_name):
    current_txt, current_bg = userconfig_device_value(ch_name)
    button.config(text=current_txt ,bg=current_bg)
    root.after(update_time*1000, lambda: update_userconfig_device_button(button,ch_name))

def update_time_fun():
    current_datetime = datetime.now()
    current_day = time.strftime("%Y/%m/%d")
    current_time = time.strftime("%H:%M:%S")
    day_of_week = current_datetime.strftime("[%a]")
    time_label.config(text=f"{day_of_week}  {current_day} {current_time}")
    root.after(1000, update_time_fun)

#CREAT FRAME##################################################################################################################################################
def create_frame(root, rows, columns, sens_name):
    frame = tk.Frame(root)
    labels = []
    buttons = []

    for row in range(rows):
        row_labels = []
        row_buttons = []

        for col in range(columns):
            #Sensor name
            if row >= 1 and col == 0:
                merged_frame = tk.Frame(frame, borderwidth=1, relief="solid")
                merged_frame.grid(row=1, column=0, rowspan=rows-1, sticky="nsew")
                merged_frame.grid_columnconfigure(0, weight=1)
                merged_frame.grid_rowconfigure(0, weight=1)

                label_text = f"{sens_name}"
                label = tk.Label(merged_frame, text=label_text, bg='gray70')
                label.grid(sticky="nsew")
                row_labels.append(label)

            #LV name
            elif row > 0 and row < 5 and col == 1:
                subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                subframe.grid(row=row, column=col, sticky="nsew")
                subframe.grid_columnconfigure(0, weight=1)
                subframe.grid_rowconfigure(0, weight=1)
                bg_color = 'gray70'

                if row == 1:
                    label_text = 'P 1.8V'
                elif row == 2:
                    label_text = 'P 1.2V'
                elif row == 3:
                    label_text = 'N 1.8V'
                elif row == 4:
                    label_text = 'N 1.2V'

                label = tk.Label(subframe, text=label_text, bg=bg_color)
                label.grid(sticky="nsew")
                row_labels.append(label)

            #HV outputVoltage
            elif row > 5 and col == 1:
                merged_frame = tk.Frame(frame, borderwidth=1, relief="solid")
                merged_frame.grid(row=6, column=1, rowspan=2, sticky="nsew")
                merged_frame.grid_columnconfigure(0, weight=1)
                merged_frame.grid_columnconfigure(1, weight=1)
                merged_frame.grid_rowconfigure(0, weight=1)

                label_text = '0'
                label = tk.Label(merged_frame, text=label_text, bg= 'gray90')

                button_text = 'Fix'
                button = ttk.Button(merged_frame, text=button_text, command=lambda: hv_fix_window(sens_name))

                label.grid(row=0, column=0, sticky="nsew")
                row_labels.append(label)
                update_text(label,row,sens_name,'outputVoltage')

                button.grid(row=0, column=1, sticky="nsew")
                row_buttons.append(button)

            #LV Power & UserConfig
            elif row > 0 and row < 5 and(col==2 or col==5):
                if col == 2 :
                    subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                    subframe.grid(row=row, column=col, sticky="nsew")
                    subframe.grid_columnconfigure(0, weight=1)
                    subframe.grid_rowconfigure(0, weight=1)

                    button_text_onoff,button_bg_onoff = on_off_value(row,sens_name)
                    if row == 1:
                        button = tk.Button(subframe, text=button_text_onoff, command=lambda: on_off_window(1,sens_name,'outputSwitch'), bg=button_bg_onoff )
                    elif row == 2:
                        button = tk.Button(subframe, text=button_text_onoff, command=lambda: on_off_window(2,sens_name,'outputSwitch'), bg=button_bg_onoff )
                    elif row == 3:
                        button = tk.Button(subframe, text=button_text_onoff, command=lambda: on_off_window(3,sens_name,'outputSwitch'), bg=button_bg_onoff )
                    elif row == 4:
                        button = tk.Button(subframe, text=button_text_onoff, command=lambda: on_off_window(4,sens_name,'outputSwitch'), bg=button_bg_onoff)

                    button.grid(row=0, column=0, sticky=tk.EW)
                    row_buttons.append(button)
                    update_on_off_button(button,row,sens_name)

                if col == 5:
                    subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                    subframe.grid(row=row, column=col, sticky="nsew")
                    subframe.grid_columnconfigure(0, weight=1)
                    subframe.grid_columnconfigure(1, weight=1)
                    subframe.grid_rowconfigure(0, weight=1)

                    button_text_sw,button_bg_sw = userconfig_value(row,sens_name)
                    if row == 1:
                        button = tk.Button(subframe, text=button_text_sw, command=lambda: on_off_window(1,sens_name,'outputUserConfig'), bg=button_bg_sw)
                    elif row == 2:
                        button = tk.Button(subframe, text=button_text_sw, command=lambda: on_off_window(2,sens_name,'outputUserConfig'), bg=button_bg_sw)
                    elif row == 3:
                        button = tk.Button(subframe, text=button_text_sw, command=lambda: on_off_window(3,sens_name,'outputUserConfig'), bg=button_bg_sw)
                    else:
                        button = tk.Button(subframe, text=button_text_sw, command=lambda: on_off_window(4,sens_name,'outputUserConfig'), bg=button_bg_sw)

                    button.grid(row=0, column=0, sticky=tk.EW)
                    row_buttons.append(button)
                    update_userconfig_button(button,row,sens_name)


            #HV RampUp
            elif row == 6 and col == 2:
                subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                subframe.grid(row=row, column=col, sticky="nsew")
                subframe.grid_columnconfigure(0, weight=1)
                subframe.grid_rowconfigure(0, weight=1)

                button_text_up = 'Up'
                button_up = ttk.Button(subframe, text=button_text_up, command=lambda: rampup_window(sens_name))
                button_up.grid(row=0, column=0, sticky="nsew")
                row_buttons.append(button_up)

            #HV RampDown
            elif row == 7 and col == 2:
                subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                subframe.grid(row=row, column=col, sticky="nsew")
                subframe.grid_columnconfigure(0, weight=1)
                subframe.grid_rowconfigure(0, weight=1)

                button_text_down = 'Down'
                button_down = ttk.Button(subframe, text=button_text_down, command=lambda: rampdown_window(sens_name))
                button_down.grid(row=0, column=0, sticky="nsew")
                row_buttons.append(button_down)

            #LV outputVoltage
            elif row > 0 and row < 5 and col == 3:
                subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                subframe.grid(row=row, column=col, sticky="nsew")
                subframe.grid_columnconfigure(0, weight=1)
                subframe.grid_columnconfigure(1, weight=1)
                subframe.grid_rowconfigure(0, weight=1)

                label_text = gui_value(row,sens_name,'outputVoltage')
                label = tk.Label(subframe, text=label_text, bg= 'gray90')
                label.grid(row=0, column=0, sticky="nsew")
                row_labels.append(label)
                update_text(label,row, sens_name, 'outputVoltage')

                button_text = "Fix"
                if row == 1:
                    button = ttk.Button(subframe, text=button_text, command=lambda: lv_fix_window(1,sens_name))
                elif row == 2:
                    button = ttk.Button(subframe, text=button_text, command=lambda: lv_fix_window(2,sens_name))
                elif row == 3:
                    button = ttk.Button(subframe, text=button_text, command=lambda: lv_fix_window(3,sens_name))
                elif row == 4:
                    button = ttk.Button(subframe, text=button_text, command=lambda: lv_fix_window(4,sens_name))
                button.grid(row=0, column=1, sticky="nsew")

            # HV Ramp Stop
            elif row > 5 and col == 3:
                merged_frame = tk.Frame(frame, borderwidth=1, relief="solid")
                merged_frame.grid(row=6, column=3, rowspan= 2, sticky="nsew")
                merged_frame.grid_columnconfigure(0, weight=1)
                merged_frame.grid_rowconfigure(0, weight=1)

                button_text = 'Stop\n(Interruption)'
                #button = ttk.Button(merged_frame, text=button_text, command=stop_task)
                button = ttk.Button(merged_frame, text=button_text, command=lambda: stop_task(sens_name))
                button.grid(row=0, column=0, sticky="nsew")
                row_buttons.append(button)

            #HV NorP
            elif row > 5 and col == 5:
                subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                subframe.grid(row=row, column=col, sticky="nsew")
                subframe.grid_columnconfigure(0, weight=1)
                subframe.grid_rowconfigure(0, weight=1)

                if row == 6:
                    label_text = "N(+)"
                else:
                    label_text = "P(-)"
                label = tk.Label(subframe, text=label_text, bg= 'gray70')
                label.grid(sticky="nsew")
                row_labels.append(label)

            #LV/HV measurement
            elif row != 0 and row != 5 and (col == 6 or col == 7 or col == 8):
                #outputMeasurementTerminalVoltage
                if col == 6:
                    subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                    subframe.grid(row=row, column=col, sticky="nsew")
                    subframe.grid_columnconfigure(0, weight=1)
                    subframe.grid_rowconfigure(0, weight=1)
                    label_text = '0'
                    label = tk.Label(subframe, text=label_text, bg= 'gray90')
                    label.grid(sticky="nsew")
                    row_labels.append(label)
                    update_text(label,row,sens_name,'outputMeasurementTerminalVoltage')

                #outputMeasurementSenseVoltage
                if col == 7:
                    subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                    subframe.grid(row=row, column=col, sticky="nsew")
                    subframe.grid_columnconfigure(0, weight=1)
                    subframe.grid_rowconfigure(0, weight=1)
                    label_text = '0'
                    label = tk.Label(subframe, text=label_text, bg= 'gray90')
                    label.grid(sticky="nsew")
                    row_labels.append(label)
                    update_text(label,row,sens_name,'outputMeasurementSenseVoltage')

                #outputMeasurementCurrent
                if col == 8:
                    subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                    subframe.grid(row=row, column=col, sticky="nsew")
                    subframe.grid_columnconfigure(0, weight=1)
                    subframe.grid_rowconfigure(0, weight=1)
                    label_text = '0'
                    label = tk.Label(subframe, text=label_text, bg= 'gray90')
                    label.grid(sticky="nsew")
                    row_labels.append(label)
                    update_text(label,row,sens_name,'outputMeasurementCurrent')

            #LV MaxTV
            elif row != 0 and row != 5 and row != 6 and row != 7 and col == 4:
                subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                subframe.grid(row=row, column=col, sticky="nsew")
                subframe.grid_columnconfigure(0, weight=1)
                subframe.grid_rowconfigure(0, weight=1)
                label_text = '0'
                label = tk.Label(subframe, text=label_text, bg= 'gray90')
                label.grid(sticky="nsew")
                row_labels.append(label)
                update_text(label,row,sens_name,'outputSupervisionMaxTerminalVoltage')

            #HV current detail botton
            elif row > 5 and col == 4:
                merged_frame = tk.Frame(frame, borderwidth=1, relief="solid")
                merged_frame.grid(row=6, column=4, rowspan= 2, sticky="nsew")
                merged_frame.grid_columnconfigure(0, weight=1)
                merged_frame.grid_rowconfigure(0, weight=1)

                button_text = 'Current\nDetail'
                button = ttk.Button(merged_frame, text=button_text, command=lambda: hv_current_graph(sens_name))
                button.grid(row=0, column=0, sticky="nsew")
                row_buttons.append(button)

            else:
                # Other frames
                subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                subframe.grid(row=row, column=col, sticky="nsew")
                subframe.grid_columnconfigure(0, weight=1)
                subframe.grid_rowconfigure(0, weight=1)

                if row == 0:
                    bg_color = 'gray70'
                    if col == 0:
                        label_text = "Sensor"
                    elif col == 1:
                        label_text = "Name"
                    elif col == 2:
                        label_text = "Power"
                    elif col == 3:
                        label_text = "LV [V]"
                    elif col == 4:
                        label_text = "MaxTV [V]"
                    elif col == 5:
                        label_text = "SW mode"
                    elif col == 6:
                        label_text = "TVmeas [V]"
                    elif col == 7:
                        label_text = "Vmeas [V]"
                    elif col == 8:
                        label_text = "Imeas [A]"
                elif row == 5:
                    bg_color = 'gray70'
                    if col == 1:
                        label_text = "HV [V]"
                    elif col == 2:
                        label_text = "Ramp"
                    elif col == 3:
                        label_text = "RampStop"
                    elif col == 4:
                        label_text = "I mon"
                    elif col == 5:
                        label_text = "N/P"
                    elif col == 6:
                        label_text = "TVmeas [V]"
                    elif col == 7:
                        label_text = "Vmeas [V]"
                    elif col == 8:
                        label_text = "Imeas [uA]"
                else:
                    bg_color = 'gray90'
                    label_text = '0'

                label = tk.Label(subframe, text=label_text, bg=bg_color)
                label.grid(sticky="nsew")
                row_labels.append(label)

        labels.append(row_labels)
        buttons.append(row_buttons)
    return frame, labels, buttons

def create_frame_device(root,device,device_rows,columns):
    frame = tk.Frame(root)
    labels = []
    buttons = []

    gbt_row_sens = {}
    rp_row_sens = {}

    gbt_nm = 1
    rp_nm = 1

    gbt_row_ch_name = {}
    rp_row_ch_name = {}

    test = []

    for gbt_sen in gbt_sensors:
        gbt_row_sens[gbt_nm] = gbt_sen
        ch_name = 'GBT_' + gbt_sen
        gbt_row_ch_name[gbt_nm] = ch_name
        gbt_nm += 1

    for rp_sen in rp_sensors:
        rp_row_sens[rp_nm] = rp_sen
        ch_name = 'RP_' + rp_sen
        rp_row_ch_name[rp_nm] = ch_name
        rp_nm += 1

    for row in range(device_rows):
        row_labels = []
        row_buttons = []

        for col in range(columns):

            #Device initial
            if row == 0 and col != 0:
                subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                subframe.grid(row=row, column=col, sticky="nsew")
                subframe.grid_columnconfigure(0, weight=1)
                subframe.grid_rowconfigure(0, weight=1)

                bg_color = 'gray70'
                if col == 1:
                    label_text = "Sensor"
                elif col == 2:
                    label_text = "Power"
                elif col == 3:
                    label_text = "LV [V]"
                elif col == 4:
                    label_text = "MaxTV [V]"
                elif col == 5:
                    label_text = "SW mode"
                elif col == 6:
                    label_text = "TVmeas [V]"
                elif col == 7:
                    label_text = "Vmeas [V]"
                elif col == 8:
                    label_text = "Imeas [A]"

                label = tk.Label(subframe, text=label_text, bg=bg_color)
                label.grid(sticky="nsew")
                row_labels.append(label)

            elif row >= 0 and col == 0:
                merged_frame = tk.Frame(frame, borderwidth=1, relief="solid")
                merged_frame.grid(row=0, column=0, rowspan=device_rows, sticky="nsew")
                merged_frame.grid_columnconfigure(0, weight=1)
                merged_frame.grid_rowconfigure(0, weight=1)

                label_text = device
                label = tk.Label(merged_frame, text=label_text, bg='gray70')
                label.grid(sticky="nsew")
                row_labels.append(label)

            #Sensor name
            elif col == 1:
                subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                subframe.grid(row=row, column=col, sticky="nsew")
                subframe.grid_columnconfigure(0, weight=1)
                subframe.grid_rowconfigure(0, weight=1)
                bg_color = 'gray70'

                if device == 'GBT':
                    label_text = gbt_row_sens[row]
                else:
                    label_text = rp_row_sens[row]

                label = tk.Label(subframe, text=label_text, bg=bg_color)
                label.grid(sticky="nsew")
                row_labels.append(label)

            #LV Power & UserConfig
            elif col==2 or col==5:
                if col == 2 :
                    subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                    subframe.grid(row=row, column=col, sticky="nsew")
                    subframe.grid_columnconfigure(0, weight=1)
                    subframe.grid_rowconfigure(0, weight=1)

                    if device == 'GBT':
                        ch_name = gbt_row_ch_name[row]
                        button_text_onoff,button_bg_onoff = on_off_device_value(gbt_row_ch_name[row])
                        button = tk.Button(subframe, text=button_text_onoff, command=lambda r=row: on_off_device_wd(gbt_row_ch_name[r-0],'outputSwitch'), bg=button_bg_onoff )
                    else:
                        ch_name = rp_row_ch_name[row]
                        button_text_onoff,button_bg_onoff = on_off_device_value(rp_row_ch_name[row])
                        button = tk.Button(subframe, text=button_text_onoff, command=lambda r=row: on_off_device_wd(rp_row_ch_name[r-0],'outputSwitch'), bg=button_bg_onoff )
                    button.grid(row=0, column=0, sticky=tk.EW)
                    row_buttons.append(button)
                    update_on_off_device_button(button,ch_name)

                else:
                    subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                    subframe.grid(row=row, column=col, sticky="nsew")
                    subframe.grid_columnconfigure(0, weight=1)
                    subframe.grid_rowconfigure(0, weight=1)

                    if device == 'GBT':
                        ch_name = gbt_row_ch_name[row]
                        button_text_onoff,button_bg_onoff = userconfig_device_value(gbt_row_ch_name[row])
                        button = tk.Button(subframe, text=button_text_onoff, command=lambda r=row: on_off_device_wd(gbt_row_ch_name[r],'outputUserConfig'), bg=button_bg_onoff )
                    else:
                        ch_name = rp_row_ch_name[row]
                        button_text_onoff,button_bg_onoff = userconfig_device_value(rp_row_ch_name[row])
                        button = tk.Button(subframe, text=button_text_onoff, command=lambda r=row: on_off_device_wd(rp_row_ch_name[r],'outputUserConfig'), bg=button_bg_onoff )
                    button.grid(row=0, column=0, sticky=tk.EW)
                    row_buttons.append(button)
                    update_userconfig_device_button(button,ch_name)

            #LV outputVoltage
            elif col == 3:
                subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                subframe.grid(row=row, column=col, sticky="nsew")
                subframe.grid_columnconfigure(0, weight=1)
                subframe.grid_columnconfigure(1, weight=1)
                subframe.grid_rowconfigure(0, weight=1)

                button_text = "Fix"

                if device == 'GBT':
                    ch_name = gbt_row_ch_name[row]
                    label_text = get_value_use_all(gbt_row_ch_name[row],'outputVoltage')
                    button = tk.Button(subframe, text=button_text, command=lambda r=row: device_lv_fix_wd(gbt_row_ch_name[r]))
                else:
                    ch_name = rp_row_ch_name[row]
                    label_text = get_value_use_all(rp_row_ch_name[row],'outputVoltage')
                    button = tk.Button(subframe, text=button_text, command=lambda r=row: device_lv_fix_wd(rp_row_ch_name[r]))

                label = tk.Label(subframe, text=label_text, bg= 'gray90')

                label.grid(row=0, column=0, sticky="nsew")
                button.grid(row=0, column=1, sticky="nsew")
                row_labels.append(label)
                row_buttons.append(button)
                update_device_text(label,ch_name,'outputVoltage')

            #LV MaxTV
            elif col == 4:
                subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                subframe.grid(row=row, column=col, sticky="nsew")
                subframe.grid_columnconfigure(0, weight=1)
                subframe.grid_rowconfigure(0, weight=1)

                if device == 'GBT':
                    ch_name=gbt_row_ch_name[row]
                    label_text = get_value_use_all(gbt_row_ch_name[row],'outputSupervisionMaxTerminalVoltage')
                else:
                    ch_name=rp_row_ch_name[row]
                    label_text = get_value_use_all(rp_row_ch_name[row],'outputSupervisionMaxTerminalVoltage')
                label = tk.Label(subframe, text=label_text, bg= 'gray90')
                update_device_text(label,ch_name,'outputSupervisionMaxTerminalVoltage')
                label.grid(row=0, column=0, sticky="nsew")
                row_labels.append(label)

            else:
                subframe = tk.Frame(frame, borderwidth=1, relief="solid")
                subframe.grid(row=row, column=col, sticky="nsew")
                subframe.grid_columnconfigure(0, weight=1)
                subframe.grid_rowconfigure(0, weight=1)

                if col == 6:
                    if device == 'GBT':
                        ch_name=gbt_row_ch_name[row]
                        label_text = get_value_use_all(gbt_row_ch_name[row],'outputMeasurementTerminalVoltage')
                    else:
                        ch_name=rp_row_ch_name[row]
                        label_text = get_value_use_all(rp_row_ch_name[row],'outputMeasurementTerminalVoltage')
                    label = tk.Label(subframe, text=label_text, bg= 'gray90')
                    update_device_text(label,ch_name,'outputMeasurementTerminalVoltage')

                if col == 7:
                    if device == 'GBT':
                        ch_name=gbt_row_ch_name[row]
                        label_text = get_value_use_all(gbt_row_ch_name[row],'outputMeasurementSenseVoltage')
                    else:
                        ch_name=rp_row_ch_name[row]
                        label_text = get_value_use_all(rp_row_ch_name[row],'outputMeasurementSenseVoltage')
                    label = tk.Label(subframe, text=label_text, bg= 'gray90')
                    update_device_text(label,ch_name,'outputMeasurementSenseVoltage')

                if col == 8:
                    if device == 'GBT':
                        ch_name=gbt_row_ch_name[row]
                        label_text = get_value_use_all(gbt_row_ch_name[row],'outputMeasurementCurrent')
                    else:
                        ch_name=rp_row_ch_name[row]
                        label_text = get_value_use_all(rp_row_ch_name[row],'outputMeasurementCurrent')
                    label = tk.Label(subframe, text=label_text, bg= 'gray90')
                    update_device_text(label,ch_name,'outputMeasurementCurrent')

                label.grid(row=0, column=0, sticky="nsew")
                row_labels.append(label)

        labels.append(row_labels)
        buttons.append(row_buttons)
    return frame, labels, buttons


def create_gui(root_frame):
    global gbt_s_nm
    global rp_s_nm
    global d_sens
    gbt_rows = gbt_s_nm+1
    rp_rows = rp_s_nm+1
    n_sens = 0
    frame_grid = []

    #frame_top = tk.Frame(root_frame,bg='gray90')
    #frame_top.pack(side="top", pady=10)

    #label_title = tk.Label(frame_top, text="STS Voltage Manager", font=("Helvetica", 24), bg='gray90')
    #label_title.pack(pady=5)

    #time_label = tk.Label(frame_top, text="", font=("Helvetica", 14), bg='gray90')
    #time_label.pack(padx=20)


    for i in range(display_nrow):#行row
        row_frames = []
        for j in range(display_ncol):#列columm
            if d_sens[n_sens] != 'GBT' and d_sens[n_sens] != 'RP':
                frame, _, _ = create_frame(root_frame, 8, 9, d_sens[n_sens])
                frame.grid(row=i, column=j, padx=5, pady=5)
            elif d_sens[n_sens] == 'GBT':
                frame, _, _ = create_frame_device(root_frame, 'GBT',gbt_rows, 9)
                frame.grid(row=i, column=j, padx=5, pady=5)
            else:
                frame, _, _ = create_frame_device(root_frame, 'RP', rp_rows, 9)
                frame.grid(row=i, column=j, padx=5, pady=5)

            row_frames.append(frame)
            n_sens+=1
        frame_grid.append(row_frames)


if __name__ == "__main__":
    '''root = tk.Tk()
    root.title("STS_Voltage_Manager")
    root.resizable(False, False)
    root.configure(bg="gray90")

    frame_top = tk.Frame(root,bg='gray90')
    
    frame_top.pack(side="top", pady=10)

    label_title = tk.Label(frame_top, text="STS Voltage Manager", font=("Helvetica", 24), bg='gray90')
    label_title.pack(pady=5)

    time_label = tk.Label(frame_top, text="", font=("Helvetica", 14), bg='gray90')
    time_label.pack(padx=20)
    update_time_fun()

    snmp_walk_all()

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    
    frame = tk.Frame(root, bg='gray90')
    frame.pack()


    create_gui(frame)

    root.mainloop()'''

    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    canvas = tk.Canvas(root)

    frame = tk.Frame(canvas,bg='gray90')

    root.title("STS_Voltage_Manager")
    root.resizable(False, False)
    root.configure(bg="gray90")

    scrollbar = tk.Scrollbar(canvas, orient=tk.VERTICAL, command=canvas.yview)

    snmp_walk_all()
    create_gui(frame)

    canvas.configure(scrollregion=(0, 0, f"{window_width}", 1600))
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(expand=True, fill=tk.BOTH)
    canvas.create_window((0,0), window=frame, anchor="nw", width=f"{window_width}", height=1600)

    root.mainloop()
