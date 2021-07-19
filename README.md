# Huffman for integer list

Compress text files containing integers encoded in ASCII (base 10) with a custom Huffman encoding.

## Usage
  1. Write the integers to compress, one per line, in base 10 ASCII in a text file
  2. `python3 HUFF.py file_path`

## How it works

It uses only 11 symbols: the digits between zero and nine and a separator. To encode negative numbers the minus sign is encoded as a zero: this is possible since the script discards all leading zeros and in this way it spares a symbol in the dictionary.

The huffman tree is stored as an array: each elements contains the index of its parent. Having 11 symbols (0-9 and the separator) the tree has at most 21 nodes. Since leaves don't need to be encoded (they are parent of no node) we have to encode only 10 indexes, and we can do this with 4 bits (we store the index minus 11).
