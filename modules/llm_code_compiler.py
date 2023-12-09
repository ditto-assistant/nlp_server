import tkinter as tk
from tkinter import Text, Scrollbar
import subprocess
import os
import ast

class LLMCodeCompiler:
    def __init__(self, root):
        self.root = root
        self.latest_script = None

    def update_script(self, script):
        self.latest_script = script

    def compile_and_run_script(self):
        if self.latest_script is None:
            print("No script to compile.")
            return

        try:
            # Try to parse the script (without executing)
            parsed_script = compile(self.latest_script, '<string>', 'exec', ast.PyCF_ONLY_AST)

            # Compile the script (may still raise other exceptions)
            compiled_script = compile(parsed_script, '<string>', 'exec')

            # Redirect stdout to capture the output
            try:
                import io
                import sys

                old_stdout = sys.stdout
                new_stdout = io.StringIO()
                sys.stdout = new_stdout

                # Execute the compiled script
                exec(compiled_script)

                # Get the output
                output = new_stdout.getvalue()

                # Show the output in the main window
                self.show_output_in_main_window(output)
            finally:
                sys.stdout = old_stdout

        except SyntaxError as e:
            # Show syntax error message in the main window
            self.show_output_in_main_window(f"SyntaxError: {e}")

    def show_output_in_main_window(self, output):
        # Clear existing text in the main window
        for widget in self.root.winfo_children():
            widget.destroy()

        # Create a Text widget to display the output in the main window
        text_widget = Text(self.root, wrap="word", height=20, width=80)
        text_widget.insert(tk.END, output)

        # Create a Scrollbar for the Text widget
        scrollbar = Scrollbar(self.root, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        # Pack the widgets
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def update_compile_and_run(self, script):
        self.update_script(script)
        self.compile_and_run_script()

def isolate_code_from_llm_script(script, language="python"):
    # isolate code from llm script
    script = script.split(f"```{language}")[-1]
    script = script.split("```")[0]
    return script

def write_llm_code(script, language="python"):

    try:

        # isolate code from llm script
        script = isolate_code_from_llm_script(script)

        # save the script to llm_scripts/script.py
        if not os.path.exists("llm_scripts"):
            os.makedirs("llm_scripts")
        if language == "python":
            with open("llm_scripts/script.py", "w") as f:
                f.write(script)
        elif language == "openscad":
            with open("llm_scripts/openscad.SCAD", "w") as f:
                f.write(script)

    except BaseException as e:
        print(e)
        return 'error'
    return 'success'

def run_llm_code():


    # run the script (python llm_scripts/script.py)
    subprocess.Popen(["python", "llm_scripts/script.py"])


def run_openscad_code(script):

    code = isolate_code_from_llm_script(script, language="openscad")

    # save the script to llm_scripts/openSCAD.SCAD
    write_llm_code(code, language="openscad")

    # run the script (openscad script.SCAD)
    subprocess.Popen(["openscad", "llm_scripts/openscad.SCAD"])


if __name__ == '__main__':


    run_openscad_code("""
                 
$fn = 100; // Set the resolution for the sphere

// Create a sphere
sphere(r = 20); // Adjust the radius as needed
                 
    """)

    # run_llm_code()
