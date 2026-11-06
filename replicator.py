from dataclasses import dataclass,field
import re
import math
vector_regex =  r"([\w, ]+?) : (in|out) STD_LOGIC_VECTOR \((\d+?) downto 0\)(;|\);)"
single_regex = r"([\w, ]+?) : (in|out) STD_LOGIC(;|\);)"
name_regex = r"entity (.+?) is"


def assign(out_l,in_l,_):
    return f"{out_l} <= {in_l}"
    


@dataclass
class Component:
    name: str
    _ins: dict = field(default_factory=dict)
    _outs: dict = field(default_factory=dict)
    links: list = field(default_factory=list)
    def loads(s):
        new = Component(re.findall(name_regex,s)[0])
        for match in re.findall(vector_regex,s):
            for name in match[0].strip().split(","):
                if match[1] == "in":
                    new._ins[name.strip().upper()] = int(match[2])+1
                else:
                    new._outs[name.strip().upper()] = int(match[2])+1
        for match in re.findall(single_regex,s):
            for name in match[0].strip().split(","):
                if match[1] == "in":
                    new._ins[name.strip().upper()] = 1
                else:
                    new._outs[name.strip().upper()] = 1
        return new
    def link(self,key,other_key,function=assign):
        self.links.append((key.upper(),other_key.upper(),function))
    def ins(self,key):
        return  1 if "(" in key and key.split("(")[0] in self._ins else self._ins[key]
    def outs(self,key):
        return 1 if "(" in key and key.split("(")[0] in self._outs else self._outs[key]

def replicate(parent_comp:Component, rep_comp:Component):
    final = "---- PORTS ----\n"
    for link in parent_comp.links:
        from_l,to_l,_ = link
        if parent_comp.ins(from_l) != rep_comp.ins(to_l):
            final += f"signal {', '.join([f'{from_l}_bit{i}' for i in range(parent_comp.ins(from_l))])} : std_logic;\n"
    for link in rep_comp.links:
        from_l,to_l,_ = link
        if rep_comp.outs(from_l) != parent_comp.outs(to_l):
            final += f"signal {', '.join([f'{to_l}_bit{i}' for i in range(parent_comp.outs(to_l))])} : std_logic;\n"      
    
    final += "---- BITS ----\n"
    N = parent_comp.outs(rep_comp.links[0][1])
    for i in range(N):
        final += "\n"
        for link in parent_comp.links:
            from_l,to_l,func = link
            if parent_comp.ins(from_l) != rep_comp.ins(to_l):
                final += f"""	{func(f'{from_l}_bit{i}',f'{from_l}({i})',i)};\n"""
        final += f"""	bit{i}: {rep_comp.name} PORT MAP (
		{', '.join([f'{to_l} => {from_l}_bit{i}' if parent_comp.ins(from_l) != rep_comp.ins(to_l) else f'{to_l} => {from_l}' for from_l,to_l,_ in parent_comp.links])}, {', '.join([f'{from_l} => {to_l}_bit{i}' if rep_comp.outs(from_l) != parent_comp.outs(to_l) else f'{from_l} => {to_l}' for from_l,to_l,_ in rep_comp.links])});\n"""
        for link in rep_comp.links:
            from_l,to_l,func = link
            if rep_comp.outs(from_l) != parent_comp.outs(to_l):
                final += f"""	{func(f'{to_l}({i})',f'{to_l}_bit{i}',i)};\n"""
    return final

def extrude(parent_comp:Component, fitted_comp:Component,name):
    final = "---- BITS ----\n"
    N = len(parent_comp.links)
    for i,(from_l,to_l,_) in enumerate(parent_comp.links):
        final += f"""	{name}{i}: {fitted_comp.name} PORT MAP (
        {to_l} => {from_l},
        { ", ".join([f'{from_l} => {to_l}' for from_l,to_l,_ in fitted_comp.links])});\n\n"""
    return final

