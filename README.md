# wgconfig

Parsing and writing WireGuard configuration files (comment preserving)

WireGuard config files are ini-style. Since all "Peer" sections have the same name, these files cannot be parsed and modified by most libraries handling configuration files. Most existing libraries are not able to preserve or even add comments when modifying a config file. "wgconfig" was created to work with WireGuard configuration files and to preserve comments.

---

## Features

- Read and parse WireGuard configuration files and make the data available as Python dictionaries.
- Create new WireGuard configuration files.
- Add peers to WireGuard configuration files and delete peers from WireGuard configuration files.
- Save and clone WireGuard configuration files.
- Comments are preserved when reading and writing WireGuard configuration files.
- Leading comments may be added when creating sections or attributes.
- Such comments may be deleted when removing sections or attributes.
- No other libraries are needed, i.e. no dependencies.

---

## Installation

Install using PyPi:

```shell
pip3 install wgconfig
```

### Package for Debian Linux

Download the provided Debian package (in the desired version) and install it:

```shell
dpkg -i python3-wgconfig_1.0.2-1_all.deb
```

### Package for Alpine Linux

You may install the Alpine package (https://pkgs.alpinelinux.org/packages?name=py3-wgconfig) from Alpine's testing repository:

```shell
apk add wgconfig@testing
```

Note that a line like `@testing https://dl-cdn.alpinelinux.org/alpine/edge/testing` needs to be present in `/etc/apk/repositories` to make the testing repository available.

---

## Quickstart

### Reading and parsing an existing WireGuard configuration file

Read and parse the existing WireGuard configuration file 'wg0.conf' located in '/etc/wireguard':

```python
import wgconfig
wc = wgconfig.WGConfig('wg0')
wc.read_file()
print('INTERFACE DATA:', wc.get_interface())
print('LIST OF PEERS:', wc.get_peers())
print('ALL PEER DATA:', wc.get_peers(keys_only=False))
```

Add a new peer with a comment line before the peer section:
```python
wc.add_peer('801mgm2JhjTOCxfihEknzFJGYxDvi+8oVYBrWe3hOWM=', '# Newly added peer')
```

Add an attribute to that peer:
```python
wc.add_attr('801mgm2JhjTOCxfihEknzFJGYxDvi+8oVYBrWe3hOWM=', 'Endpoint', 'wg.example.com:51820', '# Added for demonstration purposes')
```

Write the changes to disk. Comments that were present when reading the file are preserved.
```python
wc.write_file()
```

Please see below for more detailed usage information.

### Creating a new WireGuard configuration file

Create a new WireGuard configuration file as '/root/wgtest.conf':

```python
import wgconfig
wc = wgconfig.WGConfig('/root/wgtest.conf')
# Add attribute to Interface section (denoted by 'None')
wc.add_attr(None, 'PrivateKey', '6FYKQKEtGFAb5HSwyj5cQl3wgS1E9d6SqVjdVksOn2s=')
# Save to disk
wc.write_file()
# Access the data
print('INTERFACE DATA:', wc.get_interface())
print('LIST OF PEERS (there are no peers yet):', wc.get_peers())
print('ALL PEER DATA (there are no peers yet):', wc.get_peers(keys_only=False))
```

The module also contains simple wrappers around the wg command (contained in WireGuard tools) to generate and manage keys:

```python
import wgconfig.wgexec as wgexec
# Create a new WireGuard private key
private_key = wgexec.generate_privatekey()
```

More information and examples can be found here:

- [Detailed example for reading WireGuard config files](https://github.com/towalink/wgconfig/blob/master/doc/example_notebook_1.md)
- Please see the section below for detailed API description.

---

## Detailed API description

### Properties

#### interface

*Returns attributes and values (including wgconfig-internal ones) of the Interface section as a dictionary*

Notes:
* You might want to use the more flexible `get_interface()` method (see further below) instead.

#### peers

*Returns attributes and values (including wgconfig-internal ones) of all peers as a nested dictionary*

Notes:
* You might want to use the more flexible `get_peers()` method (see further below) instead.

### Methods for interaction

#### `__init__(file)`

*Initializes the instance*

Parameters:
* "file" (str): Path of the WireGuard configuration file
    You may also just provide the interface name. In this case, the path '/etc/wireguard' is assumed along with a file extension '.conf'.

Examples:
* `wc = wgconfig.WGConfig('wg0')`
* `wc = wgconfig.WGConfig('/etc/wireguard/wg0.conf')`

#### `read_file()`

*Reads the WireGuard config file from disk into memory*
        
#### `write_file(file)`

*Writes a WireGuard config file from memory to file*
      
Parameters:
* "file" (str, optional, default: None): Path of the WireGuard configuration file
    You may also just provide the interface name. In this case the path '/etc/wireguard' is assumed along with a file extension '.conf'.
    In case the parameter is missing, the config file defined on object initialization is used.

Examples:
* `wc.write_file()`
* `wc.write_file('wg0')`
* `wc.write_file('/etc/wireguard/wg0.conf')`

#### `initialize_file(leading_comment)`

*Empties the file and adds the interface section header*

Parameters:
* "leading_comment" (str, optional, default: None): Comment line to be added before the Interface section. Must start with a '#' to indicate a comment.

Examples:
* `wc.initialize_file()`
* `wc.initialize_file('# Here comes the Interface section:')`

#### `get_interface(include_details)`

*Returns a dictionary of the attributes and values of the interface section*

Parameters:
* "include_details" (boolean, optional, default: False): Also include attributes with a leading underscore (e.g. the disabled state or the raw data).

Examples:
* `ifdata = wc.get_interface()`

#### `get_peers(keys_only, include_disabled, include_details)`

*Returns a list of peers or - if selected - a dictionary including peers' data*

Parameters:
* "keys_only" (boolean, optional, default: True): Return only the public keys as a list or return keys and corresponding data as a dictionary.
* "include_disabled" (boolean, optional, default: False): Also return data of disabled peers.
* "include_details" (boolean, optional, default: False): Also include attributes with a leading underscore (e.g. the disabled state or the raw data).

Examples:
* `peers = wc.get_peers()`
* `peerdata = wc.get_peers(keys_only=False)`

#### `get_peer(key, include_details)`

*Returns the data of the peer with the given (public) key*

Parameters:
* "key" (str): Public key of the peer
* "include_details" (boolean, optional, default: False): Also include attributes with a leading underscore (e.g. the disabled state or the raw data).

Examples:
* `peerdata = wc.get_peer('801mgm2JhjTOCxfihEknzFJGYxDvi+8oVYBrWe3hOWM=')`
* `peerdata = wc.get_peer('801mgm2JhjTOCxfihEknzFJGYxDvi+8oVYBrWe3hOWM=', include_details=True)`

Notes:
* Don't forget to call `read_file()` before attempting to get data out of a file
* Access the `peers` property if you want to retrieve the data of all peers    

#### `add_peer(key, leading_comment)`

*Adds a new peer with the given (public) key*

Parameters:
* "key" (str): Public key of the new peer
* "leading_comment" (str, optional, default: None): Comment line to be added before the Peer section. Must start with a '#' to indicate a comment.

Examples:
* `wc.add_peer('801mgm2JhjTOCxfihEknzFJGYxDvi+8oVYBrWe3hOWM=')`
* `wc.add_peer('801mgm2JhjTOCxfihEknzFJGYxDvi+8oVYBrWe3hOWM=', '# Here comes the Interface section:')`

#### `del_peer(key)`

*Removes the peer with the given (public) key*

Note: Comment lines immediately before the Peer section are removed, too.

Parameters:
* "key" (str): Public key of the peer

Examples:
* `wc.del_peer('801mgm2JhjTOCxfihEknzFJGYxDvi+8oVYBrWe3hOWM=')`

#### `add_attr(key, attr, value, leading_comment, append_as_line)`

*Adds an attribute/value pair to the given peer ('None' for adding an interface attribute)*

Parameters:
* "key" (str): Key of the peer. Set to 'None' to denote the Interface section
* "attr" (str) Name of the attribute to add
* "value" (str or int) Value of the attribute to add
* "leading_comment" (str, optional, default: None): Comment line to be added before the Peer section. Must start with a '#' to indicate a comment.
* "append_as_line" (bool, optional, default: False): Whether to add the attribute as a new line if another attribute with the same name already exists. If "False", adding an attribute that already exists results in comma-separated attribute values. This way, "AllowedIPs" can be added one by one.

Examples:
* `wc.add_attr(None, 'ListenPort', '51820')`
* `wc.add_attr('801mgm2JhjTOCxfihEknzFJGYxDvi+8oVYBrWe3hOWM=', 'AllowedIPs', '0.0.0.0/0')`
* `wc.add_attr('801mgm2JhjTOCxfihEknzFJGYxDvi+8oVYBrWe3hOWM=', 'AllowedIPs', '0.0.0.0/0', '# Allow all IPv4 addresses', append_as_line=True)`

#### `del_attr(self, key, attr, value, remove_leading_comments)`

*Removes an attribute/value pair from the given peer ('None' for adding an interface attribute); set 'value' to 'None' to remove all values*

Parameters:
* "key" (str): Key of the peer. Set to 'None' to denote the Interface section
* "attr" (str) Name of the attribute to remove
* "value" (str or int, optional, default: None) Value of the attribute to remove
    Set to 'None' if all values (either comma-separated or is multiple attribute lines) shall be removed. Otherwise specify the specific value to be removed.
* "remove_leading_comments" (bool, optional, default: True): Indicates whether comment lines before the attribute line(s) shall be removed, too

Examples:
* `wc.del_attr(None, 'ListenPort')`
* `wc.del_attr('801mgm2JhjTOCxfihEknzFJGYxDvi+8oVYBrWe3hOWM=', 'AllowedIPs')`
* `wc.del_attr('801mgm2JhjTOCxfihEknzFJGYxDvi+8oVYBrWe3hOWM=', 'AllowedIPs', '0.0.0.0/0')`
* `wc.del_attr('801mgm2JhjTOCxfihEknzFJGYxDvi+8oVYBrWe3hOWM=', 'AllowedIPs', '0.0.0.0/0', remove_leading_comments=False)`

#### `disable_peer(self, key)`

*Disables the peer with the given (public) key by prepending `#!` to all lines in a peer section*

Parameters:
* "key" (str): Public key of the peer

Examples:
* `wc.disable_peer('801mgm2JhjTOCxfihEknzFJGYxDvi+8oVYBrWe3hOWM=')`

#### `enable_peer(self, key)`

*Enables the peer with the given (public) key by removing `#!` from all lines in a peer section*

Parameters:
* "key" (str): Public key of the peer

Examples:
* `wc.enable_peer('801mgm2JhjTOCxfihEknzFJGYxDvi+8oVYBrWe3hOWM=')`

#### `get_peer_enabled(self, key)`

*Checks whether the peer with the given (public) key is enabled*

Parameters:
* "key" (str): Public key of the peer

Examples:
* `wc.get_peer_enabled('801mgm2JhjTOCxfihEknzFJGYxDvi+8oVYBrWe3hOWM=')`

#### `read_from_fileobj(fobj)`

*Reads the WireGuard config file from a file object (e.g. StringIO) into memory*

Note: This reads from the current file position (from the beginning ofter regular opening; or as set with `seek`) until the end of file.

Parameters:
* "fobj" (str): File-like object

Examples:
* see examples/stringio.py
        
#### `write_to_fileobj(fobj)`

*Writes a WireGuard config file from memory to a file-like object*
      
Parameters:
* "fobj" (str): File-like object

Examples:
* see examples/stringio.py

---

## Reporting bugs

In case you encounter any bugs, please report the expected behavior and the actual behavior so that the issue can be reproduced and fixed.

---
## Developers

### Clone repository

Clone this repo to your local machine using `https://github.com/towalink/wgconfig.git`

Install the module temporarily to make it available in your Python installation:
```shell
pip3 install -e <path to root of "src" directory>
```

### Run unit tests

Call "pytest" to run the unit tests:
```shell
pytest <path to root of "test" directory>
```

---

## License

[![License](http://img.shields.io/:license-agpl3-blue.svg?style=flat-square)](https://opensource.org/licenses/AGPL-3.0)

- **[AGPL3 license](https://opensource.org/licenses/AGPL-3.0)**
- Copyright 2020-2025 © <a href="https://github.com/towalink/wgconfig" target="_blank">Dirk Henrici</a>.
- [WireGuard](https://www.wireguard.com/) is a registered trademark of Jason A. Donenfeld.
