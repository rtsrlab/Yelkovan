
# List sorting
from operator import itemgetter

# Directory listing
from os import listdir

# Graph operations
import networkx
from networkx.drawing.nx_agraph import graphviz_layout, to_agraph

# Graph visualization
import pygraphviz



# Line numbers of starting points of basic blocks.
start_list = []

# Line numbers of end points and line numbers of targets of basic blocks.
# In this list each item represents the end of a basic block. The first element
# of the item is the line number of the end of a basic block. The other elements 
# (if present) of the item represent the targets of the basic block.
end_list = []

# This is the stack like data structure which holds the starting line numbers
# of functions which will be visited and processed for basic block
# detection. During the analysis when we encounter a function we add it to this
# list. When we visit a function we pop that function from this list.
will_be_visited_fn_list = []

# Conditional branch instructions
branch_inst = ["beq", "bne", "blt", "bltu", "bge", "bgeu", "beqz", "bnez",
    "bltz", "blez", "bgtz", "bgez", "bgt", "bgtu", "ble", "bleu"]

# Unconditional jump instruction
jump_inst = ["jal", "j", "jalr", "jr"]


# The set of nodes which have already been added to the the control flow graph 
# of the program.
# Each item in the set is an integer which represents the starting point of a 
# basic block. By the help of this set, we know if a node is already in the 
# control flow graph or not. We use this set in the creation of the control
# flow graph to prevent duplicate entries.
cfg_set = set()


# Line number of the end of main function.
end_of_main_function = 0

# Starting line number of the root node of the graph.
root_node = 0



def main():
    """Main function
    """

    # List of trace files.
    trace_files = []

    for file_name in listdir("./"):
        if file_name.endswith(".trc"):
            trace_files.append(file_name)
        elif file_name.endswith(".dump"):
            assembly_file = file_name

    analyse(assembly_file, trace_files)


def analyse(assembly_file, trace_files):
    """Analyses the contents of the assembly file.
    """

    # Basic blocks. Each basic block is represented as a BasicBlock dataclass.
    #basic_block = []

    visited_fn_list = []

    global start_list
    global end_list
    global will_be_visited_fn_list


    with open(assembly_file) as f:
        content = f.read()
    f.closed

    assembly_code = content.splitlines()


    # Find main function and add to it to the will be visited function list.
    # It is the first function in this list.
    line_no = find_main_fn(assembly_code) + 1
    will_be_visited_fn_list.append(line_no)

    while(will_be_visited_fn_list):

        line_no = will_be_visited_fn_list.pop()

        # If the starting line number of the funtion is not in visited function
        # list then add it to the list and process the related function.
        if (line_no not in visited_fn_list):
            visited_fn_list.append(line_no)
            process_fn(line_no, assembly_code, trace_files)

    start_list = sorted(set(start_list))        
    end_list.sort(key = itemgetter(0))
    remove_duplicates()

    print(start_list)
    print(end_list)
    
    check_targets()
    
    print(start_list)
    print(end_list)

    if (len(start_list) != len(end_list)):
        print("Error: Lengths of the start list and end list do not match!")
        return

    # Create directed graph.
    cfg = networkx.DiGraph()
    root_node = find_main_fn(assembly_code) + 1
    create_di_graph(cfg, -1, root_node)
    print(cfg.nodes(data=True))

    # Configure the graph.
    cfg.graph['node']={'shape':'box', 'fontname':'helvetica', 'margin':'0.07', 'width':'0.1', 'height':'0.1'}
    # cfg.graph['edges']={'arrowsize':'1.0'}

    cfg_graph = to_agraph(cfg)
    print(cfg_graph)
    cfg_graph.layout('dot')
    cfg_graph.draw('cfg.pdf')

    # Print root node information.
    print(cfg.nodes[root_node]['target1'])
    print(cfg.nodes[root_node]['target2'])


