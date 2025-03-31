# 2025.03.31 Note by R. Yamada
1. git clone

2. Vch_name.txt
Vch_name.txtを同じdirに用意する. 以下命名規則.
```
・HV: [module]_[P/N]_HV
・LV: [module]_[P/N][2.5/2.3]
・GBT/RP: [GBT/RP]_[module]
・設定していないchは000とする.
```
ある程度は./make_Vch_name.pyで作ることが可能.

3. ./sts_voltage_manager.py or ./sts_voltage_manager_scl.py
```
display_nrow = 3
display_ncol = 1
window_width = 900
window_height = 600

d_sens = {0:'test', 1:'GBT', 2:'RP', 3:'RP', 4:'106', 5:'107', 6:'109', 7:'RP', 8:'GBT', 9:'RP'}

```
などと好きなように編集して配置を整える.


初めて書いたものなので、全てがベタ書きになっている.開発しにくい.

<重要事項!!!>
・バグった時は、
```
snmpset -v 2c -m +WIENER-CRATE-MIB -c guru 192.168.48.46 sysMainSwitch.0 i 0
```
で強制シャットダウン.電圧を変えたりして触ると変に高電圧がかかる可能性あり.


・最大出力端子電圧を変えたい場合、
```
ex)
snmpset -v 2c -m +WIENER-CRATE-MIB -c guru 192.168.48.46 outputSupervisionMaxTerminalVoltage.u407 F 4.1
```
などとする。これをGUI化していないのは安全のため.
