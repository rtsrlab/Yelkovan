
"""Yelkovan main file.

Yelkovan is a program structure analyser for RISC-V architecture. It detects 
basic blocks of risc-v assembly code and creates the control flow graph of the 
program. The cfg is outputted to command line as text and to pdf file as figure. 

The detection of the basic blocks is performed by the help of trace information 
of the program. Yelkovan analyses the trace files created by gem5 architecture 
simulator.

Yelkovan takes two types of input files. Assembly file of the program and
trace files of the program. To be able to create a cfg of the a program perform
the following steps:

1. Create the assembly file of the program's executable file by the help of 
objdump tool which is delivered with the RISC-V compiler toolchain.
2. Give ".dump" extension to the assembly file.
3. Create trace files of the program by using gem5 architecture simulator.
4. Give ".trc" extension to the trace files.
5. Put above mentioned files to the working directory of Yelkovan.
6. Run Yelkovan.
7. The text outuput is going to be shown in command line interface, and the
graphical output is created as a pdf file in the working directory.


TODO: Move helper functions to another module.
TODO: Work on more efficient usage of cfg variable.

"""

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



def main() -> None:
    """Main function of Yelkovan.

    This function is called by the entry point of the Yelkovan. This function
    searches the current directory for assembly file and trace files of the
    program and then calls analyse function for program structure analysis.
    """

    # List of trace files.
    trace_files = []

    for file_name in listdir("./"):
        if file_name.endswith(".trc"):
            trace_files.append(file_name)
        elif file_name.endswith(".dump"):
            assembly_file = file_name

    analyse(assembly_file, trace_files)


def analyse(assembly_file: str, trace_files: list) -> None:
    """Analyses the contents of the assembly file.

    This function is the main function who starts and manages basic block
    detection operation.

    Parameters
    ----------
    assembly_file : str
        Name of the assembly file of the program.
    trace_files : list of str
        List of names of the trace files of the program.
    """


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
    line_no = find_main_function(assembly_code) + 1
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
    root_node = find_main_function(assembly_code) + 1
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


def create_di_graph(cfg: networkx.DiGraph, previous_node: int, 
                    current_node: int) -> None:
    """Creates control flow graph of the program.

    Note: This function is a recursive function.

    In control flow graph a node represents a basic block, and an edge
    represents the connection between two basic blocks. Starting line number of 
    a basic block is the id of the node which represents that basic block.

    Previous node and current node are id numbers of two nodes. In other words
    they are starting line numbers of two basic blocks. Current node is the new 
    node which will be added to the cfg. This function works as follows:

    1. It adds a new node to the cfg with the current_node id number. It updates
    the information of the node with the values from start_list and end_list.
    2. It adds an edge between the current node and previous node. Current node 
    is one of the targets of previous node.
    3. It checks the targets of the current node (newly added basic block) by
    looking at end_list. If there is a target information it calls itself again. 
    In the new call, the id number of newly added node (current_node) will be 
    passed as previous_node argument, and the target of the newly added node 
    will be passed as current_node argument.
    

    Parameters
    ----------
    cfg : directed graph
        This is the control flow graph of the program.
    previous_node : int
        The id number of the previous node. In other words the starting line
        number of the previous basic block.
    current_node : int
        The id number of the current node. In other words the starting line
        number of the current basic block. This node will be added to the
        control flow graph.
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
        # There are two targets
        cfg.nodes[current_node]['target1'] = end_list[index][1]
        create_di_graph(cfg, current_node, end_list[index][1])
        cfg.nodes[current_node]['target2'] = end_list[index][2]
        create_di_graph(cfg, current_node, end_list[index][2])



def remove_duplicates() -> None:
    """Detects and removes the duplicate elements in the end_list.

    This function is called afeter analyzing the assembly code. During detection 
    we don't check duplicate end points. Therefore, after analyzing the file 
    there may be duplicate elements in the end_list. This function checks and 
    removes them.

    This function does not return a value. Instead it makes required 
    modifications to end_list.
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


def check_targets() -> None:
    """Checks the targets of basic blocks.
    
    This function is called afeter analyzing the assembly code. It is used to 
    check the targets of basic blocks. It detects targets of basic blocks which 
    are not detected until now. This only happens if a basic block's target is 
    the next line of the same basic block.

    Iterate all of the items in the end_list. The items of the end_list 
    represent end points of basic blocks. First element of an item is the line 
    number of the end point of a basic block. Other elements of an item are the
    targets of the basic block.
    
    If an item has not target information (basic block has not any 
    target) and is not the end of the main function, the next line of the item 
    should be the target of the item (the target of the basic block should be
    the next line).

    1. If the length of an item is 1 the item has not target information.
    2. If the line number of an item (item[0]) is different from the line number 
    of the end of main function, the item is not the end of the main function.
    In this case the next line of the item is the target of the item (basic 
    block).

    This function does not return a value. Instead it makes required
    modifications to end_list.
    """

    for index, item in enumerate(end_list):
        if (len(item) == 1):
            if (item[0] != end_of_main_function):
                item = [item[0], item[0] + 1]
                end_list[index] = item



