###############################################################
# Name:			 Renderer.py
# Purpose:	 Render a song on a dc
# Author:		 Luca Allulli (webmaster@roma21.it)
# Created:	 2009-02-21
# Copyright: Luca Allulli (http://www.roma21.it/songpress)
# License:	 GNU GPL v2
##############################################################

import wx
from SongDecorator import *
from SongTokenizer import *
from SongFormat import *
from SongBoxes import *

class Renderer(object):
	
	def __init__(self, sf, sd = SongDecorator()):
		object.__init__(self)
		self.text = ""
		self.sd = sd
		self.dc = None
		# SongFormat
		self.sf = sf
		self.verseNumber = 0
		self.textFont = None
		self.chordFont = None
		self.commentFont = None
		self.format = None
		self.currentBlock = None
		self.currentLine = None
		self.song = None

	def BeginBlock(self, type):
		self.EndBlock()
		if type == SongBlock.verse:
			self.verseNumber += 1
			# self.currentBlock.verseNumber = self.verseNumber
			self.sf.StubSetVerseCount(self.verseNumber)
			self.format = self.sf.verse[self.verseNumber-1]
		else:
			self.format = self.sf.chorus
		self.currentBlock = SongBlock(type, self.format)
		self.currentBlock.verseNumber = self.verseNumber
		self.textFont = self.format.wxFont
		self.chordFont = self.format.chord.wxFont	
		self.commentFont = self.format.comment.wxFont
	
	def EndBlock(self):
		if self.currentBlock != None:
			self.EndLine()
			self.song.AddBox(self.currentBlock)
			self.currentBlock = None

	def BeginVerse(self):
		if self.currentBlock == None:
			self.verseNumber += 1
			print("self.verse %d" % (self.verseNumber,))
			self.sf.StubSetVerseCount(self.verseNumber)
			self.format = self.sf.verse[self.verseNumber-1]
			self.BeginBlock(SongBlock.verse)

	def BeginChorus(self):
		self.format = self.sf.chorus
		self.BeginBlock(SongBlock.chorus)
		
	def ChorusVSkip(self):
		self.EndLine()
		self.BeginLine()
		self.EndLine()
		
	def AddText(self, text, type = SongText.text):
		self.BeginVerse()
		self.BeginLine()
		if type == SongText.comment:
			text = "(" + text + ")"
			font = self.commentFont
		elif text == SongText.chord:
			font = self.chordFont
		else:
			font = self.textFont
		t = SongText(text, font, type)
		self.currentLine.AddBox(t)
		
	def AddTitle(self, title):
		self.format = self.sf.title
		self.BeginBlock(SongBlock.title)	
		self.AddText(title, SongText.title)
		self.EndBlock()
		
	def BeginLine(self):
		if self.currentLine == None:
			self.currentLine = SongLine()
			
	def EndLine(self):
		if self.currentLine != None:
			self.currentBlock.AddBox(self.currentLine)
			self.currentLine = None
		
	def GetAttribute(self):
		print("Getting attribute...")
		try:
			tok = self.tkz.next()
			if tok.token != SongTokenizer.colonToken:
				self.tkz.Repeat()
				return None
			tok = self.tkz.next()
			if tok.token != SongTokenizer.attrToken:
				self.tkz.Repeat()
				return None
			return tok.content
		except StopIteration:
			print("No attribute")
			pass
		return None
		
	def GetState(self):
		return None if self.currentBlock == None else self.currentBlock.type
	
	def Render(self, text, dc):
		self.text = text
		self.dc = dc
		self.verseNumber = 0
		self.format = self.sf
		self.currentLine = None
		self.currentBlock = None
		self.song = SongSong(self.sf)
		
		for l in self.text.splitlines():
			state = self.GetState()
			self.tkz = SongTokenizer(l)
			empty = True
			for tok in self.tkz:
				state = self.GetState()
				empty = False
				t = tok.token
				if t == SongTokenizer.normalToken:
					self.AddText(tok.content)
				elif t == SongTokenizer.chordToken:
					self.AddText(tok.content[1:], SongText.chord)
				elif t == SongTokenizer.commandToken:
					cmd = tok.content
					if cmd == 'soc':
						self.BeginChorus()
					elif cmd == 'eoc' and state == SongBlock.chorus:
						self.EndBlock()
					elif cmd == 'c' or cmd == 'comment':
						a = self.GetAttribute()
						if a != None:
							self.AddText(a, SongText.comment)
					elif cmd == 't' or cmd == 'title':
						a = self.GetAttribute()
						if a != None:
							self.AddTitle(a)
							
			self.EndLine()
			if empty:
				if state == SongBlock.verse:
					self.EndBlock()
				elif state == SongBlock.chorus:
					self.ChorusVSkip()
		self.EndBlock()
		self.sd.Draw(self.song, dc)
		self.dc = None
		
		