# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 13:59:33 2019

@author: Akshar Patel
"""
from Parsing import ParserEngine
from Parsing import Parser
class Output:
    def __init__(self, output):
        self.__output = output
       
    def feed(self, parser):
        parser = ParserEngine().generateParser(parser) 
        
        return Parser(parser, self)
    def unpack(self):
     
        return self.__output
    def pack(self, output):
        self.__output = output