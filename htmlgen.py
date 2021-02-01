# TODO: implement generating INDEX html with "tree" bash command
# https://stackoverflow.com/questions/3785055/how-can-i-create-a-simple-index-html-file-which-lists-all-files-directories
# with falling back to simple ls method with a template
import os


def create_index_page_if_not_exist(path_to_file):
    filename = path_to_file.split('/')[-1]
    from icecream import ic
    ic(filename)
    ic(os.path.exists(path_to_file))
    if not os.path.exists(path_to_file) and filename == 'index.html':
        """tree -H '.' -L 1 --noreport --charset utf-8 > index.html"""
        ic('we are here')
