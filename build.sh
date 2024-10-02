# ensure an argument is passed
if [ -z "$1" ]; then
    echo "Usage: $0 <input file>"
    exit 1
fi

python src/python/python.py $1 --dump --debug
python src/structToTeX.py
python src/latex.py test.tex --debug