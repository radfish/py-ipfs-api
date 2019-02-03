# -*- coding: utf-8 -*-
from __future__ import absolute_import

from . import base

from .. import multipart


class Section(base.SectionBase):
	"""
	Functions used to manage files in IPFS's virtual “Mutable File System” (MFS)
	file storage space.
	"""

	def cp(self, source, dest, **kwargs):
		"""Copies files within the MFS.

		Due to the nature of IPFS this will not actually involve any of the
		file's content being copied.

		.. code-block:: python

			>>> client.files.ls("/")
			{'Entries': [
				{'Size': 0, 'Hash': '', 'Name': 'Software', 'Type': 0},
				{'Size': 0, 'Hash': '', 'Name': 'test', 'Type': 0}
			]}
			>>> client.files.cp("/test", "/bla")
			''
			>>> client.files.ls("/")
			{'Entries': [
				{'Size': 0, 'Hash': '', 'Name': 'Software', 'Type': 0},
				{'Size': 0, 'Hash': '', 'Name': 'bla', 'Type': 0},
				{'Size': 0, 'Hash': '', 'Name': 'test', 'Type': 0}
			]}

		Parameters
		----------
		source : str
			Filepath within the MFS to copy from
		dest : str
			Destination filepath with the MFS to which the file will be
			copied to
		"""
		args = (source, dest)
		return self._client.request('/files/cp', args, **kwargs)


	#TODO: Add `flush(path="/")`


	def ls(self, path, **kwargs):
		"""Lists contents of a directory in the MFS.

		.. code-block:: python

			>>> client.files.ls("/")
			{'Entries': [
				{'Size': 0, 'Hash': '', 'Name': 'Software', 'Type': 0}
			]}

		Parameters
		----------
		path : str
			Filepath within the MFS

		Returns
		-------
			dict : Directory entries
		"""
		args = (path,)
		return self._client.request('/files/ls', args, decoder='json', **kwargs)


	def mkdir(self, path, parents=False, **kwargs):
		"""Creates a directory within the MFS.

		.. code-block:: python

			>>> client.files.mkdir("/test")
			b''

		Parameters
		----------
		path : str
			Filepath within the MFS
		parents : bool
			Create parent directories as needed and do not raise an exception
			if the requested directory already exists
		"""
		kwargs.setdefault("opts", {"parents": parents})

		args = (path,)
		return self._client.request('/files/mkdir', args, **kwargs)


	def mv(self, source, dest, **kwargs):
		"""Moves files and directories within the MFS.

		.. code-block:: python

			>>> client.files.mv("/test/file", "/bla/file")
			b''

		Parameters
		----------
		source : str
			Existing filepath within the MFS
		dest : str
			Destination to which the file will be moved in the MFS
		"""
		args = (source, dest)
		return self._client.request('/files/mv', args, **kwargs)


	def read(self, path, offset=0, count=None, **kwargs):
		"""Reads a file stored in the MFS.

		.. code-block:: python

			>>> client.files.read("/bla/file")
			b'hi'

		Parameters
		----------
		path : str
			Filepath within the MFS
		offset : int
			Byte offset at which to begin reading at
		count : int
			Maximum number of bytes to read

		Returns
		-------
			str : MFS file contents
		"""
		opts = {"offset": offset}
		if count is not None:
			opts["count"] = count
		kwargs.setdefault("opts", opts)

		args = (path,)
		return self._client.request('/files/read', args, **kwargs)


	def rm(self, path, recursive=False, **kwargs):
		"""Removes a file from the MFS.

		.. code-block:: python

			>>> client.files.rm("/bla/file")
			b''

		Parameters
		----------
		path : str
			Filepath within the MFS
		recursive : bool
			Recursively remove directories?
		"""
		kwargs.setdefault("opts", {"recursive": recursive})

		args = (path,)
		return self._client.request('/files/rm', args, **kwargs)


	def stat(self, path, **kwargs):
		"""Returns basic ``stat`` information for an MFS file
		(including its hash).

		.. code-block:: python

			>>> client.files.stat("/test")
			{'Hash': 'QmUNLLsPACCz1vLxQVkXqqLX5R1X345qqfHbsf67hvA3Nn',
			 'Size': 0, 'CumulativeSize': 4, 'Type': 'directory', 'Blocks': 0}

		Parameters
		----------
		path : str
			Filepath within the MFS

		Returns
		-------
			dict : MFS file information
		"""
		args = (path,)
		return self._client.request('/files/stat', args, decoder='json', **kwargs)


	def write(self, path, file, offset=0, create=False, truncate=False, count=None, **kwargs):
		"""Writes to a mutable file in the MFS.

		.. code-block:: python

			>>> client.files.write("/test/file", io.BytesIO(b"hi"), create=True)
			b''

		Parameters
		----------
		path : str
			Filepath within the MFS
		file : io.RawIOBase
			IO stream object with data that should be written
		offset : int
			Byte offset at which to begin writing at
		create : bool
			Create the file if it does not exist
		truncate : bool
			Truncate the file to size zero before writing
		count : int
			Maximum number of bytes to read from the source ``file``
		"""
		opts = {"offset": offset, "create": create, "truncate": truncate}
		if count is not None:
			opts["count"] = count
		kwargs.setdefault("opts", opts)

		args = (path,)
		body, headers = multipart.stream_files(file, self.chunk_size)
		return self._client.request('/files/write', args, data=body, headers=headers, **kwargs)


