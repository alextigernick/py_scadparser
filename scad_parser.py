from ply import lex, yacc
import os
import math
#workaround relative imports.... make this module runable as script
if __name__ == "__main__":
    from scad_ast import *
    from scad_tokens import *
else:
    from .scad_ast import *
    from .scad_tokens import *

precedence = (
    ('nonassoc', 'ASSERT'),
    ('nonassoc', 'ECHO'),
    ('nonassoc', "THEN"),
    ('nonassoc', "ELSE"),
    ('nonassoc', "?"),
    ('nonassoc', ":"),

    ('nonassoc', '='),
    ('left', "AND", "OR"),
    ('left', "EQUAL", "NOT_EQUAL", "GREATER_OR_EQUAL", "LESS_OR_EQUAL", ">", "<"),
    ('left', '+', '-'),
    ('left', "%"),
    ('left', '*', '/'),
    ('right', '^'),
    ('right', 'NEG', 'POS', 'BACKGROUND', 'NOT'),
    ('left', "ACCESS"),
    ('nonassoc', "(", ")", "{", "}"),
    
 )
count = 0
class InlineAssert:
    def __init__(self,expr,a):
        self.expr = expr
        self.a = a
class Parameter:
    def __init__(self,name):
        self.name = name
class OptionalParameter:
    def __init__(self,name,expr):
        self.name = name
        self.expr = expr
class ScopedObject:
    def __init__(self,expr,lineno,ret=True) -> None:
        global count
        self.count = count
        count += 1
        self.expr = expr
        self.lineno = lineno
        self.ret =ret
    def get_string(self):
        lines = parse_expr_list(self.expr)
        if(self.ret):#used for things that return on their own.
            lines[-1] = f"return {lines[-1]}"
        lines = '\n\t'.join(lines)
        ret = f"def ScopedObject_{self.lineno}_{self.count}():\n\t{lines}\nScopedObject_{self.lineno}_{self.count}()"
        return ret.split("\n")
    
def p_statements(p):
    '''statements : statements statement'''
    if type(p[2]) is list:
        p[0] = p[1] + p[2]
    else:
        p[0] = [*p[1],p[2]]
    

def p_statements_empty(p):
    '''statements : empty'''
    p[0] = []

def p_empty(p):
    'empty : '
    p[0] = ""

def p_statement(p):
    ''' statement : IF "(" expression ")" statement %prec THEN
                |   IF "(" expression ")" statement ELSE statement
                |   for_loop
                |   LET "(" assignment_list ")" statement %prec THEN
                |   assert_or_echo
                |   "{" statements "}"
                |   "%" statement %prec BACKGROUND
                |   "*" statement %prec BACKGROUND
                |   "!" statement %prec BACKGROUND
                |   "#" statement %prec BACKGROUND
                |   call statement
                |   USE FILENAME
                |   INCLUDE FILENAME
                |   ";"
                '''
    if p[1] == "!": 
        p[0] = f"not {p[2]}"
        
    p[0] = "statement("+",".join([str(i) for i in p[1:]])+")"
    
def p_id(p):
    '''id : ID'''
    p[0] = p[1]
    
def p_loop_var(p):
    '''loop_var : id "=" expression
    '''
    p[0] = f"loop_level({p[1]} = {p[3]})"
    