def create_di_graph(cfg, previous_node, current_node):
    """Creates control flow graph of the program.
    """

    index = 0

    if (current_node in cfg_set) & (previous_node != -1):
        cfg.add_edge(previous_node, current_node)
        return

    for i in range(0, len(start_list)):
        if (start_list[i] == current_node):
            index = i

    cfg.add_node(current_node)
    cfg_set.add(current_node)

    if (previous_node != -1):
        cfg.add_edge(previous_node, current_node)

    cfg.nodes[current_node]['label'] = "Start: " + str(start_list[index]) + "; End: " + str(end_list[index][0])
    cfg.nodes[current_node]['start'] = start_list[index]
    cfg.nodes[current_node]['end'] = end_list[index][0]
    cfg.nodes[current_node]['target1'] = "null"
    cfg.nodes[current_node]['target2'] = "null"

    if (len(end_list[index]) == 2):
        # There is one target            
        cfg.nodes[current_node]['target1'] = end_list[index][1]
        create_di_graph(cfg, current_node, end_list[index][1])
    elif (len(end_list[index]) == 3):
        # There is two targets
        cfg.nodes[current_node]['target1'] = end_list[index][1]
        create_di_graph(cfg, current_node, end_list[index][1])
        cfg.nodes[current_node]['target2'] = end_list[index][2]
        create_di_graph(cfg, current_node, end_list[index][2])



def remove_duplicates():
    """Detects and removes the duplicate keys in the end_list.
    """

    result = -1    
    while(True):
        if (result != -1):
            del(end_list[result])
            result = -1

        found = False
        for index_1, item_1 in enumerate(end_list):    
            for index_2, item_2 in enumerate(end_list):
                if ((item_1[0] == item_2[0]) & (index_1 != index_2)):
                    found = True
                    if (len(item_1) >= len(item_2)):
                        result = index_2
                    else:
                        result = index_1
                    break

            if (found):
                break

        if (result == -1):
            break


def check_targets():
    """Checks the targets of basic blocks.
    
    Iterate all of the items in the end_list. The items of the end_list 
    represent end points of basic blocks. First element of an item is the line 
    number of a basic block. Other elements of an item are the targets of the 
    basic block.
    
    If an item has not got target information and is not the end of main 
    function, the next line of the item should be the target of the item.

    - If the length of an item is 1 the item has not got target information.
    - If the line number of an item (item[0]) is different from the line number 
    of the end of main function the item is not the end of the main function.
    """

    for index, item in enumerate(end_list):
        if (len(item) == 1):
            if (item[0] != end_of_main_function):
                item = [item[0], item[0] + 1]
                end_list[index] = item



def process_fn(line_no, assembly_code, trace_files):
    """Detects basic blocks in a given funtion.
    """

    global start_list
    global end_list
    global end_of_main_function

    # Start of a funtion is always the start of a basic block.
    start_list.append(line_no)

    index = line_no - 1
    while(True):
        index = index + 1
        if (assembly_code[index] == ""):
            return
        tokens = assembly_code[index].split()
        # tokens[0] -> address:
        # tokens[1] -> hexadecimal code of machine language instruction
        # tokens[2] -> mnemonic
        # tokens[3] -> operands

        if (len(tokens) < 3):
            # Not a valid instruction
            continue

        elif (tokens[2] == 'ret'):
            # Return from subroutine

            # If we are in main function just return. Else find the target of
            # the return instruction.
            if "<main>:" in assembly_code[line_no - 1]:
                end_list.append([index])
                end_of_main_function = index
            else:
                target_line_no = find_target(tokens[0][:-1], assembly_code, trace_files)
                end_list.append([index, target_line_no])

        elif (tokens[2] in branch_inst):
            process_branch_inst(index, tokens, assembly_code)
            
        elif (tokens[2] in jump_inst):
            process_jump_inst(index, tokens, assembly_code, trace_files)
    

def process_branch_inst(line_no, tokens, assembly_code):
    """Detects basic block start and end points from given branch instruction.
    
    Processes a given branch instrcution. Depending on the instruction it
    detects the start and end points of basic blocks. Look at rules in the
    documentation.
    """

    operands = tokens[3].split(',')

    # operands[2] -> target address

    target_line_no = address_to_line_no(operands[2], assembly_code)

    # The line of the current branch instruction is the end of a basic block.
    # Branch instructions have two targets.
    # The subsequent line and the branch target are the targets of the branch
    # instruction. We add all this together to the end list.
    end_list.append([line_no, line_no + 1, target_line_no])


    # Previous line of the target of a branch instruction is also the end of
    # a basic block.
    end_list.append([target_line_no - 1])

    # The subsequent line of a branch instruction is the start of basic block.
    start_list.append(line_no + 1)

    # The target line of a branch instruction is the start of a basic block.
    start_list.append(target_line_no)


