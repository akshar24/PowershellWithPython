# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 13:06:13 2019

@author: Akshar Patel
"""
from Parsing import ParsingCriteria
from Output import Output
import subprocess as sp
class PowerShellFunction:
    def __init__(self, funcName, funcArgs, funcDef, defaultParsing, defaultParsingArgs = {},defaultParsingCriteria = ParsingCriteria.OTHER):
        self.funcName = funcName
        self.funcArgs = funcArgs
        self.funcDef = funcDef
        self.defaultParsingCriteria = defaultParsingCriteria
        self.defaultParsing = defaultParsing
        self.parsingArgs = defaultParsingArgs
    def executeFunction(self, output = True, parsingCriteria = None, default = False, unpack = True ,  **kargs):
        params = " ".join(list(map(lambda x: f"-{x[0]} {x[1]}", kargs.items())))
        if parsingCriteria is None:
            parsingCriteria = self.defaultParsingCriteria
        parsingOp = ParsingCriteria().generateCriteria(parsingCriteria)
        if parsingOp is None:
            parsingOp = ""
        code = f"""{self.funcDef}
 $result =  {self.funcName} {params} 
if($result -ne $null){{
    $result = $result {parsingOp} 
     return $result
}}
"""
        if output:
            powershell = sp.Popen(["powershell", code], stderr = sp.STDOUT, stdout = sp.PIPE)
            result = powershell.communicate()
            try:
                result = result[0].decode('utf-8')
            except:
                result = str(result[0])
                result = result[2:-1]
        
            result = Output(result)
            if default:
                if self.defaultParsing is None:
                    return result
                try:
                    parser = result.feed(self.defaultParsing)
                    parser.parsingArgs = self.parsingArgs
                    output = parser.parse()
                    if unpack:
                        return output.unpack()
                    else:
                        return output
                except:
                    return result
            else:
                return result
        else:
            sp.call(["powershell", code])
            return None
    def setDefaultParsingCriteria(self, defaultParsingCriteria):
        self.defaultParsingCriteria = defaultParsingCriteria
    def setDefaultParsing(self,parse):
        self.defaultParsing = parse
    def setDefaultParsingArgs(self, parsingArgs):
        self.parsingArgs = parsingArgs
    def __str__(self):
        return self.funcDef
    def funcDefinition(self, **kargs):
        keys = list(kargs.keys())
        func = str(self.funcDef)
        for key in keys:
            func = func.replace(f"${key}", str(kargs.get(key)))
        return func
class PowerShellPipe:
	def __init__(self,defaultParsing = None, defaultParsingArgs = {}, defaultParsingCriteria = ParsingCriteria.OTHER):
		self.code = []
		self.build = None
		self.defaultParsingCriteria = defaultParsingCriteria
		self.defaultParsing = defaultParsing
		self.parsingArgs = defaultParsingArgs
	def append(self, code):
		self.code.append(code)
		return self
	def buildPipe(self):
		self.build = " | ".join(self.code)
		return self
	def replace(self, code, newcode, index = "first"):
		if index == "all":
			self.code = list(map(lambda x: newcode if x == code else code, self.code))
		elif index  == "first":
			self.code[self.code.index(code)] = newcode
		else:
			for i in range(len(self.code)):
				if (i + 1) in index and self.code[i] == code:
					self.code[i] = newcode
		return self
	def remove(self, code):
		self.code.remove(code)
		return self
	def execute(self, default = False, parsingCriteria = 'other'):
		if self.build is None: return None

		ps = PowerShellExecutor()
		pipe = ps.defineFunction("pipe", self.build, defaultParsing = self.defaultParsing, defaultParsingArgs = self.parsingArgs, defaultParsingCriteria = self.defaultParsingCriteria)
		return pipe.executeFunction(default = default, parsingCriteria= parsingCriteria)
		
	def __str__(self):
		return " | ".join(self.code)

class PowerShellExecutor:

    #Run Code Snippet
    def executeCodeSnippet(self, code, output = True, parsingCriteria = ParsingCriteria.OTHER):
        psFunc = self.defineFunction("CodeSnippet", code)

            
        result = psFunc.executeFunction(output = output, parsingCriteria = parsingCriteria)
        return result
    #Define a Function
    def defineFunction(self, funcName, funcBody, defaultParsing = None, defaultParsingArgs = {}, defaultParsingCriteria = ParsingCriteria.OTHER, **kargs):
        funcArgs = "(" + ",".join(list(map(lambda x: f"${x[0]}" if x[1] is None else f"[{x[1]}]${x[0]}", kargs.items()))) + ")"
        func = f"""function {funcName}{funcArgs}{{
  {funcBody} 
}} """
        return PowerShellFunction(funcName, funcArgs, func, defaultParsing, defaultParsingArgs, defaultParsingCriteria)
    #Execute Script
    def executeScript(self, scriptName, output = True, parsingCriteria = ParsingCriteria.OTHER, **kargs):
        params = []
        for key, val in kargs.items():
            params.append(f"-{key}")
            params.append(str(val))
        code = [scriptName] + params
        code = " ".join(code)
        script = self.defineFunction("script", code)
        result = script.executeFunction(output = output, parsingCritera = parsingCriteria)
        return result
    def generatePipe(self, defaultParsing = None, defaultParsingArgs = {}, defaultParsingCriteria = ParsingCriteria.OTHER):
        return PowerShellPipe(defaultParsing, defaultParsingArgs, defaultParsingCriteria)
    def transformFuncToPipe(self, pipe):
        pipe.simulate('determine').transform(PowerShellFunction).withArguments(True).extract(use = "UniversalExtractorEngine")

	   