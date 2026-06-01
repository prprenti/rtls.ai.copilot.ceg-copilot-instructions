import re
import argparse


class PathExtractor:
    def __init__(self, line):
        self.line = line

    def replace_line_with_ipx(self):
        if '/p/ipx/ipcache2' in self.line:
            new_line = self.line
            matches = list(re.finditer(self.ipcache_regex(), self.line))
            for match in reversed(matches):  # reversed to avoid offset issues
                groups = match.groupdict()
                ipx_key = f"{groups['ipx_name']}@{groups['dot_version']}.{groups['version']}"
                replacement = f"{groups['header']}{{{{ ipx['{ipx_key}'] }}}}{groups['slash_found']}{groups['path_tail']}"
                start, end = match.span()
                new_line = new_line[:start] + replacement + new_line[end:]
            return new_line
        return self.line

    def ipcache_regex(self):
        # some_stuff,/p/ipx/ipcache2/mtlb/fuse_proxy/MTLBA0P10RTL1IFC1V1/2/mtlb.fuse_proxy,more_stuff, and_this
        return (r'(?P<header>[^/,]*)/p/ipx/ipcache2/+(\w+)/+([\w.-]+)/+(?P<version>[\w.-]+)/+(?P<dot_version>[\w.-]+)/+(?P<ipx_name>[\w.-]+)(?P<slash_found>/*)(?P<path_tail>[^,]*)')

    @staticmethod
    def legalize_version(version):
        return version.replace('.', '_')


class FileToIPXConverter:
    def __init__(self, file):
        self.file = file
        self.converted_lines = []
        self.convert()
        self.write_output()

    def read_file(self):
        with open(self.file, 'r') as f:
            return f.readlines()

    def convert(self):
        for line in self.read_file():
            converted_line = PathExtractor(line).replace_line_with_ipx()
            self.converted_lines.append(converted_line)

    def write_output(self):
        output_file = self.file.replace('.list', '.ipx')
        with open(output_file, 'w') as f:
            f.write(''.join(self.converted_lines))
        print(f"Converted file written to {output_file}")


def parse_args():
    header_str = """Parses a Cheetah *.list file and returns a FQN template file"""
    parser = argparse.ArgumentParser(add_help=True,
                                     description=header_str)
    parser.add_argument('-f', '--file',
                        required=True,
                        dest='file',
                        help='Full path to *.list file to parse'
                        )
    return parser.parse_args()


if __name__ == "__main__":
    parsed_args = parse_args()
    FileToIPXConverter(parsed_args.file)