def process_jump_inst(line_no, tokens, assembly_code, trace_files):
    """Detects basic block starting and end points from given jump instruction.
    
    Processes a given jump instrcution. Depending on the instruction, it
    detects the start and end points of basic blocks. This is achieved by the 
    help of the rule set.

    This function does not return a value. Instead it adds the line numbers of
    the detected starting and end points of basic blocks to the start_list and
    end_list.

    Parameters
    ----------
    line_no : integer 
        Line number of the jump instruction which will be processed.
    tokens : list of strings
        The jump instruction line which will be processed.
    assembly_code : list of strings 
        Assembly code of the program.
    trace_files : list of files
        List of trace files of the program.
    """

    global will_be_visited_fn_list

    if (tokens[2] == 'jal'):
        operands = tokens[3].split(',')

        # operands[2] -> target address
        
        target_line_no = address_to_line_no(operands[1], assembly_code)

        start_list.append(line_no + 1)
        start_list.append(target_line_no)
        end_list.append([line_no, target_line_no])
        
        will_be_visited_fn_list.append(target_line_no)

    elif (tokens[2] == 'j'):
        
        # No need to split. Fourth token in the line of a j instruction is
        # the target address
        target_line_no = address_to_line_no(tokens[3], assembly_code)

        start_list.append(line_no + 1)
        start_list.append(target_line_no)
        end_list.append([line_no, target_line_no])
        
        # Previous line of the target of a j instruction is also the end of
        # a basic block.
        end_list.append([target_line_no - 1])

    elif (tokens[2] == 'jalr'):

        start_list.append(line_no + 1)

        target_line_no = find_target(tokens[0][:-1], assembly_code, trace_files)
        if (target_line_no == -1):
            print("Error: Could not find the target of jalr instruction on line " + line_no)
        else:
            start_list.append(target_line_no)
            will_be_visited_fn_list.append(target_line_no)

        end_list.append([line_no, target_line_no])
        
    elif (tokens[2] == 'jr'):

        start_list.append(line_no + 1)

        target_line_no = find_target(tokens[0][:-1], assembly_code, trace_files)
        if (target_line_no == -1):
            print("Error: Could not find the target of jr instruction on line " + line_no)
        else:
            start_list.append(target_line_no)
            # Previous line of the target of a jr instruction is also the end of
            # a basic block.
            end_list.append([target_line_no - 1])

        end_list.append([line_no, target_line_no])



def find_target(source_address, assembly_code, trace_files):
    """Finds the line number of the target address of a jump instruction by
    the help of trace files.
 
    This is achived by processing trace files. Firstly the source address 
    of jump instruction is found in the trace files. The subsequent line  
    is the target of the jump instruction. This function extracts the address
    information from the subsequent line in the trace file. Then
    finds the line in the assembly file which contains that address. That
    line is the target of the jump instruction and the beginning of a basic
    block.

    If source address of the jump instruction is not found in the trace files
    than this means that an the path was not taken. In this case returns -1.

    Args:
        source_address (str): The source address which will be searched in trace 
            files.
        assembly_code (list of strings): Assembly code in which the line number 
            of the target address will be searched.
        trace_files (list): List of trace files in which the source address will 
            be searched.

    Returns:
        line_no (int): The line number of the target address.
    """

    for file in trace_files:
        with open(file) as f:
            content = f.read()
        f.closed

        trace_info = content.splitlines()

        for line_no_1, line_1 in enumerate(trace_info, 0):
            if source_address in line_1:
                tokens = trace_info[line_no_1 + 1].split()
                target_address = tokens[4][2:] + ':'
                
                for line_no_2, line_2 in enumerate(assembly_code, 0):
                    if (target_address in line_2):
                        return line_no_2

    return -1



def address_to_line_no(address, assembly_code):
    """Finds the line number of an address and returns the line number of it.

    Args:
        address (str): The address whose line number will be searched.
        assembly_code (list of strings): Assembly code in which the address will
            be searched.
    Returns:
        line_no (int): The line number of the address.
    """

    for line_no, line in enumerate(assembly_code, 0):
        if line and line.split()[0][:-1] == address:
            break

    return line_no



def find_main_fn(assembly_code):
    """Finds the main function and returns the line number of the starting
    point of it.

    Searches for main function in the contents of the assembly file. After 
    finding the main function the line number of the starting point of it is
    returned.
    
    The presence of "<main>:" expression in a line indicates the start of the 
    main function.

    Args:
        assembly_code (list of strings): Assembly code in which the main 
            function will be searched.
    
    Returns:
        line_no (int): The line number of the of the starting point of the main 
            funtion in the file.
    """

    for line_no, line in enumerate(assembly_code, 0):
        if "<main>:" in line:
            break

    return line_no



if __name__ == "__main__":
    """Entry point of the program.
    """

    main()