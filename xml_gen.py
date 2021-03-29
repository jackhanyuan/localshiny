#!/usr/bin/python3
# -*- coding:utf-8 -*-

from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from xml.etree.ElementTree import ElementTree
import os
from datetime import datetime

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static/package')
HOST = 'http://www.findn.cn:5000'


# Return a pretty-printed version of the xml
def indent(elem, level=0):
	i = "\n" + level * "  "
	if len(elem):
		if not elem.text or not elem.text.strip():
			elem.text = i + "  "
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
		for elem in elem:
			indent(elem, level + 1)
		if not elem.tail or not elem.tail.strip():
			elem.tail = i
	else:
		if level and (not elem.tail or not elem.tail.strip()):
			elem.tail = i


# generate xml
def generate_xml(pakid, pakname, pakauthor, version, pakdesc, pakos, pakdate, upmethod, rversion, runcmd, fileurl):
	# generate root node
	root = Element('app')

	# generate first root-child-node head
	head = SubElement(root, 'head')

	title = SubElement(head, 'title')
	title.text = pakname

	date = SubElement(head, 'date')
	date.text = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

	icon = SubElement(head, 'icon')
	icon.text = ""

	pid = SubElement(head, 'pakid')
	pid.text = pakid

	name = SubElement(head, 'pakname')
	name.text = pakname

	author = SubElement(head, 'pakauthor')
	author.text = pakauthor

	description = SubElement(head, 'description')
	description.text = pakdesc

	date = SubElement(head, 'pakdate')
	date.text = pakdate

	# generate second root-child-node install
	install = SubElement(root, 'install', attrib={'preferred': 'standalone' if upmethod == 'web' else 'localShiny'})

	if upmethod == 'web':
		# generate first install-child-node standalone
		standalone = SubElement(install, 'standalone')
		package = SubElement(standalone, pakos, attrib={'pakVersion': version, 'OSVersion': '', 'RVersion': rversion})
		package_url = SubElement(package, 'url')
		package_url.text = fileurl
	else:
		# generate second install-child-node localShiny
		local_shiny = SubElement(install, 'localShiny', attrib={'pakVersion': version, 'RVersion': rversion, 'localShinyVersion': '1.0'})
		command1 = SubElement(local_shiny, 'Rcommand')
		command1.text = 'Rscript -e "args=commandArgs(TRUE);library(localShiny);installApp(args[1])" {0}'.format(pakid)

	# generate third install-child-node reportable
	rportable = SubElement(install, 'rportable')

	winr = SubElement(rportable, 'Windows', attrib={'OSVersion': 'Windows10', 'RVersion': '4.0.4'})
	winr_url = SubElement(winr, 'url')
	winr_url.text = HOST + '/static/qtshiny/R-Windows-4.0.4.zip'

	macr = SubElement(rportable, 'macOS', attrib={'OSVersion': '', 'RVersion': '4.0.4'})
	macr_url = SubElement(macr, 'url')
	macr_url.text = ''

	linuxr = SubElement(rportable, 'Linux', attrib={'OSVersion': '', 'RVersion': '4.0.4'})
	linuxr_url = SubElement(linuxr, 'url')
	linuxr_url.text = ''

	# generate third root-child-node run
	run = SubElement(root, 'run')
	command2 = SubElement(run, 'Rcommand')
	command2.text = runcmd

	tree = ElementTree(root)

	# a pretty-printed xml
	indent(root)

	# write out xml data
	tree.write(UPLOAD_FOLDER + '/result.xml', encoding='utf-8', xml_declaration=True)
