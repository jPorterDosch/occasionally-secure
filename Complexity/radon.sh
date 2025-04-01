echo "#### Cyclomatic Complexity test"
radon cc task.py --total-average -s

echo "#### Maintainability Index score (multi-line comments)"
radon mi task.py -s
echo "#### Maintainability Index score (no multi-line comments)"
radon mi task.py -s -m

# LOC: the total number of lines of code
# LLOC: the number of logical lines of code
# SLOC: the number of source lines of code - not necessarily corresponding to the LLOC
# comments: the number of Python comment lines (i.e. only single-line comments #)
# multi: the number of lines representing multi-line strings
# blank: the number of blank lines (or whitespace-only ones)
echo "#### raw metrics"
radon raw task.py -s

echo "#### Halstead complexity metrics (file)"
radon hal task.py
echo "#### Halstead complexity metrics (function)"
radon hal task.py -f