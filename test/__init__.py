import os
import sys
REL_PATH = os.path.dirname(os.path.realpath(__file__))
DIR_PATH = os.path.join(REL_PATH, "../source")
SRC_PATH = os.path.abspath(DIR_PATH)
sys.path.insert(0, SRC_PATH)

DIR_PATH = os.path.join(REL_PATH, "fixtures")
SRC_PATH = os.path.abspath(DIR_PATH)
sys.path.append(SRC_PATH)