def process_fn(line_no: int, assembly_code: list, trace_files: list) -> None:
    """Detects basic blocks in a given funtion.

    Traverses a function in assembly code line by line and detects basic blocks.
    
    First it checks if the is null or not. If the line is null this means the
    end of the function is reached. In this case returns. If the line is not 
    null the line is tokenized and analyzed.

    If the length of the tokens is less than 3 the line is not a valid
    instruction. In this case processing continues with the next line.

    If the line is a "ret" (return from subroutine) instruction starting and
    end points of basic blocks are detected and written in start_list and
    end_list respectively.

    If the line is a branch or jump instruction the related functions which
    process them is called.
    
    This function does not return a value. Instead it adds the line numbers of
    the detected starting and end points of basic blocks to the start_list and
    end_list.

    Parameters
    ----------
    line_no : integer
        Starting line number of the function which is going to be processed.
    assembly_code : list of strings 
        Assembly code of the program.
    trace_files : list of files
        List of trace files of the program.
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
            # Reached end of the function.
            return

        tokens = assembly_code[index].split()
        # tokens[0] -> address:
        # tokens[1] -> hexadecimal code of machine language instruction
        # tokens[2] -> mnemonic
        # tokens[3] -> operands

        if (len(tokens) < 3):
            # Not a valid instruction. Continue with next line.
            continue

        # TODO: Move "ret" code to process_jump_inst function.
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
    

def process_branch_inst(line_no: int, tokens: list, assembly_code: list) -> None:
    """Detects basic block starting and end points from given branch instruction.
    
    Processes a given branch instrcution. Depending on the instruction, it
    detects the startng and end points of basic blocks. This is achieved by the 
    help of the rule set.

    This function does not return a value. Instead it adds the line numbers of
    the detected starting and end points of basic blocks to the start_list and
    end_list.

    Parameters
    ----------
    line_no : integer 
        Line number of the branch instruction which will be processed.
    tokens : list of strings
        The branch instruction line which will be processed.
    assembly_code : list of strings 
        Assembly code of the program.
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


def process_jump_inst(line_no: int, tokens: list, assembly_code: list, 
                      trace_files: list) -> None:
    """Detects basic block starting and end points from given jump instruction.
    
    Processes a given jump instrcution. Depending on the instruction, it
    detects the starting and end points of basic blocks. This is achieved by the 
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



def find_target(source_address: str, assembly_code: list, 
                trace_files: list) ->int:
    """Finds the line number of the target address of an indirect jump 
    instruction by the help of trace files.
 
    This is achived by processing trace files. Firstly the source address 
    of jump instruction is found in the trace files. The subsequent line  
    is the target of the jump instruction. This function extracts the address
    information from the subsequent line in the trace file. Then
    finds the line in the assembly file which contains that address. That
    line is the target of the jump instruction and the beginning of a basic
    block.

    If source address of the jump instruction is not found in the trace files
    than this means that an the path was not taken. In this case returns -1.

    Parameters
    ----------
    source_address : string
        The source address which will be searched in trace files.
    assembly_code : list of strings
        Assembly code in which the line number of the target address will be 
        searched.
    trace_files : list of files
        List of trace files in which the source address will be searched.

    Returns
    -------
    line_no : integer
        The line number of the target address. Positive integer if successful,
        -1 otherwise
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



def address_to_line_no(address: str, assembly_code: list) -> int:
    """Finds the line number of an address and returns the line number of it.

    Parameters
    ----------
    address : string
        The address whose line number will be searched.
    assembly_code : list of strings
        Assembly code in which the address will be searched.

    Returns
    -------
    integer
        The line number of the of the address if successful.
    
    Raises
    ------
    Exception
        If the address is not found in the assembly code.
    """


    found = False

    for line_no, line in enumerate(assembly_code, 0):
        if line and line.split()[0][:-1] == address:
            found = True
            break

    if found == True:
        return line_no
    else:
        raise Exception('The address could not be found in the current assembly file.')



def find_main_function(assembly_code: list) -> int:
    """Finds the main function and returns the line number of the starting
    point of it.

    Searches for main function in the contents of the assembly file. After 
    finding the main function the line number of the starting point of it is
    returned.
    
    The presence of "<main>:" expression in a line indicates the start of the 
    main function.

    Parameters
    ----------
    assembly_code : list of strings
        Assembly code in which the main function will be searched.
    
    Returns
    -------
    integer
        The line number of the of the starting point of the main funtion in the
        assembly code if successful.
    
    Raises
    ------
    Exception
        If main function is not found in the assembly code.
    """


    found = False

    for line_no, line in enumerate(assembly_code, 0):
        if "<main>:" in line:
            found = True
            break

    if found == True:
        return line_no
    else:
        raise Exception('Main function could not be found in the current assembly file.')


if __name__ == "__main__":
    """Entry point of the program.
    """

    main()