# -*- encoding: utf-8 -*-
##
# $Id: terminfo.py 503 2008-02-29 04:11:40Z jwp $
##
# Copyright 2007, James William Pye. http://jwp.name
##
try:
	import curses
	curses.setupterm()
	data_provider = 'curses'
except:
	data_provider = None

if data_provider == 'curses':
	MOVE_CURSOR_BOL = curses.tigetstr('cr') or ''
	MOVE_CURSOR_UP = curses.tigetstr('cuu1') or ''
	MOVE_CURSOR_DOWN = curses.tigetstr('cud1') or ''
	MOVE_CURSOR_LEFT = curses.tigetstr('cub1') or ''
	MOVE_CURSOR_RIGHT = curses.tigetstr('cuf1') or ''

	CLEAR_SCREEN = curses.tigetstr('clear') or ''
	CLEAR_EOL = curses.tigetstr('el') or ''
	CLEAR_BOL = curses.tigetstr('el1') or (MOVE_CURSOR_BOL + CLEAR_EOL)
	CLEAR_EOS = curses.tigetstr('ed') or ''

	BOLD = curses.tigetstr('bold') or ''
	BLINK = curses.tigetstr('blink') or ''
	DIM = curses.tigetstr('dim') or ''
	REVERSE = curses.tigetstr('rev') or ''
	UNDERLINE = curses.tigetstr('smul') or ''
	ITALICS = curses.tigetstr('sitm') or ''
	INVISIBLE = curses.tigetstr('invis') or ''
	NORMAL = curses.tigetstr('sgr0') or ''
	SUBSCRIPT = curses.tigetstr('ssubm') or ''
	SUPERSCRIPT = curses.tigetstr('ssupm') or ''

	HIDE_CURSOR = curses.tigetstr('civis') or ''
	SHOW_CURSOR = curses.tigetstr('cnorm') or ''
	ABSOLUTE_MOVE_CURSOR = curses.tigetstr('cup') or ''
	RELATIVE_MOVE_CURSOR = curses.tigetstr('mrcup') or ''

	def dimensions():
		"get the dimensions of the terminal"
		return curses.tigetnum('cols'), curses.tigetnum('lines')
	def move_cursor_absolute((x,y)):
		"move the cursor to the given x,y coordinates"
		return curses.tparm(ABSOLUTE_MOVE_CURSOR, y, x)
	def move_cursor_relative((x,y)):
		"move the cursor to the given x,y coordinates relative to current position"
		return curses.tparm(RELATIVE_MOVE_CURSOR, y, x)

	set_color = curses.tigetstr('setf')
	x = -1
	if set_color:
		FG_BLACK, FG_BLUE, FG_GREEN, FG_CYAN, \
		FG_RED, FG_MAGENTA, FG_YELLOW, FG_WHITE = [	
			curses.tparm(set_color, x) for x in range(8)
		]
	else:
		set_color = curses.tigetstr('setaf')
		if set_color:
			FG_BLACK, FG_RED, FG_GREEN, FG_YELLOW, \
			FG_BLUE, FG_MAGENTA, FG_CYAN, FG_WHITE = [	
				curses.tparm(set_color, x) for x in range(8)
			]
		else:
			# No foreground coloring.
			FG_BLACK = FG_BLUE = FG_GREEN = FG_CYAN = \
			FG_RED = FG_MAGENTA = FG_YELLOW = FG_WHITE = ''

	set_color = curses.tigetstr('setb')
	if set_color:
		BG_BLACK, BG_BLUE, BG_GREEN, BG_CYAN, \
		BG_RED, BG_MAGENTA, BG_YELLOW, BG_WHITE = [	
			curses.tparm(set_color, x) for x in range(8)
		]
	else:
		set_color = curses.tigetstr('setab')
		if set_color:
			BG_BLACK, BG_RED, BG_GREEN, BG_YELLOW, \
			BG_BLUE, BG_MAGENTA, BG_CYAN, BG_WHITE = [	
				curses.tparm(set_color, x) for x in range(8)
			]
		else:
			# No background coloring.
			BG_BLACK = BG_BLUE = BG_GREEN = BG_CYAN = \
			BG_RED = BG_MAGENTA = BG_YELLOW = BG_WHITE = ''
	COLUMNS, LINES = dimensions()
	del x
else:
	MOVE_CURSOR_BOL = \
	MOVE_CURSOR_UP = \
	MOVE_CURSOR_DOWN = \
	MOVE_CURSOR_LEFT = \
	MOVE_CURSOR_RIGHT = \
	CLEAR_SCREEN = \
	CLEAR_EOL = \
	CLEAR_BOL = \
	CLEAR_EOS = \
	BOLD = \
	BLINK = \
	DIM = \
	REVERSE = \
	UNDERLINE = \
	NORMAL = \
	HIDE_CURSOR = \
	SHOW_CURSOR = \
	FG_BLACK = FG_BLUE = FG_GREEN = FG_CYAN = \
	FG_RED = FG_MAGENTA = FG_YELLOW = FG_WHITE = \
	BG_BLACK = BG_BLUE = BG_GREEN = BG_CYAN = \
	BG_RED = BG_MAGENTA = BG_YELLOW = BG_WHITE = ''
	def dimensions():
		raise NotImplementedError, 'no terminfo data source available'
	def position():
		raise NotImplementedError, 'no terminfo data source available'
	def move_cursor(xy):
		raise NotImplementedError, 'no terminfo data source available'
	COLUMNS = LINES = None

if __name__ == '__main__':
	import sys
	import os
	import __main__
	show_usage = False
	mod = 'name.jwp.terminfo'
	if len(sys.argv) > 1:
		if sys.argv[1] == 'sample':
			samples = [
				'FG_BLACK', 'FG_BLUE', 'FG_GREEN', 'FG_RED',
				'FG_CYAN', 'FG_WHITE', 'FG_YELLOW', 'FG_MAGENTA',
				'BOLD', 'BLINK', 'DIM',
				'REVERSE', 'UNDERLINE', 'ITALICS',
				'SUBSCRIPT', 'SUPERSCRIPT'
			]
			sys.stdout.write("import sys, os, " + mod + os.linesep * 2)

			for x in samples:
				sys.stdout.write('# [%ssample%s] %s%s' %(
					getattr(__main__, x), NORMAL, x, os.linesep,
				))
				sys.stdout.write(
					('sys.stdout.write("[%%ssample%%s] %(sample)s%%s" %%(' \
					'%(mod)s.%(sample)s, %(mod)s.NORMAL, os.linesep))' %{
						'mod' : mod, 'sample' : x
					}) + os.linesep
				)
		else:
			show_usage = True
			sys.stderr.write('unknown command: %r%s' %(sys.argv[1], os.linesep))
	else:
		show_usage = True

	if show_usage:
		sys.stderr.write("%s -m %s: [sample]%s" %(sys.executable, mod, os.linesep))
