# extractInternalSignals
This script can be used to extract the names of the internal wires and registers of a Verilog file.

The script accepts the name of the Verilog module file. An example of how the script might be called is shown below:

    "extract_internal_signals.py --filename multiplier.v"

A list of all the internal wires and registers is written to a file with the following format:

    "<module_name>_internal_signals.txt"
    
Tip: You can add an alias to your ~/.aliases file that will point to the script - e.g.:

    "alias extract_internal_signals '<path_to_directory_with_script>/extract_internal_signals.py'"

Then, you can simply call 'extract_internal_signals --filename <module_name>' from *anywhere* in your
Linux environment (assuming you have sourced your .aliases file)
