#!/usr/bin/python3
file_name = "./Vch_name.txt"
#test
def split_and_assign(input_str):
    if input_str.count(",") == 1:
        parts = input_str.split(",")
        if parts[0] == "":
            back = parts[1]
            front = ""
        elif parts[1] == "":
            back = ""
            front = parts[0]
        else:
            front = parts[0]
            back = parts[1]
    else:
        front = input_str
        back = ""
    return back, front

print("=================================\n<HV setup>\n")
HV_modules_ori = input("Where are HV modules?:")
HV_modules_str = HV_modules_ori.split(',')
HV_module_int = [int(x) for x in HV_modules_str]
with open(file_name, "w") as file:
    for module in HV_module_int:
        print(f"---------------------------------\n<mod[{module}] setup>\nConnected -> ch[#]:\"sensor name\"(0=<#=<7)\nNo Connected -> \"Enter\"\n")
        ch_min = int(str(module)+"00")
        ch_max = int(str(module)+"08")
        for ch in range(ch_min,ch_max):
            ch_ob = input(f"ch[{ch-ch_min}]:")
            ch_n = 2*ch_min+15-ch
            if ch_ob == "":
                line = f"u{ch},{0:03d}\n"
                file.write(line)
                line = f"u{ch_n},{0:03d}\n"
                file.write(line)
            else:
                line = f"u{ch},{ch_ob}_P_HV\n"
                file.write(line)
                line = f"u{ch_n},{ch_ob}_N_HV\n"
                file.write(line)



# テキストファイルを書き込みモードで開く
print("=================================\n<LV setup>\nConnected -> mod[#]:\"sensor name(0-3[ch],4-7[ch])\"\nNo Connected -> \"Enter\"\n")
with open(file_name, "a") as file:
    for module in range(9):
        #if module == HV_module:
        if module in HV_module_int:
            continue  # 指定したmoduleをスキップする

        module_ob = input(f"mod[{module}]:")
        if module_ob == "":#moduleに何も接続していない
            ch_min = int(str(module)+"00")
            ch_max = int(str(module)+"08")
            # 0から8までの数値を含むテキストファイルを作成
            for ch in range(ch_min,ch_max):
                line = f"u{ch},{0:03d}\n"
                file.write(line)
        else:
            back_sensor,front_sensor = split_and_assign(module_ob)
            if front_sensor == "" and back_sensor != "":#module前半に何も接続していないが後半には接続している
                ch_min = int(str(module)+"00")
                ch_max = int(str(module)+"04")
                ch_max_max = int(str(module)+"08")
                for ch in range(ch_min,ch_max):
                    line = f"u{ch},{0:03d}\n"
                    file.write(line)

                for ch in range(ch_max,ch_max_max):
                    if ch % 4 == 0:
                        line = f"u{ch},{back_sensor}_P2.5\n"
                    elif ch % 4 == 1:
                        line = f"u{ch},{back_sensor}_P2.3\n"
                    elif ch % 4 == 2:
                        line = f"u{ch},{back_sensor}_N2.5\n"
                    else:
                        line = f"u{ch},{back_sensor}_N2.3\n"
                    file.write(line)

            elif front_sensor != "" and back_sensor == "":
                ch_min = int(str(module)+"00")
                ch_max = int(str(module)+"04")
                ch_max_max = int(str(module)+"08")
                for ch in range(ch_min,ch_max):
                    if ch % 4 == 0:
                        line = f"u{ch},{front_sensor}_P2.5\n"
                    elif ch % 4 == 1:
                        line = f"u{ch},{front_sensor}_P2.3\n"
                    elif ch % 4 == 2:
                        line = f"u{ch},{front_sensor}_N2.5\n"
                    else:
                        line = f"u{ch},{front_sensor}_N2.3\n"
                    file.write(line)

                for ch in range(ch_max,ch_max_max):
                    line = f"u{ch},{0:03d}\n"
                    file.write(line)

            else:
                ch_min = int(str(module)+"00")
                ch_max = int(str(module)+"04")
                ch_max_max = int(str(module)+"08")
                for ch in range(ch_min,ch_max):
                    if ch % 4 == 0:
                        line = f"u{ch},{front_sensor}_P2.5\n"
                    elif ch % 4 == 1:
                        line = f"u{ch},{front_sensor}_P2.3\n"
                    elif ch % 4 == 2:
                        line = f"u{ch},{front_sensor}_N2.5\n"
                    else:
                        line = f"u{ch},{front_sensor}_N2.3\n"
                    file.write(line)

                for ch in range(ch_max,ch_max_max):
                    if ch % 4 == 0:
                        line = f"u{ch},{back_sensor}_P2.5\n"
                    elif ch % 4 == 1:
                        line = f"u{ch},{back_sensor}_P2.3\n"
                    elif ch % 4 == 2:
                        line = f"u{ch},{back_sensor}_N2.5\n"
                    else:
                        line = f"u{ch},{back_sensor}_N2.3\n"
                    file.write(line)



print(f"The file '{file_name}' has been created.")
