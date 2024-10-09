# Diagram Tool

## Description

Python script for creating UML diagrams from source code.
- Can parse multiple languages:
    - Python
    - Javascript (not yet implemented)
    - Typescript (not yet implemented)
- Generate a SVG file with the diagram


## Usage

### Command Line
Use `diagramTool` command to generate the diagram.
```bash
diagramTool [options] <source> <output>
```

#### Options
use ```diagramTool --help``` to see the available options:

```
usage: DiagramTool [-h] [--debug] [--dump] [--save-ast] source output

create a class diagram from source code

positional arguments:
  source      source code main file
  output      output file

options:
  -h, --help  show this help message and exit
  --debug     print debug information
  --dump      dump parsed data to stdout
  --save-ast  save ast to file
```

### From Python
```python
import diagramTool as dt

dt.fromSource(source, output, save_ast=False, dump=False, showBorder=False)
```


## Example

![Example](example.svg)

Class diagram of this project generated with the tool.