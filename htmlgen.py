import os

template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Contents</title>
</head>
<body>
    <h1>Contents of <span style="color:green">%s</span></h1>
    <p>%s</p>
</body>
</html>
"""


def create_index_page_if_not_exist(path_to_file):
    """ A primitive generator of an index page"""
    def generate_content(raw):
        table_line = "<b>d/-</b> <b>filename</b> <b>size</b><br>"
        lines = [table_line]
        for row in raw:
            row = row.split()
            line = f"{row[0][0]} {row[-1]} {row[-5]}<br>"
            lines.append(line)
        return ''.join(lines)

    filename = path_to_file.split('/')[-1]
    if not os.path.exists(path_to_file) and filename == 'index.html':
        path_to_dir = path_to_file[:-10]  # cut off 'index.html'
        stream = os.popen(f'cd {path_to_dir}; ls -l')
        output = stream.read()
        list_of_files = output.split('\n')[1:-1]
        content = generate_content(list_of_files)

        with open(path_to_file, 'w') as file:
            file.write(template % (path_to_dir, content))

