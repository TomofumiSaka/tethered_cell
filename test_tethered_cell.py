import sys
import os

# add current directry to import path
code_dir = os.path.dirname(__file__)
sys.path.append(code_dir)
from tethered_cell import tethered_cell

path = os.path.join(code_dir, 'test_movies/1103_pH6.5_2016.04.15_17.17.19S.ihvideo-2.tif')
tethered_cell(path)