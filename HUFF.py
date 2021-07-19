#!/usr/bin/env python3

# © Davide Peressoni
# MIT LICENSE

# Compress text files containing integers encoded in ASCII (base 10) with a custom Huffman encoding

import sys

FILE: str = sys.argv[1] # Path of the file to compress

DIFF = "diff" # Tool used to check the corectness (e.g. "kdiff3")

import os, tempfile
from queue import PriorityQueue

from typing import BinaryIO, Optional, List, Tuple

def tree(symbol_counts: List[int]) -> List[int]:
  """
  Builds the Huffman tree.
  The tree is stored as an array: each elements contains the index of its parent. Having 11 symbols (0-9 and the separator) the tree has at most 21 nodes. Since leaves don't need to be encoded (they are parent of no node) we have to encode only 10 indexes, and we can do this with 4 bits (we store the index minus 11).
  """
  root = 0xF + 11 # root "parent" will be encoded as 0xF = 2**4-1 (the biggest unsigned integer of 4 bits)
  tree: List[int] = [root] * 11 # the 11 leaves: the symbols
  q = PriorityQueue()
  for symbol, count in enumerate(symbol_counts):
    q.put((count, symbol))

  # join the two nodes with lowest probability
  while not q.empty():
    ci, i = q.get()
    if q.empty():
      break # nothing to join
    cj, j = q.get()
    k = len(tree)
    tree.append(root) # the join of this two nodes (k) is the new root
    tree[i] = tree[j] = k # i and j are children of k
    q.put((ci+cj, k)) # put k in the priority queue with the sum of its children probabilities
  return tree

def huffman(tree: List[int]) -> List[str]:
  """
  Generates Huffman encoding from Huffman tree.
  """
  code: List[str] = [""] * len(tree) # stores the encoding of each node
  children: List[int] = [0] * len(tree) # counts the number of children parsed for each node
  for i in range(len(tree)-1, -1, -1): # loop backwards on the tree array
    parent = tree[i]
    if parent < len(tree): # otherwise tree[i] is the root, which code is empty
      code[i] = code[parent] + str(children[parent])
      children[parent] += 1
  return code[:11] # return only the encoding of the symbols

################ ENCODE

text: List[int] = [] # numbers to encode
counts: List[int] = [0] * 11 # symbol counts
codes: List[str] = [] # Huffman encoding of symbols
header: List[int] = [] # Huffman header to allow decompression

### Read input

i = 0
with open(FILE, 'r') as src:

  for line in src: # for each number (one per line)
    i += 1
    leading = True
    for c in line.strip(): # for each digit
      # remove leading zeros, which have no meaning
      if leading and c[0] == '0':
        continue
      # substitute minus with a leading zero. It is possible because we don't have no more leading zeros. With this trick we spare a symbol in the dictionary.
      if c == '-':
        c = '0'
      else:
        leading = False
      digit = ord(c) - ord('0')
      # add this digit
      counts[digit] += 1
      text.append(digit)
    # add a separator (10)
    counts[10] += 1
    text.append(10)

text += [0, 0] # EOF sequence: two leading zeros are not allowed

print(f"Scanned {i} lines")

# Huffman coding

header = tree(counts)
codes = huffman(header)

# Infos

bits = 0
count = 0
for n in range(11):
  print(n, counts[n], codes[n])
  count += counts[n]
  bits += counts[n] * len(codes[n])

print(bits/count, "bit/symbol")
print(bits/1024/8, "kiB")

### Write output

with open(FILE + ".huf", "wb") as out:
  buffer: str = "".join([f"{n-11:04b}" for n in header]) # store header using 4 bits for each parent
  n: int = 0
  while n < len(text) or buffer != "": # while there is something to write
    out.write(bytes((int(buffer[:8],2),))) # write a byte from the buffer
    buffer = buffer[8:] # remove the written byte
    while (l:=len(buffer)) < 8: # load at least a byte in the buffer
      if n < len(text):
        buffer += codes[text[n]] # load next encoded number
        n += 1
      elif l>0:
        buffer += "0" * (8 - l) # align to byte with zero padding
      else:
        break

################ DECODE

def rb(src: BinaryIO, size: int=1,  byte_order: str='big', signed: bool=False) -> Optional[int]:
  """
  Binary read bytes as integer
  """
  if res := src.read(size):
    return int.from_bytes(res, byte_order, signed=signed)
  return None

j: int = 0 # count read numbers
with open(FILE + ".huf", "rb") as src, open(FILE + ".tmp", 'w') as out:

  buffer: str = ""
  number: str = "" # current read number
  header: List[int] = []

  # read header
  while True:
    byte: int = rb(src)
    a, b = byte >> 4, byte & 0xF # extract the two 4-tuples from the byte
    header.append(a+11)
    if a != 0xF: # a is not root, so b is part of the header
      header.append(b+11)
      if b == 0xF: # b is root (header is ended)
        break
    else: # a is root
      # put b into the buffer (header is ended)
      buffer = f"{b:04b}"
      break

  codes = huffman(header)

  writing: bool = True

  while writing and (byte := rb(src)) is not None:
    buffer += f"{byte:08b}" # add read byte into the buffer

    while True:
      if number == "-0": # EOF sequence
        writing = False # our text is ended
        break
      # this code is a separator?
      if len(buffer) >= (l := len(codes[-1])) and buffer[:l] == codes[-1]:
        buffer = buffer[l:] # remove code from buffer
        if number == "":
          number = "0"
        print(number, file=out) # print current number
        number = "" # empty current number
        j += 1
        assert j <= i # read numbers cannot exceed written ones
        continue
      still: bool = True # no code read
      for n in range (10):
        # this code is digit n?
        if len(buffer) >= (l := len(codes[n])) and buffer[:l] == codes[n]:
          # add this digit to the number
          if len(number) == 0 and n == 0:
            number = '-' # leading zero is a minus
          else:
            number += chr(ord('0') + n)
          buffer = buffer[l:] # remove code from buffer
          still = False
          break # read next digit
      if still:
        break # add more bytes in the buffer

print(f"Generated {j} lines")

input("Press a key to continue")
os.system(f'{DIFF} "{FILE}" "{FILE}.tmp"')
os.system(f'rm "{FILE}.tmp"')
