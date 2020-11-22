"""Helper functions of Yelkovan.

This file includes helper functions of Yelkovan.


"""


def get_function_start(function_name: str, assembly_code: list) -> int:
    """Detects and returns the line number of the first instruction of a function.

    Searches for a function which is named with the parameter `function_name` in 
    the assembly code. After finding the function returns the line number of the 
    first instruciton of the function.
    
    The presence of "<function_name>:" expression in a line indicates the start 
    of the function. The next line is the first instruction line of that 
    function.

    Parameters
    ----------
    function_name : str
        The name of the function which will be searched in the assembly code.
    assembly_code : list of str
        Assembly code in which the main function will be searched.
    
    Returns
    -------
    integer
        The line number of the of the first instruction of the funtion in the
        assembly code if successful.
    
    Raises
    ------
    Exception
        If the function is not found in the assembly code.
    """


    found = False
    function_declaration = '<' + function_name + '>:'

    for line_no, line in enumerate(assembly_code, 0):
        if function_declaration in line:
            found = True
            break

    if found == True:
        return line_no + 1
    else:
        raise Exception('The function' + function_name + 'could not be found in \
                         the current assembly code.')



def get_function_end(function_name: str, assembly_code: list) -> int:
    """Detects and returns the line number of the last instruction of a function.

    Searches for a function which is named with the parameter `function_name` in 
    the assembly code. After finding the function returns the line number of the 
    last instruciton of the function.
    
    The presence of "<function_name>:" expression in a line indicates the start 
    of the function. The line which includes "ret" instruction is the last 
    instruction line of the function.

    Parameters
    ----------
    function_name : str
        The name of the function which will be searched in the assembly code.
    assembly_code : list of str
        Assembly code in which the main function will be searched.
    
    Returns
    -------
    integer
        The line number of the of the last instruction of the funtion in the
        assembly code if successful.
    
    Raises
    ------
    Exception
        If the function is not found in the assembly code.
    """


    start_found = False
    end_found = False
    function_declaration = '<' + function_name + '>:'

    for start_no, line in enumerate(assembly_code, 0):
        if function_declaration in line:
            start_found = True
            break

    if start_found == False:
        raise Exception('The function' + function_name + 'could not be found in \
                         the current assembly code.')

    # This is the first instruction of the function.
    start_no = start_no + 1
    line_no = start_no
    for line in assembly_code[start_no:]:

        # If an empty line is found this means the function ended and no ret
        # instruction is encountered
        if (line == ''):
            break
        
        # Tokenize the current line and check if it is ret instruction or not.
        tokens = line.split()
        if (len(tokens) >= 3 and tokens[2] == 'ret'):
            end_found = True
            break

        line_no = line_no + 1

    if end_found == True:
        return line_no
    else:
        raise Exception('The end point of the function' + function_name + 'could \
                         not be found in the current assembly code.')
