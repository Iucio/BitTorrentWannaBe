# Formato     campos          Exempo
# Byte string => <len>:<str>  => 4:spam == "spam"
# Int         => i<num>e      => i-55e == -55
# List        => l<item>e     => l2:oie == ["oi"]
# Dict        => d<key><val>e => d2:oi3:olae == {"oi":"ola"}

# Índices foram usados pois, com: for char in string, eu ficaria lendo várias e várias vezes um mesmo texto que já decodifiquei em outra função.
# Além de eu não saber como poderia fazer com for each. Porque ficaria mais complexo, na minha opnião.

##############################################
### DECODIFICAÇÃO PARA DICIONÁRIO OU TEXTO ###
##############################################

# [IMPORTANTE] A função inicial é a parser()

def parse_int(str, j):
    # Retira o inteiro e retorna o número como uma string e o índice que parou.
    i = 1
    valor = ""
    while str[i] != 'e':
        valor = valor + str[i] # Concateno strings na medida que ele vai lendo.
        i += 1
    return int(valor), j+i

def parse_list(str, j):
    # Retira itens da lista e retorna uma lista os contendo e o índice que parou.
    i = 1
    lista = []
    while str[i] != 'e': # 'e' é o que identifica o final da lista.
        retorno = parse_bencode(str[i:]) # Como podem ter outros tipos de itens na lista(byte string, int, list e dict), eu chamo o parser.
        i = retorno[1]
        lista.append(retorno[0])
    return lista, j+i

def parse_byte_string(str, len):
    # Retorna a strin do byte string.
    return str[:len] # Slice para ter apenas a byte string. Só consigo fazer isso com a byte string, por causa do <len>:
        
def parse_dict(str):
    dicionario = {}
    i = 1
    while str[i] != 'e': # 'e' é o que ientifica o final do dicionario.
        retorno = parse_bencode(str[i:])
        chave_valor = retorno[0]
        for j in range(0,len(chave_valor),2):
            dicionario.update({chave_valor[j] : chave_valor[j+1]})
        i = retorno[1]
    return dicionario, i + 1 # + 1 pra não devolver o 'e'. Caso contrário, a cache ficaria envenenada.


def parse_bencode(str):
    # lê e decide que tipo de formato deve ser traduzido.
    i = 0
    lista = []
    cache = "" # Variavel temporario para guarda <len> do byte string, já que eu tenho que passar por ele pra descobrir ':'.
    while i < len(str)-1:
        if str[i] == 'i': # Inteiro
            retorno = parse_int(str[i:], i)
            lista.append(retorno[0])
            i = retorno[1] + 1 # +1 para resolver o caracter de término 'e' na cache, usada exclusivamente pelo parse_byte_string
            cache = "" # Reseto a cache, pois deve ser temporaria
        elif str[i] == 'l': # Lista
            retorno = parse_list(str[i:], i)
            for item in retorno[0]:
                lista.append(item)
            i = retorno[1] + 1 # +1 para resolver o caracter de término 'e' na cache, usada exclusivamente pelo parse_byte_string
            cache = "" # Reseto a cache, pois deve ser temporaria
        elif str[i] == ':': # Byte string
            length = int(cache) # string => inteiro. Campo <len> do byte string.
            lista.append(parse_byte_string(str[i+1:], length)) # +1 para pular ':'
            i += length + 1 # +1 por causa do pulo do ':'
            cache = "" # Reseto a cache, pois deve ser temporaria
        elif str[i] == 'd': # Dicionario
            retorno = parse_dict(str[i:])
            lista.append(retorno[0])
            i += retorno[1] # Retorna o índice que parou, logo preciso somar para não ler tudo dnv
            cache = "" # Reseto a cache, pois deve ser temporaria
        else:
            if cache == 'e': # Fim de um dicionário.
               break
            cache += str[i] # Concateno o char na cache
            i += 1 # avanço com o índice
    return lista, i

#################################
### CODIFICAÇÃO PARA B-ENCODE ###
#################################

# [IMPORTANTE] A função inicial é a encode_dict()

# Basicamente, é tudo concatenação de strings. 
def encoder(valor):
    # Essa função codifica os valores primitivos, inteiro e string
    bencode = ""
    if type(valor) == int:
        bencode += f"i{valor}e" # exemplo: valor = -67 => bencode = i-67e
    elif type(valor) == str:
        bencode += f"{len(valor)}:{valor}" # exemplo: valor = "chave" => bencode 5:chave
    return bencode
      
def encode_list(lista):
    # Essa função codifica listas
    # Como o item da lista pode ser um dicionario ou outra lista, temos que usar a recursividade
    bencode = "l"
    for item in lista:
        if type(item) == list:
            bencode += encode_list(item)
        elif type(item) == dict:
            bencode += encode_dict(item)
        else:
            bencode += encoder(item) 
    bencode += "e"
    return bencode

def encode_dict(dic:dict):
    # Essa função codifica dicionarios
    # Como o valor podem ser uma lista ou outro dicionario, de novo recursividade
    # A chave sempre vai ser uma string.
    bencode = "d"
    for chave,valor in dic.items():
        bencode += f"{len(chave)}:{chave}"
        if type(valor) == list:
            bencode += encode_list(valor)
        elif type(valor) == dict:
            bencode += encode_dict(valor)
        else:
            bencode += encoder(valor)
    bencode += "e"
    return bencode


def parser(var): # Função para decidir se vai codificar ou decodificar baseada no tipo do argumento
    if type(var) == dict: # Dicionário para codificar em B-encode
        return encode_dict(var)
    else: # String para decodificar para B-encode
        return parse_bencode(var)[0][0] # Pela natureza da minha solução, tive que usar índices por causa da lista.

# Exemplo de um B-encode
#stream = "d8:announce36:https://tracker.example.com/announce4:infod6:lengthi5242880e4:name11:example.txt6:pieces20:abcdefghijabcdefghij12:piece lengthi262144eee"
#stream2 = "d8:intervali1800e5:peers6:IPPORT8:completei10e10:incompletei5ee"
# Exemplos de uso:
#print(f"B-encode => Dicionario: \n{parser(stream)}\n")
#print(f"Dicionario => B-encode: \n{parser(parser(stream))}\n")
#print("Stream2: ", parser(stream2))