"""
COMS W4705 - Natural Language Processing - Fall 2023
Homework 2 - Parsing with Probabilistic Context Free Grammars 
Daniel Bauer
"""
import math
import sys
from collections import defaultdict
import itertools
from grammar import Pcfg

### Use the following two functions to check the format of your data structures in part 3 ###
def check_table_format(table):
    """
    Return true if the backpointer table object is formatted correctly.
    Otherwise return False and print an error.  
    """
    if not isinstance(table, dict): 
        sys.stderr.write("Backpointer table is not a dict.\n")
        return False
    for split in table: 
        if not isinstance(split, tuple) and len(split) ==2 and \
          isinstance(split[0], int)  and isinstance(split[1], int):
            sys.stderr.write("Keys of the backpointer table must be tuples (i,j) representing spans.\n")
            return False
        if not isinstance(table[split], dict):
            sys.stderr.write("Value of backpointer table (for each span) is not a dict.\n")
            return False
        for nt in table[split]:
            if not isinstance(nt, str): 
                sys.stderr.write("Keys of the inner dictionary (for each span) must be strings representing nonterminals.\n")
                return False
            bps = table[split][nt]
            if isinstance(bps, str): # Leaf nodes may be strings
                continue 
            if not isinstance(bps, tuple):
                sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a pair ((i,k,A),(k,j,B)) of backpointers. Incorrect type: {}\n".format(bps))
                return False
            if len(bps) != 2:
                sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a pair ((i,k,A),(k,j,B)) of backpointers. Found more than two backpointers: {}\n".format(bps))
                return False
            for bp in bps: 
                if not isinstance(bp, tuple) or len(bp)!=3:
                    sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a pair ((i,k,A),(k,j,B)) of backpointers. Backpointer has length != 3.\n".format(bp))
                    return False
                if not (isinstance(bp[0], str) and isinstance(bp[1], int) and isinstance(bp[2], int)):
                    print(bp)
                    sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a pair ((i,k,A),(k,j,B)) of backpointers. Backpointer has incorrect type.\n".format(bp))
                    return False
    return True

def check_probs_format(table):
    """
    Return true if the probability table object is formatted correctly.
    Otherwise return False and print an error.  
    """
    if not isinstance(table, dict): 
        sys.stderr.write("Probability table is not a dict.\n")
        return False
    for split in table: 
        if not isinstance(split, tuple) and len(split) ==2 and isinstance(split[0], int) and isinstance(split[1], int):
            sys.stderr.write("Keys of the probability must be tuples (i,j) representing spans.\n")
            return False
        if not isinstance(table[split], dict):
            sys.stderr.write("Value of probability table (for each span) is not a dict.\n")
            return False
        for nt in table[split]:
            if not isinstance(nt, str): 
                sys.stderr.write("Keys of the inner dictionary (for each span) must be strings representing nonterminals.\n")
                return False
            prob = table[split][nt]
            if not isinstance(prob, float):
                sys.stderr.write("Values of the inner dictionary (for each span and nonterminal) must be a float.{}\n".format(prob))
                return False
            if prob > 0:
                sys.stderr.write("Log probability may not be > 0.  {}\n".format(prob))
                return False
    return True



