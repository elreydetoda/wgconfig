#!/usr/bin/env python3

"""wgconfig.py: A class for parsing and writing WireGuard configuration files."""

# The following imports are for Python2 support only
from __future__ import with_statement
from __future__ import absolute_import
from __future__ import print_function
from builtins import str
from builtins import range
from io import open


__author__ = "Dirk Henrici"
__license__ = "AGPL" # + author has right to release in parallel under different licenses
__email__ = "towalink.wgconfig@henrici.name"


import os


class WGConfig():
    """A class for parsing and writing WireGuard configuration files"""
    SECTION_DISABLED = '_disabled'
    SECTION_FIRSTLINE = '_index_firstline'
    SECTION_LASTLINE = '_index_lastline'
    SECTION_RAW = '_rawdata'
    _interface = None # interface attributes
    _peers = None # peer data

    def __init__(self, file=None, keyattr='PublicKey'):
        """Object initialization"""
        self.filename = self.file2filename(file)
        self.keyattr = keyattr
        self.lines = []
        self.initialize_file()

    @staticmethod
    def file2filename(file):
        """Handle special filenames: 'wg0' and 'wg0.conf' become '/etc/wireguard/wg0.conf' """
        if file is None:
            return None
        if os.path.basename(file) == file:
            if not file.endswith('.conf'):
                file += '.conf'
            file = os.path.join('/etc/wireguard', file)
        return file

    def invalidate_data(self):
        """Clears the data structs"""
        self._interface = None
        self._peers = None

    def read_from_fileobj(self, fobj):
        """Reads from the given file object into memory"""
        self.lines = [line.rstrip() for line in fobj.readlines()]
        self.invalidate_data()

    def write_to_fileobj(self, fobj):
        """Writes from memory to the given file object"""
        fobj.writelines(line + '\n' for line in self.lines)

    def read_file(self):
        """Reads the WireGuard config file into memory"""
        if self.filename is None:
            raise ValueError('A filename needs to be provided on object creation')
        with open(self.filename, 'r') as wgfile:
            self.read_from_fileobj(wgfile)

    def write_file(self, file=None):
        """Writes a WireGuard config file from memory to file"""
        if file is None:
            filename = self.filename
        else:
            filename = self.file2filename(file)
        if filename is None:
            raise ValueError('A filename needs to be provided')
        with os.fdopen(os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o640), 'w') as wgfile:
            self.write_to_fileobj(wgfile)

    @staticmethod
    def parse_line(line):
        """Splits a single attr/value line into its parts"""
        attr, _, value = line.partition('=')
        attr = attr.strip()
        parts = value.partition('#')
        value = parts[0].strip() # strip comments and whitespace
        value = str(value) # this line is for Python2 support only
        comment = parts[1] + parts[2]
        if value.isnumeric():
            value = [int(value)]
        else:
            value = [item.strip() for item in value.split(',')] # decompose into list based on commata as separator
        return attr, value, comment

    def parse_lines(self):
        """Parses the lines of a WireGuard config file into memory"""

        # There will be two special attributes in the parsed data:
        #_index_firstline: Line (zero indexed) of the section header (including any leading lines with comments)
        #_index_lastline: Line (zero indexed) of the last attribute line of the section (including any directly following comments)

        def close_section(section, section_data):
            section_data = {k: (v if len(v) > 1 else v[0]) for k, v in section_data.items()}
            if section is None: # nothing to close on first section
                return
            elif section == 'interface': # close interface section
                self._interface = section_data
            else: # close peer section
                peername = section_data.get(self.keyattr)
                self._peers[peername] = section_data
            section_data[self.SECTION_RAW] = self.lines[section_data[self.SECTION_FIRSTLINE]:(section_data[self.SECTION_LASTLINE] + 1)]
            # Checking if the section is disabled and adding an attribute to section data
            if section_data[self.SECTION_RAW][0].startswith('#! '):
                section_data[self.SECTION_DISABLED] = True
            else:
                section_data[self.SECTION_DISABLED] = False

        self._interface = dict()
        self._peers = dict()
        section = None
        section_data = dict()
        last_empty_line_in_section = -1 # virtual empty line before start of file
        for i, line in enumerate(self.lines):
            # Ignore leading whitespace and trailing whitespace
            line = line.replace('#! ', '').strip()
            # Ignore empty lines and comments
            if len(line) == 0:
                last_empty_line_in_section = i
                continue
            if line.startswith('['): # section
                if last_empty_line_in_section is not None:
                    section_data[self.SECTION_LASTLINE] = [last_empty_line_in_section - 1]
                close_section(section, section_data)
                section_data = dict()
                section = line[1:].partition(']')[0].lower()
                if last_empty_line_in_section is None:
                    section_data[self.SECTION_FIRSTLINE] = [i]
                else:
                    section_data[self.SECTION_FIRSTLINE] = [last_empty_line_in_section + 1]
                    last_empty_line_in_section = None
                section_data[self.SECTION_LASTLINE] = [i]
                if not section in ['interface', 'peer']:
                    raise ValueError('Unsupported section [{0}] in line {1}'.format(section, i))
            elif line.startswith('#'):
                section_data[self.SECTION_LASTLINE] = [i]
            else: # regular line
                attr, value, _comment = self.parse_line(line)
                section_data[attr] = section_data.get(attr, [])
                section_data[attr].extend(value)
                section_data[self.SECTION_LASTLINE] = [i]
        close_section(section, section_data)

    def handle_leading_comment(self, leading_comment):
        """Appends a leading comment for a section"""
        if leading_comment is not None:
            if leading_comment.strip()[0] != '#':
                raise ValueError('A comment needs to start with a "#"')
            self.lines.append(leading_comment)

    def initialize_file(self, leading_comment=None):
        """Empties the file and adds the interface section header"""
        self.lines = list()
        self.handle_leading_comment(leading_comment) # add leading comment if needed
        self.lines.append('[Interface]')
        self.invalidate_data()

    def get_filtered_dictionary(self, data, include_details=False):
        """Return a separated copy of a dictionary and filter private attributes if requested"""
        if include_details:
            # Obtain a copy of the complete dictionary
            data = data.copy()
        else:
            # Filter attributes starting with an underscore
            data = { key: value for key, value in data.items() if not key.startswith('_') }
        return data    

    def get_interface(self, include_details=False):
        """Returns the data of the interface section"""
        return self.get_filtered_dictionary(self.interface, include_details)

    def get_peers(self, keys_only=True, include_disabled=False, include_details=False):
        """Returns peer data or a list of peers (i.e. their public keys)"""
        # Get (possibly) filtered peers dictionary
        peerdata = { key: value for key, value in self.peers.items() if include_disabled or not value.get('_disabled', False) }
        # Return requested data
        if keys_only:
            return list(peerdata.keys())
        else:
            return { key: self.get_filtered_dictionary(value, include_details) for key, value in peerdata.items() }

    def get_peer(self, key, include_details=False):
        """Returns the data of the peer with the given (public) key"""
        try:
            peerdata = self.peers[key]
        except KeyError:
            raise KeyError('The peer does not exist')
        return self.get_filtered_dictionary(peerdata, include_details)

    def add_peer(self, key, leading_comment=None):
        """Adds a new peer with the given (public) key"""
        if key in self.peers:
            raise KeyError('Peer to be added already exists')
        self.lines.append('') # append an empty line for separation
        self.handle_leading_comment(leading_comment) # add leading comment if needed
        # Append peer with key attribute
        self.lines.append('[Peer]')
        self.lines.append('{0} = {1}'.format(self.keyattr, key))
        # Invalidate data cache
        self.invalidate_data()

    def del_peer(self, key):
        """Removes the peer with the given (public) key"""
        if not key in self.peers:
            raise KeyError('The peer to be deleted does not exist')
        section_firstline = self.peers[key][self.SECTION_FIRSTLINE]
        section_lastline = self.peers[key][self.SECTION_LASTLINE]
        # Remove a blank line directly before the peer section
        if section_firstline > 0:
            if len(self.lines[section_firstline - 1]) == 0:
                section_firstline -= 1
        # Only keep needed lines
        result = []
        if section_firstline > 0:
            result.extend(self.lines[0:section_firstline])
        result.extend(self.lines[(section_lastline + 1):])
        self.lines = result
        # Invalidate data cache
        self.invalidate_data()

    def get_sectioninfo(self, key):
        """Get first and last line of the section identified by the given key ("None" for interface section)"""
        if key is None: # interface
            section_firstline = self.interface[self.SECTION_FIRSTLINE]
            section_lastline = self.interface[self.SECTION_LASTLINE]
        else: # peer
            if not key in self.peers:
                raise KeyError('The specified peer does not exist')
            section_firstline = self.peers[key][self.SECTION_FIRSTLINE]
            section_lastline = self.peers[key][self.SECTION_LASTLINE]
        return section_firstline, section_lastline

    def add_attr(self, key, attr, value, leading_comment=None, append_as_line=False):
        """Adds an attribute/value pair to the given peer ("None" for adding an interface attribute)"""
        section_firstline, section_lastline = self.get_sectioninfo(key)
        if leading_comment is not None:
            if leading_comment.strip()[0] != '#':
                raise ValueError('A comment needs to start with a "#"')
        # Look for line with the attribute
        line_found = None
        for i in range(section_firstline + 1, section_lastline + 1):
            line_attr, line_value, line_comment = self.parse_line(self.lines[i])
            if attr == line_attr:
                line_found = i
        # Add the attribute at the right place
        if (line_found is None) or append_as_line:
            line_found = section_lastline if (line_found is None) else line_found
            line_found += 1
            self.lines.insert(line_found, '{0} = {1}'.format(attr, value))
        else:
            line_attr, line_value, line_comment = self.parse_line(self.lines[line_found])
            line_value.append(value)
            if len(line_comment) > 0:
                line_comment = ' ' + line_comment
            line_value = [str(item) for item in line_value]
            self.lines[line_found] = line_attr + ' = ' + ', '.join(line_value) + line_comment
        # Handle leading comments
        if leading_comment is not None:
            self.lines.insert(line_found, leading_comment)
        # Invalidate data cache
        self.invalidate_data()

    def del_attr(self, key, attr, value=None, remove_leading_comments=True):
        """Removes an attribute/value pair from the given peer ("None" for removing an interface attribute); set 'value' to 'None' to remove all values"""
        section_firstline, section_lastline = self.get_sectioninfo(key)
        # Find all lines with matching attribute name and (if requested) value
        line_found = []
        for i in range(section_firstline + 1, section_lastline + 1):
            line_attr, line_value, line_comment = self.parse_line(self.lines[i])
            if attr == line_attr:
                if (value is None) or (value in line_value):
                    line_found.append(i)
        if len(line_found) == 0:
            raise ValueError('The attribute/value to be deleted is not present')
        # Process all relevant lines
        for i in reversed(line_found): # reversed so that non-processed indices stay valid
            if value is None:
                del(self.lines[i])
            else:
                line_attr, line_value, line_comment = self.parse_line(self.lines[i])
                line_value.remove(value)
                if len(line_value) > 0: # keep remaining values in that line
                    self.lines[i] = line_attr + ' = ' + ', '.join(line_value) + line_comment
                else: # otherwise line is no longer needed
                    del(self.lines[i])
        # Handle leading comments
        if remove_leading_comments:
            i = line_found[0] - 1
            while i > 0:
                if len(self.lines[i]) and (self.lines[i][0] == '#'):
                    del(self.lines[i])
                    i -= 1
                else:
                    break
        # Invalidate data cache
        self.invalidate_data()

    def get_peer_enabled(self, key):
        """Checks whether the peer with the given (public) key is enabled"""
        peerdata = self.get_peer(key, include_details=True)
        return not peerdata.get(self.SECTION_DISABLED)

    def enable_peer(self, key):
        """Enables the peer with the given (public) key by removing #! from all lines in a peer section"""
        if key not in self.peers:
            raise KeyError('The peer to be enabled does not exist')
        section_firstline = self.peers[key][self.SECTION_FIRSTLINE]
        section_lastline = self.peers[key][self.SECTION_LASTLINE]
        result = []
        # Remove #! from lines
        for i, line in enumerate(self.lines):
            if section_firstline <= i <= section_lastline:
                line = line.replace('#! ', '')
            result.append(line)
        self.lines = result
        # Invalidate data cache
        self.invalidate_data()

    def disable_peer(self, key):
        """Disables the peer with the given (public) key by appending #! to all lines in a peer section"""
        if key not in self.peers:
            raise KeyError('The peer to be disabled does not exist')
        if not self.get_peer_enabled(key):
            return; # nothing to do anymore if peer is already disabled
        section_firstline = self.peers[key][self.SECTION_FIRSTLINE]
        section_lastline = self.peers[key][self.SECTION_LASTLINE]
        result = []
        # Append #! to lines
        for i, line in enumerate(self.lines):
            prefix = ''
            if section_firstline <= i <= section_lastline:
                prefix = '#! '
            result.append(prefix + line)
        self.lines = result
        # Invalidate data cache
        self.invalidate_data()

    @property
    def interface(self):
        """Dictionary with interface attributes"""
        if self._interface is None:
            self.parse_lines()
        return self._interface

    @property
    def peers(self):
        """Dictionary with peer data"""
        if self._peers is None:
            self.parse_lines()
        return self._peers


def main():
    """Main function"""
    print('This is a library to be imported into your applications.')


if __name__ == "__main__":
    main()
