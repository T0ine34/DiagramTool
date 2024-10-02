import sys
import os
import subprocess as sp
from feanorTempDir import TempDir, TempFile
import shutil
from gamuLogger import Logger, LEVELS

Logger.setModule("Tex2Pdf")


def getDependencies(tex_file : str):
    if not os.path.exists(tex_file):
        return []
    with open(tex_file) as f:
        lines = f.readlines()
    deps = []
    for line in lines:
        if line.startswith("\\input{"):
            dep = line.split("{")[1].split("}")[0]
            deps.append(dep)
        elif line.startswith("\\include{"):
            dep = line.split("{")[1].split("}")[0]
            deps.append(dep)
        elif line.startswith("\\usepackage"):
            dep = line.split("{")[1].split("}")[0]
            deps.append(f"{dep}.sty")
        
    return deps

def getDependenciesRecursive(tex_file : str):
    deps = getDependencies(tex_file)
    all_deps = []
    for dep in deps:
        all_deps.append(dep)
        all_deps.extend(getDependenciesRecursive(dep))
    return all_deps


def Tex2Pdf(tex_file : str):
    with (TempDir() as temp_dir, TempFile() as stdout_file):
        Logger.debug(f"Temp dir: {temp_dir}")
        current_dir = os.getcwd()

        dependencies = getDependenciesRecursive(tex_file)
        Logger.debug(f"Dependencies: {dependencies}")

        for dep in dependencies:
            if os.path.exists(dep):
                shutil.copy(dep, temp_dir)
        shutil.copy(tex_file, temp_dir)

        os.chdir(temp_dir)
        Logger.debug(f"running pdflatex -halt-on-error -interaction=errorstopmode -file-line-error {tex_file}")
        try:
            proc = sp.run(f"pdflatex -halt-on-error -interaction=errorstopmode -file-line-error {tex_file}", shell=True, stdout=open(stdout_file, "w"), timeout=10)
            match proc.returncode:
                case 0:
                    shutil.copy(tex_file.replace(".tex", ".pdf"), current_dir)
                    Logger.info(
                        f"PDF file {tex_file.replace('.tex', '.pdf')} created"
                    )

                case 32512:
                    Logger.error("pdflatex not found; please install it")

                case _:
                    Logger.error(f"Failed to convert {tex_file} to pdf")
                    Logger.error(f"stdout: {open(stdout_file).read()}")
        except sp.TimeoutExpired:
            Logger.error("pdflatex took too long to run")
            Logger.error(f"stdout: {open(stdout_file).read()}")
        os.chdir(current_dir)
        
        
def main(tex_file : str):
    try:
        Tex2Pdf(tex_file)
    except Exception as e:
        Logger.critical(f"An error occurred: {e}")
        sys.exit(1)
        
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("tex_file", help="The tex file to convert to pdf")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()  
    if args.debug:
        Logger.setLevel('stdout', LEVELS.DEBUG)
    
    main(args.tex_file)

