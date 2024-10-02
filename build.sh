# ensure an argument is passed
if [ -z "$1" ]; then
    echo "Usage: $0 <input file>"
    exit 1
fi

/home/antoine/DiagramTool/env/bin/python3.12 src/python/python.py $1 --dump --debug && /home/antoine/DiagramTool/env/bin/python3.12 src/structToTeX.py && /home/antoine/DiagramTool/env/bin/python3.12 src/latex.py test.tex --debug