def funnel(parent_comp:Component, fitted_comp:Component,name,suffix=None):
    final = "---- PORTS ----\n"
    for out in fitted_comp.outs:
        if fitted_comp.outs[out] != 1:
            final += f"signal {', '.join([f'{out}_{to_l}{suffix if suffix else ""}' for to_l in [to_l for from_l_c,to_l in fitted_comp.links if from_l_c == out]])} : STD_LOGIC_VECTOR ({fitted_comp.outs[out]-1} downto 0);\n"
        else:
            final += f"signal {', '.join([f'{out}_{to_l}{suffix if suffix else ""}' for to_l in [to_l for from_l_c,to_l in fitted_comp.links if from_l_c == out]])} : std_logic;\n"
    final += f"""\n	{name}: {parent.name} PORT MAP (
    {", ".join([f'{to_l} => {from_l}_{to_l}{suffix if suffix else ""}' for from_l,to_l,_ in fitted_comp.links])},
    { ", ".join([f'{from_l} => {to_l}' for from_l,to_l,_ in parent_comp.links])});\n\n"""
    return final
import copy
def boil_down(Input_Vec):
    final = "---- PORTS ----\nsignal "
    start = Input_Vec[1]
    layers = {0:[f"F{str(i).zfill(2)}" for i in range(start)]}
    signals = []
    for layer in range(1,int(math.log(start,2))):
        layers[layer] = []
        for s in range(0,int(start/(2**(layer-1))),2):
            first = layers[layer-1][s]
            second = layers[layer-1][s+1]
            merger = f"{first}OR{second}"
            layers[layer].append(merger) 
            signals.append(merger) 
    final += ", ".join(signals) + ": STD_LOGIC;\n"
    final += "---- BITS ----\n"
    ops = []
    newlayers = copy.copy(layers)
    newlayers[0] = [f"{Input_Vec[0]}({i})" for i in range(start)]
    for layer in range(1,int(math.log(start,2))):
        for s in range(0,int(start/(2**(layer-1))),2):
            first = newlayers[layer-1][s]
            second = newlayers[layer-1][s+1]
            merger = f"{layers[layer-1][s]}OR{layers[layer-1][s+1]}"
            ops.append(f"{merger} <= {first} OR {second} after OR_gate_delay;")
    final += "\n".join(ops)
    return final
# parent = Component.loads("""entity RF_Mux3_32Bit_25383718 is
    # Port ( A : in STD_LOGIC_VECTOR (1 downto 0);
           # In00 : in STD_LOGIC_VECTOR (31 downto 0);
		   # In01 : in STD_LOGIC_VECTOR (31 downto 0);
		   # In02 : in STD_LOGIC_VECTOR (31 downto 0);
		   # Z : out STD_LOGIC_VECTOR (31 downto 0));
# end RF_Mux3_32Bit_25383718;""")


# child = Component.loads("""entity RF_Mux3_1Bit_25383718 is
    # Port ( A : in STD_LOGIC_VECTOR (1 downto 0);
           # I0 : in STD_LOGIC;
           # I1 : in STD_LOGIC;
           # I2 : in STD_LOGIC;
           # Z : out STD_LOGIC);
# end RF_Mux3_1Bit_25383718;""")

# parent.link("A","A")
# parent.link("In00","I0")
# parent.link("In01","I1")
# parent.link("In02","I2")

# child.link("Z","Z")

# parent = Component.loads("""entity RF_DestReg_Decoder_35383718 is
    # Port ( A : in STD_LOGIC_VECTOR (2 downto 0);
           # Q0, Q1, Q2, Q3, Q4, Q5, Q6, Q7 : out STD_LOGIC);
# end RF_DestReg_Decoder_35383718;""")


# child = Component.loads("""entity RF_Register8Bit_35383718 is
    # Port ( D : in STD_LOGIC_VECTOR (7 downto 0);
           # Load : in STD_LOGIC;
           # CLK : in STD_LOGIC;
           # Reset : in STD_LOGIC;
           # Q : out STD_LOGIC_VECTOR (7 downto 0));
# end RF_Register8Bit_35383718;""")

# parent.link("RWTR_1","Load")
# parent.link("RWTR_2","Load")
# parent.link("RWTR_3","Load")
# parent.link("RWTR_4","Load")
# parent.link("RWTR_5","Load")
# parent.link("RWTR_6","Load")
# parent.link("RWTR_7","Load")


