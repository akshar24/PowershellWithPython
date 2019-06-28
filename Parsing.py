# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 13:25:15 2019

@author: Akshar Patel
"""
import pandas as pd
class ParsingCriteria:
    NONCSV = "non-csv"
    CSV = "csv"
    OTHER = "other"
    def __init__(self):
        self.__choices = {"non-csv": " | Format-List", "csv": "| ConvertTo-Csv", "other": None}
    def generateCriteria(self, criteria):
        return self.__choices.get(criteria, None)
class ParserChoices:
    PARSETOLIST= "ParseToList"
    INTERPRETTYPE = "InterpretType"
    PARSEPSCSVTOPYTABLE = "ParsePSCSVToPyTable"
    PARSETOPYDICT = "ParseToPyDict"
    PARSETOPYTABLE = "ParseToPyTable"
    PARSEPSHASHTABLETOPYDICT ="ParsePSHashTableToPyDict"
    CUSTOMPARSING ="CustomParsing"
    PARSETOTWOWAYDICT = "ParseToTwoWayDict"
class ParserEngine:
    def __init__(self):
        self.choices = {"ParseToList": self.parseToList, "InterpretType": self.convertToType,  "ParsePSCSVToPyTable": self.parsePSCSVToPyTable, "ParseToPyTable": self.parseToPyTable, "ParseToPyDict": self.parseToPyDict, "ParsePSHashTableToPyDict":self.parsePSHashTableToPyDict, "CustomParsing": self.customParsing, "ParseToTwoWayDict": self.twoWayHashTable}
    def generateParser(self, choice):
        if choice is None:
            return choice
        return self.choices.get(choice, None)
    def parseToList(self, output, kargs):
       
        clean = kargs.get("clean", "\r\n")
    
        ele = output.split(clean)
        results = []
        ele = list(filter(lambda x: x!= '', ele))
        for el in ele:
            if el.startswith('['):
                results.append(self.nestedParsing(el))
            else:
                results.append(self.convertToType(el, kargs))
        return results
    def convertToType(self, output, kargs = {}):
        output = output.strip()
        if output.replace(".", "").replace("-","").isdigit():
            if "." in output:
                return float(output)
            else: return int(output)
        elif output.lower() in ["true", "false", "yes", "no"]:
            if output.lower() in ["true", "yes"]:
                return True
            else:
                return False
            
        
        else:
            return output
    def parsePSCSVToPyTable(self, csv, kargs):
        from io import StringIO
        split = csv.split("\r\n")
        lineNum = None
        for i in range(len(split)):
            if "," in split[i]:
                lineNum = i
                break
        csv = "\n".join(split[lineNum:])
        csv = StringIO(csv)
        sep = kargs.get("sep", ",")
        df = pd.read_csv(csv, sep =sep)
        return df
    def parseToPyTable(self, line, kargs):
        data = self.parseToPyDict(line, kargs)
        return pd.DataFrame(data)
    def parseToPyDict(self, lines, kargs):
        clean = kargs.get("sep", "\r\n")
        lines = lines.split(clean)
      
        data = {}
        last = None
        lastval = None
        index = 0
        for line in lines:
            if index > 0 and last is not None:
                nextKey = line[0:(index-1)]
                
                if len(nextKey) == nextKey.count(' '):
                    lastval += line[index:len(line)]
                    continue
                else:
                    col = last.strip()
                    current = data.get(col, None)
                    if lastval.count(' ') == len(lastval):
                        lastval = None
                    if current is None:
                        data[col] = [lastval]
                    else:
                        new=  data[col]
                        new.append(lastval)
                        data[col] = new
                    last, lastval, index = ([None] * 2) + [0]
                
            temp = ""
            for i in range(len(line)):
                temp += line[i]
                if line[i] == ':':
                    last = temp[:-1]
                    index = i+ 1
                    lastval = line[index:]
                    break
       
        last = last.strip()
        lastline = lines[-1]
        
        if lastline[index:len(lastline)] not in lastval:    
            key = lastline[0:(index-1)]
      
            if len(key) == key.count(' '):
                lastval += lastline[index:len(lastline)]
   
        current = data.get(last, None)
    
        if lastval.count(' ')== len(lastval):
            lastval =None
        if current is None:
            current = [lastval]
            data[last] = current
        else:
            new=  data[last]
            new.append(lastval)
            data[last] = new
     
        lengths = list(map(lambda x: len(x), data.values()))
          
        unique = list(set(lengths))

        if len(unique)== 1:
            return data
        counts = list(map(lambda x: lengths.count(x), unique))
        common = unique[counts.index(max(counts))]
        for key, val in data.items():
            num = len(val)
            
            if num < common:
                i = 0
                while i < len(val):
                    val.append(val[i])
                    i += 1
                    if len(val) == common:
                        break
                data[key] = val
            else:
                data[key] = val[0:common]
                
        cols = list(data.keys())
        fixed = list(cols)
        row = 0
        
        for line in lines:
            for col in fixed:
                if line.lstrip().startswith(col):
                    isIn = False
                    try:
                        cols.index(col)
                        isIn = True
                    except:
                        isIn = False
                    if isIn:
                        cols.remove(col)
                    else:
                        for col1 in cols:
                            new = data[col1]
                            new.pop()
                            new.insert(row, None)
                            data[col1] = new
                        cols= list(fixed)
                    
                        cols.remove(col)
                        row += 1
        for col in cols:
            new = data[col]
            new[row] = None
            data[col] = new
        
       
        return data
    def customParsing(self, output, kargs):
        func = kargs.get("parsingFunc", None)
        if func is None:
            return output
        try:
            result = func(output)
            return result
        except:
            return output
    def twoWayHashTable(self, output, kargs):
        mode = kargs.get("mode", "separate")
        col1 = kargs.get("col1", "Name")
        col2 = kargs.get("col2", "Value")
        
        if mode in ["combine", "comb", "c", "com"]:
            kargs["mapping"] = {col1:col2, col2:col1}
            
            hashtable = self.parsePSHashTableToPyDict(output, kargs)
            return hashtable
        else:
            kargs["mapping"] = {col1:col2}
            hashtable1 = self.parsePSHashTableToPyDict(output, kargs)
            kargs["mapping"] = {col2:col1}
            hashtable2 = self.parsePSHashTableToPyDict(output, kargs)
            return (hashtable1, hashtable2)
    def parsePSHashTableToPyDict(self, lines, kargs):
        data = self.parseToPyDict(lines, kargs)
        
        mapping = kargs.get("mapping", None)
        vals = mapping
        if vals is None:
            vals = {}
            for key in data.keys():
                if key != "Value":
                    vals[key] = ["Value"]
        else:
            for key, val in mapping.items():
                if not isinstance(val, list):
                    vals[key] = [val] 
                vals[key] = list(set(vals[key]))
        
        hashtable = {}
        for key, val in data.items():
            if key in vals:
                for j in range(len(vals[key])):
                    for i in range(len(val)):
                        k = val[i].strip()
                        ans = data[vals[key][j]][i]
                        if ans is None: 
                            v = None
                        else:
                            v = self.parseToList(ans.strip(),kargs)
                        if v is not None and len(v) == 1:
                            v = v[0]
                        current = hashtable.get(k, {})
                        current1 = current.get(vals[key][j],"N/A")
                        if current1 == "N/A":
                            current1 = v
                        else:
                            if not isinstance(current1, list):
                                current1 = [current1, v]
                                
                            else: 
                                current1.append(v)
                        current[vals[key][j]] = current1
                        hashtable[k] = current
        
        for key, val in hashtable.items():
            if val is not None and len(val) == 1:
                hashtable[key] = list(val.values())[0]
            else:
                hashtable[key] =val
                        
        return hashtable
    def nestedParsing(self, out):
        stack = []
        lists = {}
        counter = 0
        temp = ""
        for i in out:
            if i == '[':
                stack.append(i)
                lists[str(counter + 1)] = []
                counter += 1
            else:
                if len(stack) == 0:
                    return out
                if i != ']':
                    if i != ',':
                        temp += i
                    else:
                        new = lists[str(counter)]
                        new.append(self.convertToType(temp))
                        lists[str(counter)] = new
                        temp = ""
                       
                else:
                    if len(temp) > 0:
                        new = lists[str(counter)]
                        new.append(self.convertToType(temp))
                        lists[str(counter)] = new
                        temp = ""
                  
                    stack.pop()
                    if len(stack) == 0:
                        break
                    l = lists[str(counter)]
                    new = lists[str(counter-1)]
                    new.append(l)
                    lists[str(counter- 1)] = new
                    del lists[str(counter)]
                    counter -=1
                    
        result = list(lists.values())
        result = list(filter(lambda x: x != '', result[0]))
        return result
	
class Parser:
    def __init__(self, parser, output):
        self.parser= parser
        self.output = output

    def initialize(self, **kargs):
        self.parsingArgs = kargs
        return self
    def parse(self):
        
        if self.parser is not None:
            try:
                output = self.parser(self.output.unpack() ,self.parsingArgs)
                self.output.pack(output)
                return self.output
            except Exception as e:
                print(str(e))
            
                return self.output
        else:
            return self.output    