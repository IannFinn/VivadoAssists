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
    if len(re.findall(r"\w+? +?(not|NOT) +?\w+?;",code)) > 0:
        return False
    return True
def valid_name(name):
    if "CSU22022" in name:
        return True
    if not "25383718" in name:
        return False
    return True


def get_name(file):
    return os.path.basename(file.split(".")[0])
def validate(path):
    LOG = ""
    if not os.path.exists(path):
        return "ERROR path does not exist"
    files = [os.path.basename(file) for file in glob.glob(os.path.join(path,"*"))]
    filenames = [os.path.basename(file.split(".")[0]) for file in glob.glob(os.path.join(path,"*"))]
    basenames = list(set([ file.split("_25383718")[0] for file in filenames if file.count("_") > 1]))
    xpr = [file for file in files if ".xpr" in file]
    sources = [file for file in files if ".srcs" in file]
    checklist = [file for file in files if "CSU22022" in file]
    if not valid_name(os.path.basename(path)):
        LOG += f"ERROR: folder name {os.path.basename(path)} is invalid\n"
    if len(xpr) != 1:
        LOG += f"ERROR: Your Vivado Project File is missing\n"
    if len(sources) != 1:
        LOG += f"ERROR: Your Vivado Sources are missing\n"
    if len(checklist) != 1:
        LOG += f"ERROR: Your Checklist is missing\n"
    regexable = "\n".join(filenames) + "\n"
    for file in files:
        if "vhd" in file.split(".")[1]:
            if not has_gate_delays(open(os.path.join(path,file),"r").read()):
                LOG += f"ERROR:{file} has missing gate delays!!!\n"
    for basename in basenames:
        docs = len(re.findall(fr"{basename}_25383718_Doc\n",regexable))
        if docs == 0:
            LOG += f"ERROR: {basename}_25383718_Doc is missing\n"
        elif docs != 1:
            LOG += f"ERROR: {basename}_25383718_Doc is duped\n"
            
        tb = len(re.findall(fr"{basename}_25383718_TB\n",regexable))
        if docs == 0:
            LOG += f"ERROR: {basename}_25383718_TB is missing\n"
        elif docs != 1:
            LOG += f"ERROR: {basename}_25383718_TB is duped\n"
            
        docs = len(re.findall(fr"{basename}_25383718\n",regexable))
        if docs == 0:
            LOG += f"ERROR: {basename}_25383718.vhd is missing\n"
        elif docs != 1:
            LOG += f"ERROR: {basename}_25383718.vhd is duped\n"


        if len(re.findall(fr"{basename}_25383718_Schematic\d+\n",regexable)) == 0:
            LOG += f"ERROR: {basename}_25383718_Schematic is missing\n"
        if len(re.findall(fr"{basename}_25383718_TD\d+\n",regexable)) == 0:
            LOG += f"ERROR: {basename}_25383718_TDXX is missing\n"
    for file in glob.glob(os.path.join(path,"*")):
        if not valid_name(os.path.basename(file)):
            LOG += f"ERROR: {os.path.basename(file)} is an invalid name\n"

    if LOG == "":
        LOG = "PASS"
    return LOG
print(validate(sys.argv[1]))