# child.link("D","D")
# child.link("CLK","Clock")
# child.link("Reset","Reset")

# print(extrude(parent,child,"TempReg"))

# parent = Component.loads("""entity RF_Mux8_8Bit_35383718 is
    # Port ( In0, In1, In2, In3 : in STD_LOGIC_VECTOR (7 downto 0);
           # In4, In5, In6, In7 : in STD_LOGIC_VECTOR (7 downto 0);
           # A : in STD_LOGIC_VECTOR (2 downto 0);
           # Z : out STD_LOGIC_VECTOR (7 downto 0));
# end RF_Mux8_8Bit_35383718;""")

# child = Component.loads("""entity RF_Register8Bit_35383718 is
    # Port ( D : in STD_LOGIC_VECTOR (7 downto 0);
           # Load : in STD_LOGIC;
           # CLK : in STD_LOGIC;
           # Reset : in STD_LOGIC;
           # Q : out STD_LOGIC_VECTOR (7 downto 0));
# end RF_Register8Bit_35383718;""")


# child.link("Q","In0")
# child.link("Q","In1")
# child.link("Q","In2")
# child.link("Q","In3")
# child.link("Q","In4")
# child.link("Q","In5")
# child.link("Q","In6")
# child.link("Q","In7")

# parent.link("A","SA")



# print(funnel(parent,child,"MUX8_A"))

# print(funnel(parent,child,"MUX8_B",suffix="T"))



# parent = Component.loads("""entity RF_Mux16_32Bit_25383718 is
    # Port (A : in STD_LOGIC_VECTOR (3 downto 0);
		  # In00 : in STD_LOGIC_VECTOR (31 downto 0);
		  # In01 : in STD_LOGIC_VECTOR (31 downto 0);
		  # In02 : in STD_LOGIC_VECTOR (31 downto 0);
		  # In03 : in STD_LOGIC_VECTOR (31 downto 0);
		  # In04 : in STD_LOGIC_VECTOR (31 downto 0);
		  # In05 : in STD_LOGIC_VECTOR (31 downto 0);
		  # In06 : in STD_LOGIC_VECTOR (31 downto 0);
		  # In07 : in STD_LOGIC_VECTOR (31 downto 0);
		  # In08 : in STD_LOGIC_VECTOR (31 downto 0);
		  # In09 : in STD_LOGIC_VECTOR (31 downto 0);
		  # In10 : in STD_LOGIC_VECTOR (31 downto 0);
		  # In11 : in STD_LOGIC_VECTOR (31 downto 0);
		  # In12 : in STD_LOGIC_VECTOR (31 downto 0);
		  # In13 : in STD_LOGIC_VECTOR (31 downto 0);
		  # In14 : in STD_LOGIC_VECTOR (31 downto 0);
		  # In15 : in STD_LOGIC_VECTOR (31 downto 0);
		  # Z : out STD_LOGIC_VECTOR (31 downto 0);
	# );
# end RF_Mux16_32Bit_25383718;""")


# child = Component.loads("""entity RF_Mux16_1Bit_25383718 is
    # Port ( I : in STD_LOGIC_VECTOR (15 downto 0);
           # S : in STD_LOGIC_VECTOR (3 downto 0);
           # Y : out STD_LOGIC);
# end RF_Mux16_1Bit_25383718;""")

# parent.link("A","S")
# parent.link("In00","I(0)")
# parent.link("In01","I(1)")
# parent.link("In02","I(2)")
# parent.link("In03","I(3)")
# parent.link("In04","I(4)")
# parent.link("In05","I(5)")
# parent.link("In06","I(6)")
# parent.link("In07","I(7)")
# parent.link("In08","I(8)")
# parent.link("In09","I(9)")
# parent.link("In10","I(10)")
# parent.link("In11","I(11)")
# parent.link("In12","I(12)")
# parent.link("In13","I(13)")
# parent.link("In14","I(14)")
# parent.link("In15","I(15)")
# parent.link("In02","I2")

