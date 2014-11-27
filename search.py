# coding=utf-8
from __future__ import print_function

__author__ = 'Bogdan'

import gzip
import json

def file_bisect ( file_handle, search_term, file_lines_pos, initial_offset )	:
	# bisect
	lo	= 0
	hi	= len ( file_lines_pos ) -1

	while	lo < hi	:
		mid	= ( lo + hi ) // 2

		file_handle.seek ( file_lines_pos [ mid ] + initial_offset )
		mid_v	= file_handle.readline ()

		mid_v, _	= mid_v.split ( b"::", 1 )

		if	mid_v < search_term	:
			lo	= mid +1
		else	:
			hi	= mid

	return	lo

def search ( index_filename, search_term = None )	:

	if	search_term is None	:
		search_term	= "relativ"

	search_term	= bytes ( search_term, "utf-8" )

	with	gzip.open ( index_filename, "rb" )	as file_handle	:

		file_lines_pos	= tuple ( map ( int, file_handle.readline ().split ( b"," ) ))
		initial_offset	= file_handle.tell ()

		articles	= json.loads ( file_handle.readline ().decode () )

		line	= file_bisect ( file_handle, search_term, file_lines_pos, initial_offset )

		file_handle.seek ( file_lines_pos [ line ] + initial_offset )
		keyword, article_ids	= file_handle.readline ().strip ().split ( b"::", 1 )

		while	keyword.startswith ( search_term )	:

			print ( "{}\t: \"{}\"".format ( keyword.decode ()
				, '", "'.join (
					articles.get ( id.decode (), "" )
						for id in article_ids.split ( b"," )
				)
			))

			keyword, article_ids	= file_handle.readline ().strip ().split ( b"::", 1 )


if __name__ == "__main__" :

	import argparse

	parser = argparse.ArgumentParser ( description = 'Command line takes a single term prefix for either a contributor or word that resolves to an article title.' )

	parser.add_argument ( 'search_term', help = 'Search term prefix' )

	parser.add_argument ( '-f', '--file',	default='search_index.gz', help='Search index archive (default: %(default)s)' )

	namespace = parser.parse_args ()

	if	namespace.search_term is not None	and len ( namespace.search_term ) < 4	:
		print ( "Minimum search query length is 4 chars" )
		exit ( 1 )

	search ( namespace.file, namespace.search_term )