def p_loop_vars(p):
    '''loop_vars :  loop_vars commas loop_var
                |   loop_var
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [*p[1],p[3]]
        
def p_for_loop(p):
    '''for_loop : FOR "(" loop_vars ")" statement'''
    p[0] = f"for_loop({[p[3],p[5]]})"

# def p_list_comp_1(p):
#     '''list_comp : expression FOR loop_var'''
    
def p_statement_function(p):
    'statement : function'
    p[0] = p[1]
    

def p_statement_module(p):
    'statement : module'
    p[0] = "module("+",".join([str(i) for i in p[1:]])+")"
    
    

def p_statement_assignment(p):
    '''statement :  id "=" expression ";"
                |   id "=" function_literal ";"
    '''
    p[0] = f"{p[1]} = {p[3]}\n"

def p_ternary(p):
    ''' ternary_expr : expression "?" expression ":" expression '''
    # temp = f"if {p[1]}:\n\return {p[3]}\nelse:\n\ttemp={p[5]}\nreturn temp\n"
    # temp = f"(({p[3]}) if ({p[1]}) else ({p[5]}))"
    # p[0] = temp
    p[0] = ScopedObject(f"if {p[1]}:\n\treturn {p[3]}\nelse:\n\treturn {p[5]}\n".split("\n"),p.lexer.lineno,ret=False)
    # p[0] = temp.split("\n")
    
def p_logic_expr(p):
    '''logic_expr :  "-" expression %prec NEG
                |   "+" expression %prec POS
                |   "!" expression %prec NOT
                |   ternary_expr
                |   expression "%" expression
                |   expression "+" expression
                |   expression "-" expression
                |   expression "/" expression
                |   expression "*" expression
                |   expression "^" expression
                |   expression "<" expression
                |   expression ">" expression
                |   expression EQUAL expression
                |   expression NOT_EQUAL expression
                |   expression GREATER_OR_EQUAL expression
                |   expression LESS_OR_EQUAL expression
                |   expression AND expression
                |   expression OR expression
       '''
    if len(p) == 4:
        p[0] = f"({p[1]} {p[2]} {p[3]})"
        # p[0] = "logic_expr_fallthrough("+",".join([str(i) for i in p[1:]])+")"
    elif len(p) == 3:
        if p[1] == "!":
            p[0] = f"not {p[2]}"
        else:
            p[0] = f"({p[1]}{p[2]})"
    elif len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = "logic_expr_fallthrough("+",".join([str(i) for i in p[1:]])+")"
        
        

def p_dot_access(p):
    '''dot_access_expr : expression "." id '''
    p[0] = f"{p[1]}.{p[3]}"

def p_call_access(p):
    '''call_access_expr : expression "(" opt_call_parameter_list ")" %prec ACCESS'''
    p[0] = f"{p[1]}({p[3]})"#"call_access_expr("+",".join([p[1],p[3]])+")"
    
    
    
def p_bracket_access(p):
    '''bracket_access_expr : expression "[" expression "]"'''
    p[0] = "bracket_access_expr("+",".join([p[1],p[3]])+")"
    
    
def p_access_expr(p):
    '''access_expr : dot_access_expr
                |   call_access_expr
                |   bracket_access_expr
        '''
    p[0] = p[1]
    

def p_list_stuff(p):
    '''list_stuff : EACH expression %prec THEN
                |   "[" expression ":" expression "]"
                |   "[" expression ":" expression ":" expression "]"
                |   "[" for_loop expression "]"
                |   tuple
        '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = "list_stuff("+",".join([str(i) for i in p[1:]])+")"
    
def p_assert_or_echo(p):
    '''assert_or_echo : ASSERT "(" opt_call_parameter_list ")"
                    |   ECHO "(" opt_call_parameter_list ")"
       '''
    if p[1] == "echo":
        p[0] = f"print({p[3]})"
    else:
        p[0] = f"assert({p[3]})"
    
    
def p_constants(p):
    '''constants : STRING
                |  TRUE
                |  FALSE
                |  NUMBER'''
    p[0] = str(p[1])
    

def p_for_or_if(p):
    '''for_or_if :  for_loop expression %prec THEN
                |   IF "(" expression ")" expression
                |   IF "(" expression ")" expression ELSE expression
       '''
    p[0] = "for_or_if("+",".join([str(i) for i in p[1:]])+")"
    
def p_let_statement(p):
    '''let_expr :   LET "(" assignment_list ")" expression %prec THEN '''
    ret = ScopedObject([*p[3],p[5]],"let")
    p[0] = ret
    
def p_expression(p):
    '''expression : id
                |   logic_expr
                |   list_stuff
                |   let_expr
                |   assert_or_echo
                |   constants
                |   for_or_if
                |   access_expr %prec ACCESS
                |   "(" expression ")"
       '''
    if len(p) == 4:
        p[0] = p[2]
    else:
        p[0] = p[1]
        
def p_expression_with_assert_or_echo(p):
    '''expression : assert_or_echo expression
       '''
    # p[0] = InlineAssert(p[2],p[1])
    # TODO: actually throw these asserts
    p[0] = p[2]#[p[1],p[2]]
def p_assignment_list(p):
    '''assignment_list : id "=" expression
       '''
    if type(p[3]) == ScopedObject:
        lines = parse_expr_list(p[3])
        lines[-1] = f"{p[1]} =  {lines[-1]}"
        p[0] = ["\n".join(lines)]
    else:
        p[0] = [f"{p[1]} = {p[3]}"]
    
def p_assignment_list2(p):
    '''assignment_list : assignment_list "," id "=" expression
       '''
    if type(p[5]) == ScopedObject:
        lines = parse_expr_list(p[5])
        lines[-1] = f"{p[3]} =  {lines[-1]}"
        p[0] = [*p[1],"\n".join(lines)]
    else:
        p[0] = [*p[1],f"{p[3]} = {p[5]}"]
            
def p_call(p):
    ''' call : id "(" opt_call_parameter_list ")"'''
    p[0] = f"{p[1]}({p[3]})"
    
    
def p_tuple(p):
    ''' tuple : "[" opt_expression_list "]"
        '''
    p[0] = p[2]
    
    
def p_commas(p):
    '''commas : commas ","
              | ","
       '''

def p_opt_expression_list(p):
    '''opt_expression_list : expression_list
                        |    expression_list commas
                        |    empty'''
    p[0] = p[1]
    
    