# child.link("Y","Z")
# parent = Component.loads("""entity CPU_Register32Bit_25383718 is
# Port (D : in STD_LOGIC_VECTOR (31 downto 0);
	# CLK : in STD_LOGIC;
	# Load : in STD_LOGIC;
	# Reset : in STD_LOGIC;
	# Q : out STD_LOGIC_VECTOR (31 downto 0));
# end CPU_Register32Bit_25383718;""")
# child = Component.loads("""entity RF_DFlipFlop_35383718 is
    # Port ( CLK, D, Reset : in STD_LOGIC;
           # Q : out STD_LOGIC);
# end RF_DFlipFlop_35383718;""")

# def load_and_or(out_l,in_l,i):
    # final = f"Not_Load_And{i} <= Not_Load_FF and Q_bit{i};\n"
    # final += f"Load_And{i} <= Load and {in_l};\n"
    # final += f"{out_l} <= Not_Load_And{i} or Load_And{i}"
    # return final
# def load_and_or_signals(i):
    # return f"signal Not_Load_And{i},Load_And{i}: STD_LOGIC;"

# parent.link("D","D",load_and_or)
# parent.link("CLK","CLK")
# parent.link("Reset","Reset")
# child.link("Q","Q")

# print(replicate(parent,child))
# for i in range(32):
    # print(load_and_or_signals(i))


# parent = Component.loads("""entity RF_DestReg_Decoder_35383718 is
    # Port ( A : in STD_LOGIC_VECTOR (3 downto 0);
           # Q00, Q01, Q02, Q03, Q04, Q05, Q06, Q07 : out STD_LOGIC;
		   # Q08, Q09, Q10, Q11, Q12, Q13, Q14, Q15 : out STD_LOGIC);
# end RF_DestReg_Decoder_35383718;""")
# child = Component.loads("""entity CPU_Register32Bit_25383718 is
# Port (D : in STD_LOGIC_VECTOR (31 downto 0);
	# CLK : in STD_LOGIC;
	# Load : in STD_LOGIC;
	# Reset : in STD_LOGIC;
	# Q : out STD_LOGIC_VECTOR (31 downto 0));
# end CPU_Register32Bit_25383718;""")


# parent.link("RWTR_0","Load")
# parent.link("RWTR_1","Load")
# parent.link("RWTR_2","Load")
# parent.link("RWTR_3","Load")
# parent.link("RWTR_4","Load")
# parent.link("RWTR_5","Load")
# parent.link("RWTR_6","Load")
# parent.link("RWTR_7","Load")
# parent.link("RWTR_8","Load")
# parent.link("RWTR_9","Load")
# parent.link("RWTR_10","Load")
# parent.link("RWTR_11","Load")
# parent.link("RWTR_12","Load")
# parent.link("RWTR_13","Load")
# parent.link("RWTR_14","Load")
# parent.link("RWTR_15","Load")


# child.link("D","D")
# child.link("CLK","Clock")
# child.link("Reset","Reset")

# print(extrude(parent,child,"TempReg"))


# for i in range(16):
    # print(f"""	RWTR_{i} <= TQ_bit{i} and RW;""")
    
    
parent = Component.loads("""entity DP_Shifter_25383718 is
 Port (B : in STD_LOGIC_VECTOR (31 downto 0);
	   S1 : in STD_LOGIC;
	   S2 : in STD_LOGIC;
	   G : out STD_LOGIC_VECTOR (31 downto 0));
end DP_Shifter_25383718;""")
child = Component.loads("""entity RF_Mux3_1Bit_25383718 is
    Port ( A : in STD_LOGIC_VECTOR (1 downto 0);
           I0 : in STD_LOGIC;
           I1 : in STD_LOGIC;
           I2 : in STD_LOGIC;
           Z : out STD_LOGIC);
end RF_Mux3_1Bit_25383718;""")


parent.link("S1","A(0)")
parent.link("S2","A(1)")
parent.link("B","I0")
parent.link("B","I1")
parent.link("B","I2")
child.link("Z","G")


print(replicate(parent,child))


# print(boil_down(("MuxF_to_F",32)))