class CkyParser(object):
    """
    A CKY parser.
    """

    def __init__(self, grammar): 
        """
        Initialize a new parser instance from a grammar. 
        """
        self.grammar = grammar

    def is_in_language(self,tokens):
        """
        Membership checking. Parse the input tokens and return True if 
        the sentence is in the language described by the grammar. Otherwise
        return False
        """
        
        sentence_length = len(tokens)
        parse_dict = {}
        span = 2
        start_token = "TOP"
        for i in range(sentence_length):
            if(len(self.grammar.rhs_to_rules[(tokens[i],)]) == 0):
                return False
            for k in range(len(self.grammar.rhs_to_rules[(tokens[i],)])):
               m = []
               m.append(self.grammar.rhs_to_rules[(tokens[i],)][k][0])
               
               if (i,i+1) in parse_dict:
                   parse_dict[i,i+1].append(self.grammar.rhs_to_rules[(tokens[i],)][k][0])
               else:
                   parse_dict[i,i+1] = m
                                   
               
        while span <= sentence_length:
            for i in range(sentence_length-span+1):
                j = i+span
                m = []
                parse_dict[i,j] = m
                for k in range(i+1,j):

                    first_part = parse_dict[i,k]
                    second_part = parse_dict[k,j]
                    for nonterminal1 in first_part:
                        
                        for nonterminal2 in second_part:

                            for l in range(len(self.grammar.rhs_to_rules[(nonterminal1,nonterminal2)])):
                                if (i,j) in parse_dict:
                                    parse_dict[i,j].append(self.grammar.rhs_to_rules[(nonterminal1,nonterminal2)][l][0])
                                else:
                                    storage = []
                                    storage.append(self.grammar.rhs_to_rules[(nonterminal1,nonterminal2)][l][0])
                                    parse_dict[i,j] = storage

            span += 1


        if start_token in parse_dict[0,sentence_length]:
            return True

        return False 
       
    def parse_with_backpointers(self, tokens):
        """
        Parse the input tokens and return a parse table and a probability table.
        """
        table= {}
        probs = {}
        if (self.is_in_language(tokens) == False):
            return table, probs
        sentence_length = len(tokens)
        span = 2
        for i in range(sentence_length):
            single_dict = {}
            prob_dict = {}
            for k in range(len(self.grammar.rhs_to_rules[(tokens[i],)])):

               single_dict[self.grammar.rhs_to_rules[(tokens[i],)][k][0]] = tokens[i]
               prob_dict[self.grammar.rhs_to_rules[(tokens[i],)][k][0]] = self.grammar.rhs_to_rules[(tokens[i],)][k][2]
               table[i,i+1] = single_dict
               probs[i,i+1] = prob_dict

         
        while span <= sentence_length:
            for i in range(sentence_length-span+1):
                j = i+span
                span_dict = {}
                span_prob_dict = {}
                span_prob = 0


                for k in range(i+1,j):

                    first_part = table[i,k]
                    second_part = table[k,j]

                    for nonterminal1 in first_part:
                        
                        for nonterminal2 in second_part:
                            for l in range(len(self.grammar.rhs_to_rules[(nonterminal1,nonterminal2)])):
                                if self.grammar.rhs_to_rules[(nonterminal1,nonterminal2)][l][2] > span_prob:

                                    span_dict[self.grammar.rhs_to_rules[(nonterminal1,nonterminal2)][l][0]] = ((nonterminal1,i,k),(nonterminal2,k,j))
                                    span_prob_dict[self.grammar.rhs_to_rules[(nonterminal1,nonterminal2)][l][0]] = math.log(self.grammar.rhs_to_rules[(nonterminal1,nonterminal2)][l][2])

  
                table[i,j] = span_dict
                probs[i,j] = span_prob_dict
            span += 1

        return table , probs


def get_tree(chart, i,j,nt): 
    """
    Return the parse-tree rooted in non-terminal nt and covering span i,j.
    """
    if isinstance(chart[(i,j)][nt], str):
        return (nt, chart[(i,j)][nt])

    else:

        left = chart[(i,j)][nt][0] 
        right = chart[(i,j)][nt][1]

  
        left_root = left[0]
        li = left[1] 
        lk = left[2] 

        right_root = right[0]
        rk = right[1]
        rj = right[2]


        left_tree = get_tree(chart, li, lk, left_root)

        right_tree = get_tree(chart, rk, rj, right_root)

        return(nt, left_tree, right_tree)
  
 
       
if __name__ == "__main__":
    
    with open('atis3.pcfg','r') as grammar_file: 
        grammar = Pcfg(grammar_file) 
        parser = CkyParser(grammar)
        toks =['flights', 'from','miami', 'to', 'cleveland','.']
        print(parser.is_in_language(toks))
        table,probs = parser.parse_with_backpointers(toks)
        assert check_table_format(table)
        assert check_probs_format(probs)
        print(get_tree(table, 0, len(toks), grammar.startsymbol))
        
