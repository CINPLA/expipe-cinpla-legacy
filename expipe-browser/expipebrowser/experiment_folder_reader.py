# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
# 
import sys
import os
# import os.path

def experiments():
    return [{}]

# import h5py
# from os import walk, listdir
# from os.path import join, isdir, splitext
# 
# print("I'm being imported!")
# 
# experiments_folder = "/media/imbv-hafting"
# if sys.platform.startswith("win"): 
#     experiments_folder = "//lh-frontend01/imbv-hafting/"  # TODO: Test this on Windows
# 
# experiments_folder = join(experiments_folder, "DATA_SERVER_DONT_TOUCH")
# 
# 
# def walklevel(root_dir, level=1):
#     root_dir = root_dir.rstrip(os.path.sep)
#     assert os.path.isdir(root_dir)
#     num_sep = root_dir.count(os.path.sep)
#     dir_list = []
#     for sub_dir in os.listdir(root_dir):
#         sub_dir = os.path.join(root_dir, sub_dir)
#         if not os.path.isdir(sub_dir):
#             continue
#         num_sep_this = sub_dir.count(os.path.sep)
#         if num_sep + level > num_sep_this:
#             dir_list.extend(walklevel(sub_dir, level-1))
#         elif num_sep + level == num_sep_this:
#             dir_list.append(sub_dir)
#     return dir_list
# 
# 
# def experiments():
#     experiment_list = []
#     for experiment_folder in walklevel(experiments_folder, 3):
#         for experiment_file in listdir(experiment_folder):
#             experiment_file_short = experiment_file
#             experiment_file = join(experiment_folder, experiment_file)
#             filename, extension = splitext(experiment_file)
#             if extension in [".hdf5", ".h5"]:
#                 experiment = {
#                     "filename": experiment_file,
#                     "shortname": experiment_file_short
#                 }
#                 try:
#                     experiment_data = h5py.File(experiment_file, "r")
#                     for attribute, value in experiment_data.attrs:
#                         experiment[attribute] = value
#                     experiment_list.append(experiment)
#                 except IOError:
#                     print("ERROR: Could note open file", experiment_file)
#     return experiment_list
# 
# 
# if __name__ == "__main__":
#     print(experiments())