def p_expression_list(p):
    ''' expression_list : expression_list commas expression
                    |     expression
        '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [*p[1],p[3]]
    
def p_expression_list_no_commas(p):
    ''' expression_list_no_commas : __expression_list_no_commas ";"
        '''
    p[0] = p[1]
    
def p___expression_list_no_commas(p):
    ''' __expression_list_no_commas : __expression_list_no_commas expression
                    |     expression
        '''
    if len(p) == 2:
        if type(p[1]) is list:
            p[0] = p[1]
        else:
            p[0] = [p[1]]
    else:
        if type(p[2]) is list:
            p[0] = [*p[1],*p[2]]
        else:
            p[0] = [*p[1],p[2]]
    
    
def p_opt_call_parameter_list(p):
    '''opt_call_parameter_list : empty
                               | call_parameter_list
       '''
    if len(p) == 1:
        p[0] = None
    else:
        p[0] = p[1]
    
def p_call_parameter_list(p):
    '''call_parameter_list : call_parameter_list commas call_parameter
                        |    call_parameter'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[1] + "," + p[3]
      
    
def p_call_parameter(p):
    '''call_parameter : expression
                    |  named_call_parameter'''
    p[0] = p[1]
      
    
def p_named_call_parameter(p):
    '''named_call_parameter : id "=" expression'''
    p[0] = "".join([str(i) for i in p[1:]])
      
       
def p_opt_parameter_list(p):
    '''opt_parameter_list : parameter_list
                        |   parameter_list commas
                        |   empty
       '''
    if p[1] is None:
        p[0] = []
    else:
        p[0] = p[1]
      

def p_parameter_list(p):
    '''parameter_list :     parameter_list commas parameter
                        |   parameter'''
    # if type(p[1]) is list:
    #     p[0] = [*p[1],p[3]]
    # else:
    #     p[0] = [p[1]]
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [*p[1],p[3]]
      

def p_parameter(p):
    '''parameter : id'''
    p[0] = Parameter(p[1])
     
     
def p_opt_parameter(p):
    '''parameter : id "=" expression'''
    p[0] = OptionalParameter(p[1],p[3])
      
def parse_expr_list(l):
    if type(l) == str:
        return [l]
    elif type(l) == list:
        ret = []
        for expr in l:
            ret.extend(parse_expr_list(expr))
        return ret
    elif type(l) == ScopedObject:
        return l.get_string()
    else:
        print(l)
        print(type(l))
        raise Exception("unexpected type in function body")
    
def p_function(p):
    '''function : FUNCTION id "(" opt_parameter_list ")" "=" expression_list_no_commas
       '''
    params = []
    opt_params = []
    for pararm in p[4]:
        if type(pararm) is Parameter:
            params.append(pararm.name)
        elif type(pararm) is OptionalParameter:
            opt_params.append(f"{pararm.name}={pararm.expr}")
        else:
            raise Exception("unexpected type in function definition")
    lines = parse_expr_list(p[7])
    lines[-1] = f"return {lines[-1]}"
    function_body = "\n".join(lines).replace('\n','\n\t')
    all_params = [*params,*opt_params]
    p[0] = f"def {p[2]}({','.join(all_params)}): \n\t{function_body}\n"
      
    
def p_function_literal(p):
    '''function_literal : FUNCTION "(" opt_parameter_list ")" expression
       '''
    p[0] = f"lambda {p[3]} : {p[5]}"
    
def p_module(p):
    '''module : MODULE id "(" opt_parameter_list ")" statement
       '''
    p[0] = "module("+",".join([str(i) for i in p[1:]])+")"
     


def p_error(p):
    if p is not None:
        print(f'py_scadparser: Syntax error: {p.lexer.filename}({p.lineno}) {p.type} - {p.value}')
    else:
        print("ERROR IS NONE")

def parseFile(scadFile):

    lexer = lex.lex(debug=False)
    lexer.filename = scadFile
    parser = yacc.yacc(debug=True)

    modules = []
    functions = []
    globalVars = []

    appendObject = { ScadTypes.MODULE : lambda x: modules.append(x),
                     ScadTypes.FUNCTION: lambda x: functions.append(x),
                     ScadTypes.GLOBAL_VAR: lambda x: globalVars.append(x),
    }

    from pathlib import Path
    with Path(scadFile).open() as f:
        p = parser.parse(f.read(), lexer=lexer)
        for each in p:
            print(each)
            print("\n")
        

    return modules, functions, globalVars

def parseFileAndPrintGlobals(scadFile):

    print(f'======{scadFile}======')
    modules, functions, globalVars = parseFile(scadFile)

    print("Modules:")
    for m in modules:
        print(f'    {m}')

    print("Functions:")
    for m in functions:
        print(f'    {m}')

    print("Global Variables:")
    for m in globalVars:
        print(f'    {m.name}')

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} [-q] <scad-file> [<scad-file> ...]\n   -q : quiete")

    quiete = sys.argv[1] == "-q"
    files = sys.argv[2:] if quiete else sys.argv[1:]
    try:
        os.remove("parsetab.py")
        os.remove("parser.out")
    except:
        pass
    for i in files:
        if quiete:
            print(i)
            parseFile(i)
        else:
            parseFileAndPrintGlobals(i)