class Base(base.ClientBase):
	files = base.SectionProperty(Section)


	def add(self, files, recursive=False, pattern='**', *args, **kwargs):
		"""Add a file, or directory of files to IPFS.

		.. code-block:: python

			>>> with io.open('nurseryrhyme.txt', 'w', encoding='utf-8') as f:
			...	 numbytes = f.write('Mary had a little lamb')
			>>> client.add('nurseryrhyme.txt')
			{'Hash': 'QmZfF6C9j4VtoCsTp4KSrhYH47QMd3DNXVZBKaxJdhaPab',
			 'Name': 'nurseryrhyme.txt'}

		Parameters
		----------
		files : str
			A filepath to either a file or directory
		recursive : bool
			Controls if files in subdirectories are added or not
		pattern : str | list
			Single `*glob* <https://docs.python.org/3/library/glob.html>`_
			pattern or list of *glob* patterns and compiled regular expressions
			to match the names of the filepaths to keep
		trickle : bool
			Use trickle-dag format (optimized for streaming) when generating
			the dag; see `the FAQ <https://github.com/ipfs/faq/issues/218>` for
			more information (Default: ``False``)
		only_hash : bool
			Only chunk and hash, but do not write to disk (Default: ``False``)
		wrap_with_directory : bool
			Wrap files with a directory object to preserve their filename
			(Default: ``False``)
		chunker : str
			The chunking algorithm to use
		pin : bool
			Pin this object when adding (Default: ``True``)
		nocopy : bool
			Add the file using filestore. Implies raw-leaves. (experimental).
			(Default: ``False``)

		Returns
		-------
			dict: File name and hash of the added file node
		"""
		#PY2: No support for kw-only parameters after glob parameters
		opts = {
			"trickle": kwargs.pop("trickle", False),
			"only-hash": kwargs.pop("only_hash", False),
			"wrap-with-directory": kwargs.pop("wrap_with_directory", False),
			"pin": kwargs.pop("pin", True),
			'nocopy': kwargs.pop("nocopy", False)
		}
		if "chunker" in kwargs:
			opts["chunker"] = kwargs.pop("chunker")
		kwargs.setdefault("opts", opts)

		body, headers = multipart.stream_filesystem_node(
			files, recursive, pattern, self.chunk_size
		)
		return self._client.request('/add', decoder='json', data=body, headers=headers, **kwargs)


	def file_ls(self, multihash, **kwargs):
		"""Lists directory contents for Unix filesystem objects.

		The result contains size information. For files, the child size is the
		total size of the file contents. For directories, the child size is the
		IPFS link size.

		The path can be a prefixless reference; in this case, it is assumed
		that it is an ``/ipfs/`` reference and not ``/ipns/``.

		.. code-block:: python

			>>> client.file_ls('QmTkzDwWqPbnAh5YiV5VwcTLnGdwSNsNTn2aDxdXBFca7D')
			{
				'Arguments': {'QmTkzDwWqPbnAh5YiV5VwcTLnGdwSNsNTn2aDxdXBFca7D':
				              'QmTkzDwWqPbnAh5YiV5VwcTLnGdwSNsNTn2aDxdXBFca7D'},
				'Objects': {
					'QmTkzDwWqPbnAh5YiV5VwcTLnGdwSNsNTn2aDxdXBFca7D': {
						'Hash': 'QmTkzDwWqPbnAh5YiV5VwcTLnGdwSNsNTn2aDxdXBFca7D',
						'Size': 0, 'Type': 'Directory',
						'Links': [
							{'Hash': 'Qmd2xkBfEwEs9oMTk77A6jrsgurpF3ugXSg7dtPNFkcNMV',
							 'Name': 'Makefile', 'Size': 163,    'Type': 'File'},
							{'Hash': 'QmeKozNssnkJ4NcyRidYgDY2jfRZqVEoRGfipkgath71bX',
							 'Name': 'example',  'Size': 1463,   'Type': 'File'},
							{'Hash': 'QmZAL3oHMQYqsV61tGvoAVtQLs1WzRe1zkkamv9qxqnDuK',
							 'Name': 'home',     'Size': 3947,   'Type': 'Directory'},
							{'Hash': 'QmZNPyKVriMsZwJSNXeQtVQSNU4v4KEKGUQaMT61LPahso',
							 'Name': 'lib',      'Size': 268261, 'Type': 'Directory'},
							{'Hash': 'QmSY8RfVntt3VdxWppv9w5hWgNrE31uctgTiYwKir8eXJY',
							 'Name': 'published-version', 'Size': 47, 'Type': 'File'}
						]
					}
				}
			}

		Parameters
		----------
		multihash : str
			The path to the object(s) to list links from

		Returns
		-------
			dict
		"""
		args = (multihash,)
		return self._client.request('/file/ls', args, decoder='json', **kwargs)


	def get(self, multihash, **kwargs):
		"""Downloads a file, or directory of files from IPFS.

		Files are placed in the current working directory.

		Parameters
		----------
		multihash : str
			The path to the IPFS object(s) to be outputted
		"""
		args = (multihash,)
		return self._client.download('/get', args, **kwargs)


	def cat(self, multihash, offset=0, length=-1, **kwargs):
		r"""Retrieves the contents of a file identified by hash.

		.. code-block:: python

			>>> client.cat('QmTkzDwWqPbnAh5YiV5VwcTLnGdwSNsNTn2aDxdXBFca7D')
			Traceback (most recent call last):
			  ...
			ipfsapi.exceptions.Error: this dag node is a directory
			>>> client.cat('QmeKozNssnkJ4NcyRidYgDY2jfRZqVEoRGfipkgath71bX')
			b'<!DOCTYPE html>\n<html>\n\n<head>\n<title>ipfs example viewer</…'

		Parameters
		----------
		multihash : str
			The path to the IPFS object(s) to be retrieved
		offset : int
			Byte offset to begin reading from
		length : int
			Maximum number of bytes to read(-1 for all)

		Returns
		-------
			str : File contents
		"""
		args = (multihash,)
		opts = {}
		if offset != 0:
			opts['offset'] = offset
		if length != -1:
			opts['length'] = length
		kwargs.setdefault('opts', opts)
		return self._client.request('/cat', args, **kwargs)


	def ls(self, multihash, **kwargs):
		"""Returns a list of objects linked to by the given hash.

		.. code-block:: python

			>>> client.ls('QmTkzDwWqPbnAh5YiV5VwcTLnGdwSNsNTn2aDxdXBFca7D')
			{'Objects': [
				{'Hash': 'QmTkzDwWqPbnAh5YiV5VwcTLnGdwSNsNTn2aDxdXBFca7D',
					'Links': [
						{'Hash': 'Qmd2xkBfEwEs9oMTk77A6jrsgurpF3ugXSg7dtPNFkcNMV',
						 'Name': 'Makefile',          'Size': 174, 'Type': 2},
						…
						{'Hash': 'QmSY8RfVntt3VdxWppv9w5hWgNrE31uctgTiYwKir8eXJY',
						 'Name': 'published-version', 'Size': 55,  'Type': 2}
					]
				}
			]}

		Parameters
		----------
		multihash : str
			The path to the IPFS object(s) to list links from

		Returns
		-------
			dict : Directory information and contents
		"""
		args = (multihash,)
		return self._client.request('/ls', args, decoder='json', **kwargs)