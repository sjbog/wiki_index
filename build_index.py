# coding=utf-8
from __future__ import print_function

__author__ = 'Bogdan'

import wikiextractor
import io
import re
import bz2, gzip
import json
import xml.etree.ElementTree as ET
from collections import defaultdict, deque

pattern_ending	= re.compile ( r"=\s*(External links|references|see also)\s*=", re.IGNORECASE | re.MULTILINE | re.UNICODE )

def get_all_words ( text, contributor, min_length = 4 )	:
	cleaned_text	= wikiextractor.WikiExtractor.clean ( text )

	ending_match	= pattern_ending.search ( cleaned_text )

	if	ending_match	:
		cleaned_text	= cleaned_text [ : ending_match.end () - len ( ending_match.group ( 0 ) ) -1 ]

	words	= re.split ( r"\W+", cleaned_text )

	# last one is always empty ""
	words [ -1 ]	= contributor

	words	= ( word.lower ()	for word in words	if len ( word ) >= min_length	)

	return	set ( words )


def article_iter ( filename )	:

	with	bz2.open ( filename, "rb" )	as file_handle	:

		for	event, elem	in ET.iterparse ( file_handle, [ "end" ] )	:

			if	elem.tag.endswith ( "page" )	:

				redirect	= elem.find ( "./{http://www.mediawiki.org/xml/export-0.9/}redirect" )
				if	redirect is not None	:
					continue

				id	= elem.findtext ( "./{http://www.mediawiki.org/xml/export-0.9/}id" )
				title	= elem.findtext ( "./{http://www.mediawiki.org/xml/export-0.9/}title" )
				contributor	= elem.findtext ( "./{http://www.mediawiki.org/xml/export-0.9/}revision/{http://www.mediawiki.org/xml/export-0.9/}contributor/*", "" )
				text	= elem.findtext ( "./{http://www.mediawiki.org/xml/export-0.9/}revision/{http://www.mediawiki.org/xml/export-0.9/}text" )

				yield	id, title, contributor, text


def build_index ( articles_filename, output_filename )	:

	with	gzip.open ( output_filename, "wb" )	as file_handle,\
		io.BytesIO ()	as mem_file_handle	:

		articles	= defaultdict ( list )
		keywords	= defaultdict ( list )

		for	id, title, contributor, text	in article_iter ( articles_filename )	:

			for	word in get_all_words ( text, contributor )	:
				keywords [ word ].append ( id )

			articles [ id ]	= title

			# if	len ( articles ) >= 2	:	break


		mem_file_handle.write ( bytes ( json.dumps ( articles ), "utf-8" ) )
		mem_file_handle.write ( b"\n" )


		lines_file_pos	= deque ()

		for	word in sorted ( keywords.keys () )	:

			lines_file_pos.append ( mem_file_handle.tell () )

			mem_file_handle.write (
				bytes ( "{}::{}\n".format ( word, ",".join ( keywords [ word ] ) ), "utf-8" )
			)


		mem_file_handle.seek ( 0, 0 )

		file_handle.write ( bytes ( ",".join ( map ( str, lines_file_pos ) ), "utf-8" ) )
		file_handle.write ( b"\n" )
		file_handle.writelines ( line for line in mem_file_handle )


if __name__ == "__main__" :

	import argparse

	parser = argparse.ArgumentParser ( description = 'Command line builds index file' )

	parser.add_argument ( '-f', '--filename',	default="enwiki-latest-pages-articles4.xml-p000055002p000104998.bz2", help='Input articles dump archive (default: %(default)s)' )
	parser.add_argument ( '-o', '--output_filename',	default="search_index.gz", help='Output index archive (default: %(default)s)' )

	namespace = parser.parse_args ()

	build_index ( namespace.filename, namespace.output_filename )
