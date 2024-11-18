# SCEfix
A tool to fix PDF files signed by the Servicio Canario de Empleo (also known as **SCE**).

# Usage
To use the tool, you will need to have Python 3.6 or later installed.

After having cloned the repository, you can install the dependencies and run the tool as follows:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scefix/cli.py --help
```

## Fix a file and write the output to another file
```bash
python scefix/cli.py <input-file> <output-file>
```

## Fix a file and write the output to stdout (useful for piping)
```bash
python scefix/cli.py <input-file> | gzip > fixed.gz
```

# Limitations
- The tool will only operate on the last PDF in the file. If you want to operate on an intermediate
  PDF, you will have to split the file first.
- The tool assumes the presence of only one `xref` table per PDF. This is not the case with 
  incrementally updated PDFs, which may contain multiple xref tables, but it looks like the SCE 
  CV tool does not build incrementally updated PDFs.

# Please note
the rows from 3 onwards of the `xref_table_1.txt` and `xref_table_2.txt` files contain a trailing
space that **must not** be removed. Most code and text editors automatically delete trailing 
spaces, so please be careful with that.
