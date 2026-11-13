import os
import sys
import glob
import re
def has_gate_delays(code):
    if len(re.findall(r"\w+? +?(and|AND) +?\w+?;",code)) > 0:
        return False
    if len(re.findall(r"\w+? +?(nand|NAND) +?\w+?;",code)) > 0:
        return False
    if len(re.findall(r"\w+? +?(or|OR) +?\w+?;",code)) > 0:
        return False
    if len(re.findall(r"\w+? +?(nor|NOR) +?\w+?;",code)) > 0:
        return False
    if len(re.findall(r"\w+? +?(xor|XOR) +?\w+?;",code)) > 0:
        return False
    if len(re.findall(r"\w+? +?(xnor|XNOR) +?\w+?;",code)) > 0:
        return False
    if len(re.findall(r" +?(not|NOT) +?\w+?;",code)) > 0:
        return False
    return True
    
def has_student_number(code):
    if len(re.findall(r'constant +?StudentID +?: +?STD_LOGIC_VECTOR +?\(27 downto 0\) +?:= +?x\"1835326\";',code)) < 1:
        return False
    return True
def valid_name(name):
    if "CSU22022" in name:
        return True
    if not "25383718" in name:
        return False
    return True

def valid_comp_name(code):
    if len(re.findall(r'entity .+?_25383718(|_TB) is',code)) < 1:
        return False
    if len(re.findall(r'end .+?_25383718(|_TB);',code)) < 1:
        return False
    if len(re.findall(r'architecture (Simulation|Behavioral) of .+?_25383718(|_TB) is',code)) < 1:
        return False
    if len(re.findall(r'COMPONENT .+?_25383718',code)) != len(re.findall(r'COMPONENT',code))//2:
        return False
    return True

ERROR = "\033[31mERROR\033[0m"
def get_name(file):
    return os.path.basename(file.split(".")[0])
def validate(path,top_level=True):
    LOG = ""
    if not os.path.exists(path):
        return f"{ERROR} path does not exist"
    files = [os.path.basename(file) for file in glob.glob(os.path.join(path,"*"))]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(path,x)))
    filenames = [os.path.basename(file.split(".")[0]) for file in glob.glob(os.path.join(path,"*"))]
    basenames = list(set([ file.split("_25383718")[0] for file in filenames if file.count("_") > 1]))

    xpr = [file for file in files if ".xpr" in file]
    sources = [file for file in files if ".srcs" in file]
    checklist = [file for file in files if "CSU22022" in file]
    regexable = "\n".join(filenames) + "\n"
    for file in files:
        if "vhd" in file.split(".")[1]:
            code = open(os.path.join(path,file),"r").read()
            if "TB" in file.split(".")[0] and not has_student_number(code):
                LOG += f"{ERROR}:{file} is missing student number!!!\n"
            if "TB" in file.split(".")[0] and not valid_comp_name(code):
                LOG += f"{ERROR}:{file} has improper component name!!!\n"
            if not has_gate_delays(code):
                LOG += f"{ERROR}:{file} has missing gate delays!!!\n"
    for basename in basenames:
        docs = len(re.findall(fr"{basename}_25383718_Doc\n",regexable))
        if docs == 0:
            LOG += f"{ERROR}: {basename}_25383718_Doc is missing\n"
        elif docs != 1:
            LOG += f"{ERROR}: {basename}_25383718_Doc is duped\n"
            
        tb = len(re.findall(fr"{basename}_25383718_TB\n",regexable))
        if tb == 0:
            LOG += f"{ERROR}: {basename}_25383718_TB is missing\n"
        elif tb != 1:
            LOG += f"{ERROR}: {basename}_25383718_TB is duped\n"
            
        docs = len(re.findall(fr"{basename}_25383718\n",regexable))
        if docs == 0:
            LOG += f"{ERROR}: {basename}_25383718.vhd is missing\n"
        elif docs != 1:
            LOG += f"{ERROR}: {basename}_25383718.vhd is duped\n"

        if len(re.findall(fr"{basename}_25383718_Schematic\d+\n",regexable)) == 0:
            LOG += f"{ERROR}: {basename}_25383718_Schematic is missing\n"
        if len(re.findall(fr"{basename}_25383718_TD\d+\n",regexable)) == 0:
            LOG += f"{ERROR}: {basename}_25383718_TDXX is missing\n"
    for file in glob.glob(os.path.join(path,"*")):
        if not valid_name(os.path.basename(file)):
            LOG += f"{ERROR}: {os.path.basename(file)} is an invalid name\n"
    if LOG == "":
        for basename in basenames:
             LOG += f"{basename} \033[32m✔\033[0m\n"

    if top_level:
        if not valid_name(os.path.basename(path)):
            LOG += f"{ERROR}: folder name {os.path.basename(path)} is invalid\n"
        if len(xpr) != 1:
            LOG += f"{ERROR}: Your Vivado Project File is missing\n"
        if len(sources) != 1:
            LOG += f"{ERROR}: Your Vivado Sources are missing\n"
        if len(checklist) != 1:
            LOG += f"{ERROR}: Your Checklist is missing\n"
    if ERROR not in LOG:
        LOG += "PASS"
    return LOG
print(validate(sys.argv[1]))
print(validate(os.path.join(sys.argv[1],"Processor_25383718.srcs/sim_1/new/"),top_level=False))
print(validate(os.path.join(sys.argv[1],"Processor_25383718.srcs/sources_1/new/"),top_level=False))